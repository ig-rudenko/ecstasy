import contextlib
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import NamedTuple, TypedDict

import orjson
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.core.cache import cache
from django.db.models import QuerySet

from check.models import Devices, InterfacesComments
from devicemanager.device import Interfaces
from net_tools.models import DescNameFormat, DevicesInfo


@dataclass
class InterfaceComment:
    user: str
    text: str
    created_time: datetime

    def to_dict(self):
        return {"user": self.user, "text": self.text, "createdTime": self.created_time}


@dataclass
class DeviceInterfacesComments:
    interfaces: dict[str, list[InterfaceComment]] = field(default_factory=dict)


@dataclass
class Comments:
    devices: dict[str, DeviceInterfacesComments] = field(default_factory=dict)

    def get_interface(self, device_name: str, interface_name: str) -> list[InterfaceComment]:
        device_interfaces = self.devices.get(device_name)
        if device_interfaces is not None:
            return device_interfaces.interfaces.get(interface_name, [])
        return []


class InterfaceCommentDict(TypedDict):
    user: str
    text: str
    createdTime: str


class InterfaceInfoDict(TypedDict):
    name: str
    status: str
    description: str
    vlans: str
    savedTime: str
    vlansSavedTime: str


class DescriptionFinderResult(TypedDict):
    device: str
    interface: InterfaceInfoDict
    comments: list[InterfaceCommentDict]


@dataclass
class DeviceInterfacesData:
    interfaces: Interfaces
    vlans: Interfaces
    interfaces_date: datetime | None
    vlans_date: datetime | None

    def get_interface_vlans(self, interface_name: str) -> str:
        for interface_with_vlans in self.vlans:
            if interface_with_vlans.name == interface_name:
                return ", ".join(map(str, interface_with_vlans.vlan))
        return ""


class Finder:
    def __init__(self, devices: QuerySet[Devices]):
        self._devices_qs = devices
        self.dev_info_queryset = (
            DevicesInfo.objects.filter(dev__in=devices)
            .select_related("dev")
            .values("interfaces", "interfaces_date", "vlans", "vlans_date", "dev__name")
        )

        self.devices: dict[str, DeviceInterfacesData] = {}
        for dev_info in self.dev_info_queryset:
            interfaces = Interfaces(orjson.loads(dev_info["interfaces"] or "[]"))
            # Проверяем, пуста ли переменная interfaces.
            if not interfaces:
                continue
            self.devices[dev_info["dev__name"]] = DeviceInterfacesData(
                interfaces=interfaces,
                vlans=Interfaces(orjson.loads(dev_info["vlans"] or "[]")),
                interfaces_date=dev_info["interfaces_date"],
                vlans_date=dev_info["vlans_date"],
            )

    def find_description(self, pattern_str: str, is_regex: bool = False) -> list[DescriptionFinderResult]:
        """
        # Поиск портов на всем оборудовании, описание которых совпадает с finding_string или re_string

        :param pattern_str: Регулярное выражение, по которому будет осуществляться поиск описания портов.
        :param is_regex: Флаг, указывающий, является ли pattern_str регулярным выражением.
        :return: Список результатов поиска
        """
        result: list[DescriptionFinderResult] = []

        if not is_regex:
            pattern_str = re.escape(pattern_str)  # Экранируем специальные символы
        pattern: re.Pattern[str] = re.compile(pattern_str, flags=re.IGNORECASE)

        comments: Comments = self.get_comments(pattern)

        self._find_in_interfaces_history(pattern, comments, result)
        self._add_comments_to_result(comments, result)

        return result

    def _find_in_interfaces_history(
        self, pattern: re.Pattern[str], comments: Comments, result: list[DescriptionFinderResult]
    ) -> None:
        # Производим поочередный поиск
        for device_name, info in self.devices.items():
            for interface in info.interfaces:
                find_on_desc = False

                # Если нашли совпадение в описании порта
                if pattern.search(interface.desc):
                    find_on_desc = True

                interface_comments = comments.get_interface(device_name, interface.name)

                if find_on_desc or interface_comments:
                    with contextlib.suppress(KeyError):  # Игнорируем, если ошибка ключа
                        result.append(
                            {
                                "device": device_name,
                                "comments": [comment.to_dict() for comment in interface_comments],
                                "interface": {
                                    "name": interface.name,
                                    "status": interface.status,
                                    "description": interface.desc,
                                    "vlans": info.get_interface_vlans(interface.name),
                                    "savedTime": self.get_natural_time(info.interfaces_date),
                                    "vlansSavedTime": self.get_natural_time(info.vlans_date),
                                },
                            }
                        )

                    # Удаляем найденные комментарии
                    if interface_comments:
                        del comments.devices[device_name].interfaces[interface.name]

    def _add_comments_to_result(self, comments: Comments, result: list[DescriptionFinderResult]) -> None:
        for dev_name, dev_intf_comments in comments.devices.items():
            if dev_name not in self.devices:
                continue

            for interface in dev_intf_comments.interfaces:
                result.extend(
                    [
                        {
                            "device": dev_name,
                            "comments": [comment.to_dict()],
                            "interface": {
                                "name": interface,
                                "status": interface,
                                "description": comment.text,
                                "vlans": self.devices[dev_name].get_interface_vlans(interface),
                                "savedTime": self.get_natural_time(self.devices[dev_name].interfaces_date),
                                "vlansSavedTime": self.get_natural_time(self.devices[dev_name].vlans_date),
                            },
                        }
                        for comment in dev_intf_comments.interfaces[interface]
                    ]
                )

    @staticmethod
    def get_natural_time(time_str: datetime | None) -> str:
        if time_str is not None:
            return naturaltime(time_str)
        return "No Datetime"

    def get_comments(self, regex: re.Pattern[str]) -> Comments:
        """Возвращает список всех комментариев поискового запроса."""
        comments = list(
            InterfacesComments.objects.filter(comment__iregex=regex.pattern, device__in=self._devices_qs)
            .select_related("user", "device")
            .values("user__username", "device__name", "interface", "comment", "datetime")
        )
        comments_result: Comments = Comments()

        for comment in comments:
            comments_result.devices.setdefault(comment["device__name"], DeviceInterfacesComments())
            comments_result.devices[comment["device__name"]].interfaces.setdefault(comment["interface"], [])

            comments_result.devices[comment["device__name"]].interfaces[comment["interface"]].append(
                InterfaceComment(
                    user=comment["user__username"] or "Anonymous",
                    text=comment["comment"],
                    created_time=comment["datetime"],
                )
            )
        return comments_result


class VlanTracerouteResult(NamedTuple):
    """
    Представляет собой именованный кортеж, который содержит информацию об узле сети, его
    следующем узле, ширине линии, описании линии и статусе административного отключения.
    """

    node: str
    next_node: str
    line_width: int
    line_description: str
    admin_down_status: str


# Класс VlanTraceroute
class VlanTraceroute:
    """
    Используется для поиска конкретного VLAN на сетевых устройствах для последующего создания
    визуальной карты топологии сети.
    """

    def __init__(self, cache_timeout: int = 60 * 5) -> None:
        self.result: list[VlanTracerouteResult] = []  # Итоговый список
        self._desc_name_list: list[DescNameFormat] = []
        self.passed_devices: set[str] = set()  # Множество уже пройденного оборудования

        # Словарь содержащий информацию об VLAN для каждого оборудования
        self._devices_vlans_info: dict[str, str | None] = {}
        self._device_ip_names: dict[str, str] = {}  # Словарь соответствия IP-адресов и имен оборудования
        self._cache_timeout = cache_timeout  # Время кеширования
        self._get_devices_vlans()

        self._reformatting_cache: dict[str, str] = {}

    def reformatting(self, name: str):
        """Форматируем строку с названием оборудования, приводя его в единый стандарт, указанный в DescNameFormat"""
        if (new_name := self._reformatting_cache.get(name)) is not None:
            return new_name

        for reformat in self._desc_name_list:
            if reformat.standard == name:
                # Если имя совпадает с правильным, то отправляем его
                self._reformatting_cache[name] = name
                return name

            for pattern in reformat.replacement.split(", "):
                if re.search(pattern, name, flags=re.IGNORECASE):  # Если паттерн содержится в исходном имени
                    # Заменяем совпадение "pattern" в названии "name" на правильное "n"
                    new_name = re.sub(pattern, reformat.standard, name, flags=re.IGNORECASE)
                    self._reformatting_cache[name] = new_name
                    return new_name

        # Если не требуется замены
        self._reformatting_cache[name] = name
        return name

    def find_vlan(
        self,
        device: str,
        vlan_to_find: int,
        empty_ports: bool,
        only_admin_up: bool,
        find_device_pattern: str,
        double_check: bool = False,
    ):
        """
        ## Осуществляет поиск VLAN по портам оборудования.

        Функция загружает данные об устройстве из базы данных, парсит информацию о VLAN на портах,
        и если находит совпадение с искомым VLAN, то добавляет информацию в итоговый список.

        :param device: Имя устройства, на котором осуществляется поиск.
        :param vlan_to_find: VLAN, который ищем.
        :param empty_ports: Включать пустые порты в анализ?
        :param only_admin_up:  Включать порты со статусом admin down в анализ?
        :param find_device_pattern:  Регулярное выражение, которое позволит найти оборудование в описании порта.
        :param double_check: Проверять двухстороннюю связь VLAN на портах или нет.
        """
        if not self._desc_name_list:
            self._desc_name_list = list(DescNameFormat.objects.all())

        if device in self.passed_devices:
            return
        self.passed_devices.add(device)  # Добавляем узел в список уже пройденных устройств

        # Получаем интерфейсы устройства, если они есть в базе данных.
        interfaces: Interfaces = self._get_device_interfaces(device)
        if not interfaces:
            return

        for interface in interfaces:
            if vlan_to_find not in interface.vlan:
                # Пропускаем несоответствующие порты
                continue

            # Ищем в описании порта следующий узел сети
            next_device = self._get_next_device(find_device_pattern, interface.desc)

            # Пропускаем порты admin down, если включена опция only admin up
            if only_admin_up:
                admin_status = "down" if interface.is_admin_down else "up"
            else:
                admin_status = ""

            # Блок кода ниже проверяет, включен ли флаг double_check и найдено ли следующее устройство. Если оба
            # условия выполняются, он получает информацию о VLAN для следующего устройства из базы данных и проверяет,
            # есть ли на следующем устройстве порт, который имеет желаемую VLAN и подключен к текущему устройству.
            # Если такой порт найден, переменная next_device не изменяется. В противном случае `next_device`
            # устанавливается в пустую строку, указывающую, что следующего устройства нет или следующее устройство
            # не имеет подходящего порта.
            next_dev_interface_name = ""
            if double_check and next_device:  # Если есть следующее оборудование
                next_dev_interfaces: Interfaces = self._get_device_interfaces(next_device)

                for next_dev_interface in next_dev_interfaces:
                    desc = self.reformatting(next_dev_interface.desc)
                    if vlan_to_find in next_dev_interface.vlan and (
                        re.search(device, desc, flags=re.IGNORECASE)
                        or self._get_next_device(find_device_pattern, desc) == device
                    ):
                        # Если нашли на соседнем оборудование порт с искомым VLAN в сторону текущего оборудования
                        next_dev_interface_name = str(next_dev_interface.name)
                        break
                else:
                    next_device = ""

            # Создаем данные для visual map
            if next_device:
                # Следующий узел сети
                self._add_next_device_result(
                    device, interface.name, next_device, next_dev_interface_name, admin_status
                )

            # Порт с описанием
            elif interface.desc:
                self._add_unknown_device_result(device, interface.name, interface.desc, admin_status)

            # Пустые порты
            elif empty_ports:
                self._add_empty_port_result(device, interface.name, admin_status)

            # Проверка наличия следующего устройства в списке пройденных устройств.
            if next_device and next_device not in self.passed_devices:
                self.find_vlan(
                    device=next_device,
                    vlan_to_find=vlan_to_find,
                    empty_ports=empty_ports,
                    only_admin_up=only_admin_up,
                    find_device_pattern=find_device_pattern,
                    double_check=double_check,
                )

    def _add_next_device_result(
        self,
        device: str,
        interface_name: str,
        next_device: str,
        next_dev_interface_name: str,
        admin_down_status: str,
    ):
        """
        Добавляет данные следующего устройства в результаты.
        :param device: Устройство (название).
        :param interface_name: Название интерфейса `device`.
        :param next_device: Следующее устройство (название).
        :param next_dev_interface_name: Название интерфейса следующего устройства, который смотрит в сторону `device`
        :param admin_down_status: Статус доступности порта `device` в сторону `next_device`.
        """
        line_description = f"""
        <strong>
            {device} port: 
            <span class="badge bg-primary" style="font-size: 0.8rem;">{interface_name}</span> -->
            {next_device} port: 
            <span class="badge bg-primary" style="font-size: 0.8rem;">{next_dev_interface_name}</span>
        </strong>
        """
        self.result.append(
            VlanTracerouteResult(
                node=device,  # Устройство (название узла)
                next_node=next_device,  # Сосед (название узла)
                line_width=10,  # Толщина линии соединения
                line_description=line_description,  # Описание линии
                admin_down_status=admin_down_status,
            )
        )

    def _add_unknown_device_result(
        self, device: str, interface_name: str, interface_desc: str, admin_down_status: str
    ):
        """
        Добавляет неизвестное устройство в результат.
        :param device: Имя устройства.
        :param interface_name: Имя порта.
        :param interface_desc: Описание порта.
        :param admin_down_status: Статус доступности порта.
        """

        line_description = f"""
        <strong>
            {device} port: 
            <span class="badge bg-primary" style="font-size: 0.8rem;">{interface_name}</span> -->
            {interface_desc}
        </strong>
        """
        self.result.append(
            VlanTracerouteResult(
                node=device,  # Устройство (название узла)
                next_node=f"{device} d:({interface_desc})",  # Порт (название узла)
                line_width=10,
                line_description=line_description,
                admin_down_status=admin_down_status,
            )
        )

    def _add_empty_port_result(self, device: str, interface: str, admin_down_status: str):
        """
        Добавляет пустой порт в результат
        :param device: Имя устройства
        :param interface: Имя порта
        :param admin_down_status: Статус доступности порта.
        """
        line_description = f"""
        <strong>
            {device} port: <span class="badge bg-primary" style="font-size: 0.8rem;">{interface}</span>
        </strong>
        """
        self.result.append(
            VlanTracerouteResult(
                node=device,  # Устройство (название узла)
                next_node=f"{device} p:({interface})",  # Порт (название узла)
                line_width=5,  # Толщина линии соединения
                line_description=line_description,  # Описание линии соединения
                admin_down_status=admin_down_status,
            )
        )

    def clear_results(self):
        """Очищает результаты поиска."""
        self.result = []

    def _get_next_device(self, pattern: str, description: str) -> str:
        next_device = ""
        # Ищем в описании порта следующий узел сети
        next_device_match = re.search(pattern, self.reformatting(description), flags=re.IGNORECASE)
        # Приводим к единому формату имя узла сети
        if next_device_match:
            next_device = next_device_match.group()
            next_device = self._device_ip_names.get(next_device, next_device)

        return next_device

    def _get_devices_info(self):
        cache_key = f"net_tools:{self.__class__.__name__}:devices_info"
        data = cache.get(cache_key)
        if data is None:
            data = DevicesInfo.objects.all().values("dev__name", "dev__ip", "vlans")
            cache.set(cache_key, data, self._cache_timeout)
        return data

    def _get_devices_vlans(self):
        """Получаем список всех устройств сети, содержащий информацию об VLAN для каждого"""
        if not self._devices_vlans_info:
            info = self._get_devices_info()

            self._devices_vlans_info = {dev["dev__name"]: dev["vlans"] for dev in info}
            self._device_ip_names = {dev["dev__ip"]: dev["dev__name"] for dev in info}

    def _get_device_interfaces(self, device_name: str) -> Interfaces:
        """Получаем список VLAN для текущего устройства"""
        device_info = self._devices_vlans_info.get(device_name, None)
        if device_info is not None:
            return Interfaces(orjson.loads(device_info or "[]"))
        return Interfaces()


class MultipleVlanTraceroute:
    def __init__(self, finder: VlanTraceroute, devices_queryset: QuerySet[Devices]):
        self._finder: VlanTraceroute = finder
        self._devices_queryset: QuerySet[Devices] = devices_queryset

    def execute_traceroute(
        self,
        vlan: int,
        empty_ports: bool,
        only_admin_up: bool,
        find_device_pattern: str,
        double_check: bool,
        graph_min_length: int,
    ) -> list[VlanTracerouteResult]:
        result: list[VlanTracerouteResult] = []
        # Цикл for, перебирающий список устройств, используемых для запуска трассировки VLAN.
        for device_name in self._devices_queryset.values_list("name", flat=True):
            # Трассировка vlan
            self._finder.find_vlan(
                device=device_name,
                vlan_to_find=vlan,
                empty_ports=empty_ports,
                only_admin_up=only_admin_up,
                find_device_pattern=find_device_pattern,
                double_check=double_check,
            )
            if not graph_min_length or len(self._finder.result) >= graph_min_length:
                result.extend(self._finder.result)

            # Очистка результаты поиска для следующего устройства
            self._finder.clear_results()

        return result
