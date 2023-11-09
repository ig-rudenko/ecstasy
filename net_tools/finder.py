from functools import lru_cache
from re import findall, sub, IGNORECASE, compile, escape
from typing import List, NamedTuple

import orjson
from django.contrib.auth.models import User
from django.db.models import QuerySet

from check.models import Devices, InterfacesComments
from devicemanager.device import Interfaces
from .models import DevicesInfo, DescNameFormat


class Finder:
    @staticmethod
    def find_description(pattern: str, user: User) -> list:
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

        :param pattern: Регулярное выражение, по которому будет осуществляться поиск описания портов.
        :param user: Поль
        :return: Список результатов поиска
        """

        all_comments = list(
            InterfacesComments.objects.filter(
                comment__iregex=escape(pattern)
            ).select_related("user", "device")
        )

        comments_dict = {}
        for comment in all_comments:
            if not comments_dict.get(comment.device):
                comments_dict[comment.device.name] = {}
            if not comments_dict[comment.device.name].get(comment.interface):
                comments_dict[comment.device.name][comment.interface] = []

            comments_dict[comment.device.name][comment.interface].append(
                {
                    "user": comment.user.username,
                    "text": comment.comment,
                    "datetime": comment.datetime,
                }
            )

        pattern = compile(escape(pattern), flags=IGNORECASE)

        result = []

        user_groups = [g["id"] for g in user.profile.devices_groups.all().values("id")]

        # Производим поочередный поиск
        for device in DevicesInfo.objects.all().select_related("dev"):
            try:
                if device.dev.group_id not in user_groups:
                    continue
            except Devices.DoesNotExist:
                continue

            # Проверяем, пуста ли переменная interfaces.
            if not device.interfaces:
                continue

            # Загрузка данных json из базы данных в словарь python.
            interfaces = orjson.loads(device.interfaces)

            for line in interfaces:
                find_on_desc = False

                # Если нашли совпадение в описании порта
                if findall(pattern, line["Description"]):
                    find_on_desc = True

                comments_dict_value = comments_dict.get(device.dev.name, {}).get(
                    line["Interface"], []
                )

                if find_on_desc or comments_dict_value:
                    result.append(
                        {
                            "Device": device.dev.name,
                            "Interface": line["Interface"],
                            "Description": line["Description"],
                            "Comments": comments_dict_value,
                            "SavedTime": device.interfaces_date.strftime(
                                "%d.%m.%Y %H:%M:%S"
                            ),
                        }
                    )

                    if comments_dict_value:
                        del comments_dict[device.dev.name][line["Interface"]]

        for dev_name in comments_dict:
            if comments_dict[dev_name]:
                for interface in comments_dict[dev_name]:
                    result.append(
                        *[
                            {
                                "Device": dev_name,
                                "Interface": interface,
                                "Description": comment["text"],
                                "Comments": [comment],
                                "SavedTime": comment["datetime"].strftime(
                                    "%d.%m.%Y %H:%M:%S"
                                ),
                            }
                            for comment in comments_dict[dev_name][interface]
                        ]
                    )

        return result


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

    def __init__(self):
        self.result: List[VlanTracerouteResult] = []  # Итоговый список
        self._desc_name_list: List[DescNameFormat] = []
        self.passed_devices = set()  # Множество уже пройденного оборудования

    @lru_cache(maxsize=200)
    def reformatting(self, name: str):
        """Форматируем строку с названием оборудования, приводя его в единый стандарт, указанный в DescNameFormat"""

        for reformat in self._desc_name_list:
            if reformat.standard == name:
                # Если имя совпадает с правильным, то отправляем его
                return name

            for pattern in reformat.replacement.split(", "):
                if pattern in name:  # Если паттерн содержится в исходном имени
                    # Заменяем совпадение "pattern" в названии "name" на правильное "n"
                    return sub(pattern, reformat.standard, name)

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

        :param device: Имя устройства, на котором осуществляется поиск
        :param vlan_to_find: VLAN, который ищем
        :param empty_ports: Включать пустые порты в анализ?
        :param only_admin_up:  Включать порты со статусом admin down в анализ?
        :param find_device_pattern:  Регулярное выражение, которое позволит найти оборудование в описании порта.
        :param double_check: Проверять двухстороннюю связь VLAN на портах или нет.
        """
        if not self._desc_name_list:
            self._desc_name_list: List[DescNameFormat] = list(
                DescNameFormat.objects.all()
            )

        if device in self.passed_devices:
            return

        self.passed_devices.add(
            device
        )  # Добавляем узел в список уже пройденных устройств
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
            next_device_find: List[str] = findall(
                find_device_pattern, self.reformatting(interface.desc), flags=IGNORECASE
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
                    next_dev_intf_json: str = (
                        DevicesInfo.objects.get(dev__name=next_device).vlans or "[]"
                    )
                except DevicesInfo.DoesNotExist:
                    next_dev_intf_json = "[]"

                next_dev_interfaces = Interfaces(orjson.loads(next_dev_intf_json))

                for next_dev_interface in next_dev_interfaces:
                    if vlan_to_find in next_dev_interface.vlan and findall(
                        device,
                        self.reformatting(next_dev_interface.desc),
                        flags=IGNORECASE,
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
                            {device} port: <span class="badge bg-primary" style="font-size: 0.8rem;">{interface.name}</span> -->
                            {next_device} port: <span class="badge bg-primary" style="font-size: 0.8rem;">{next_dev_interface_name}</span>
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
    ) -> List[VlanTracerouteResult]:

        result: List[VlanTracerouteResult] = []
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
