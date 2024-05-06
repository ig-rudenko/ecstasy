import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import NamedTuple, TypedDict, Literal

import orjson
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.db.models import QuerySet

from check.models import Devices, InterfacesComments
from devicemanager.device import Interfaces
from net_tools.models import DevicesInfo, DescNameFormat


@dataclass
class InterfaceComment:
    user: str
    text: str
    created_time: str

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


class DescriptionFinderResult(TypedDict):
    Device: str
    Interface: str
    Description: str
    Comments: list[InterfaceCommentDict]
    SavedTime: str


class Finder:
    def find_description(self, pattern_str: str, user_id: int) -> list[DescriptionFinderResult]:
        """
        # Поиск портов на всем оборудовании, описание которых совпадает с finding_string или re_string

        Возвращаем кортеж из списка результатов поиска и количество найденных описаний

        Список результатов содержит следующие элементы:

        ```python
            {
                "Device": "Имя оборудования",
                "Interface": "Порт",
                "Description": "Описание",
                "SavedTime": "Дата и время" # В формате "%d.%m.%Y %H:%M:%S",
            }
        ```

        :param pattern_str: Регулярное выражение, по которому будет осуществляться поиск описания портов.
        :param user_id: Пользователь, для которого будет осуществляться поиск.
        :return: Список результатов поиска
        """

        comments: Comments = self.get_comments(pattern_str)

        pattern: re.Pattern[str] = re.compile(re.escape(pattern_str), flags=re.IGNORECASE)

        result = []

        dev_info_queryset = (
            DevicesInfo.objects.filter(dev__group__profile__user_id=user_id)
            .select_related("dev")
            .values("interfaces", "interfaces_date", "dev__name")
        )

        # Производим поочередный поиск
        for device in dev_info_queryset:
            # Проверяем, пуста ли переменная interfaces.
            if not device["interfaces"]:
                continue

            # Загрузка данных json из базы данных в словарь python.
            interfaces: list = orjson.loads(device["interfaces"] or "[]")

            for line in interfaces:  # type: dict[Literal["Interface", "Status", "Description"], str]
                find_on_desc = False

                # Если нашли совпадение в описании порта
                if re.findall(pattern, line["Description"]):
                    find_on_desc = True

                interface_comments = comments.get_interface(device["dev__name"], line["Interface"])

                if find_on_desc or interface_comments:
                    if device["interfaces_date"] is not None:
                        interfaces_datetime = naturaltime(device["interfaces_date"])
                    else:
                        interfaces_datetime = "No Datetime"

                    result.append(
                        {
                            "Device": device["dev__name"],
                            "Interface": line["Interface"],
                            "Description": line["Description"],
                            "Comments": [comment.to_dict() for comment in interface_comments],
                            "SavedTime": interfaces_datetime,
                        }
                    )

                    if interface_comments:
                        del comments.devices[device["dev__name"]].interfaces[line["Interface"]]

        for dev_name in comments.devices:
            for interface in comments.devices[dev_name].interfaces:
                result.append(
                    *[
                        {
                            "Device": dev_name,
                            "Interface": interface,
                            "Description": comment.text,
                            "Comments": [comment.to_dict()],
                            "SavedTime": comment.created_time,
                        }
                        for comment in comments.devices[dev_name].interfaces[interface]
                    ]
                )

        return result

    @staticmethod
    def get_comments(regex_str: str) -> Comments:
        """Возвращает список всех комментариев поискового запроса."""
        comments = list(
            InterfacesComments.objects.filter(comment__iregex=re.escape(regex_str))
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

    def __init__(self) -> None:
        self.result: list[VlanTracerouteResult] = []  # Итоговый список
        self._desc_name_list: list[DescNameFormat] = []
        self.passed_devices: set[str] = set()  # Множество уже пройденного оборудования

    @lru_cache(maxsize=200)
    def reformatting(self, name: str):
        """Форматируем строку с названием оборудования, приводя его в единый стандарт, указанный в DescNameFormat"""

        for reformat in self._desc_name_list:
            if reformat.standard == name:
                # Если имя совпадает с правильным, то отправляем его
                return name

            for pattern in reformat.replacement.split(", "):
                if re.search(pattern, name, flags=re.IGNORECASE):  # Если паттерн содержится в исходном имени
                    # Заменяем совпадение "pattern" в названии "name" на правильное "n"
                    return re.sub(pattern, reformat.standard, name, flags=re.IGNORECASE)

        # Если не требуется замены
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
        try:
            dev = DevicesInfo.objects.get(dev__name=device)
        except DevicesInfo.DoesNotExist:
            return

        interfaces = Interfaces(orjson.loads(dev.vlans or "[]"))

        if not interfaces:
            return

        for interface in interfaces:
            if vlan_to_find not in interface.vlan:
                # Пропускаем несоответствующие порты
                continue

            # Ищем в описании порта следующий узел сети
            next_device_find: list[str] = re.findall(
                find_device_pattern, self.reformatting(interface.desc), flags=re.IGNORECASE
            )

            # Приводим к единому формату имя узла сети
            next_device = next_device_find[0] if next_device_find else ""

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
                try:
                    next_dev_intf_json: str = DevicesInfo.objects.get(dev__name=next_device).vlans or "[]"
                except DevicesInfo.DoesNotExist:
                    next_dev_intf_json = "[]"

                next_dev_interfaces = Interfaces(orjson.loads(next_dev_intf_json))

                for next_dev_interface in next_dev_interfaces:
                    if vlan_to_find in next_dev_interface.vlan and re.findall(
                        device, self.reformatting(next_dev_interface.desc), flags=re.IGNORECASE
                    ):
                        # Если нашли на соседнем оборудование порт с искомым VLAN в сторону текущего оборудования
                        next_dev_interface_name = str(next_dev_interface.name)
                        break
                else:
                    next_device = ""

            # Создаем данные для visual map
            if next_device:
                # Следующий узел сети
                self.result.append(
                    VlanTracerouteResult(
                        node=device,  # Устройство (название узла)
                        next_node=next_device,  # Сосед (название узла)
                        line_width=10,  # Толщина линии соединения
                        line_description=f"""
                        <strong>
                            {device} port: 
                            <span class="badge bg-primary" style="font-size: 0.8rem;">{interface.name}</span> -->
                            {next_device} port: 
                            <span class="badge bg-primary" style="font-size: 0.8rem;">{next_dev_interface_name}</span>
                        </strong>
                        """,  # Описание линии
                        admin_down_status=admin_status,
                    )
                )
            # Порт с описанием
            elif interface.desc:
                self.result.append(
                    VlanTracerouteResult(
                        node=device,  # Устройство (название узла)
                        next_node=f"{device} d:({interface.desc})",  # Порт (название узла)
                        line_width=10,  # Толщина линии соединения
                        line_description=f"""
                        <strong>
                            {device} port: <span class="badge bg-primary" style="font-size: 0.8rem;">{interface.name}</span> -->
                            {interface.desc}
                        </strong>
                        """,  # Описание линии соединения
                        admin_down_status=admin_status,
                    )
                )
            # Пустые порты
            elif empty_ports:
                self.result.append(
                    VlanTracerouteResult(
                        node=device,  # Устройство (название узла)
                        next_node=f"{device} p:({interface.name})",  # Порт (название узла)
                        line_width=5,  # Толщина линии соединения
                        line_description=f"""
                        <strong>
                            {device} port: <span class="badge bg-primary" style="font-size: 0.8rem;">{interface.name}</span>
                        </strong>
                        """,  # Описание линии соединения
                        admin_down_status=admin_status,
                    )
                )

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
        for start_dev in self._devices_queryset:
            # Трассировка vlan
            finder = VlanTraceroute()
            finder.find_vlan(
                device=start_dev.name,
                vlan_to_find=vlan,
                empty_ports=empty_ports,
                only_admin_up=only_admin_up,
                find_device_pattern=find_device_pattern,
                double_check=double_check,
            )
            if not graph_min_length or len(finder.result) >= graph_min_length:
                result.extend(finder.result)

        return result
