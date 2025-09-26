import re
from datetime import datetime
from typing import TypedDict

from django.contrib.humanize.templatetags.humanize import naturaltime
from django.utils import timezone

from app_settings.models import VlanTracerouteConfig
from gathering.models import MacAddress
from net_tools.models import DescNameFormat, VlanName


class MacQueryValues(TypedDict):
    type: str
    vlan: int
    port: str
    desc: str
    datetime: datetime
    device__name: str


class MacTraceroute:
    def __init__(self) -> None:
        self.desc_name_list: list[DescNameFormat] = list(DescNameFormat.objects.all())
        # Регулярное выражение, используемое для поиска следующего устройства в описании порта.
        self.find_device_pattern = VlanTracerouteConfig.load().find_device_pattern

        self._reformatting_cache: dict[str, str] = {}

    def get_mac_graph(self, mac: str, vlan: int | None = None) -> dict:
        """
        # Ищем MAC адрес в таблице всех MAC адресов

        Выстраивает граф связей между полученными значениями.

            (D)      (C)---------(B)
             \\       /
              \\     /
               \\   /
                \\ /
                (E)---------(A)

        :param mac: MAC адрес, который нужно найти в таблице.
        :param vlan: VLAN, в котором MAC адрес.
        :return: Словарь: {"nodes": [...], "edges": [...]}
        """

        # Запрос, который выбирает все объекты MacAddress, имеющие MAC-адрес, переданный в URL-адресе.
        macs_objects = (
            MacAddress.objects.filter(address=mac)
            .select_related("device")
            .values("type", "vlan", "port", "desc", "datetime", "device__name")
        )
        if vlan:
            macs_objects = macs_objects.filter(vlan=vlan)

        nodes = []
        edges = []
        vlans_count: dict[int, int] = {}

        # Создание списка всех устройств, которые были найдены в traceroute.
        found_devices_names = [record["device__name"] for record in macs_objects]
        exist_nodes_id = []

        for record in macs_objects:  # type: MacQueryValues
            print(record)
            next_device_id, next_device_label = self.get_next_device(record)

            # Проверка отсутствия следующего устройства в списке найденных устройств и уже добавленных.
            if next_device_id not in found_devices_names and next_device_id not in exist_nodes_id:
                # Добавление нового узла в список узлов.
                nodes.append(
                    {
                        "id": next_device_id,
                        "label": next_device_label,
                        "shape": "dot",
                        "color": "green",
                    }
                )
                # Добавление следующего устройства в список существующих узлов.
                exist_nodes_id.append(next_device_id)

            # Проверка наличия имени устройства в списке созданных узлов.
            if record["device__name"] not in exist_nodes_id:
                # Добавление нового узла в список узлов.
                nodes.append(
                    {
                        "id": record["device__name"],
                        "title": self.create_edge_title(record),
                        "label": record["device__name"],
                        "shape": "dot",
                        "color": "blue",
                    }
                )
                # Добавление имени устройства в список существующих узлов.
                exist_nodes_id.append(record["device__name"])

            # Он вычисляет разницу во времени между текущим временем и временем создания записи.
            time_delta = timezone.now().timestamp() - record["datetime"].timestamp()
            # Вычисляем вес. Чем запись новее, тем больше вес.
            #         `172800` - количество секунд в двух днях.
            #         `100` - максимальный вес.
            #         `time_delta` - разница во времени между текущим временем и временем создания записи.
            k_value = int((1 - time_delta / 172800) * 100)

            # Вычисляем непрозрачность ребра. Чем больше вес, тем меньше прозрачность.
            # `hex(int(2.55 * k_value))` возвращает шестнадцатеричное строковое представление числа.
            #         `[2:]` возвращает подстроку строки, начиная с третьего символа.
            #         Например, `hex(int(2.55 * 100))` возвращает `0x64`, а `hex(int(2.55 * 100))[2:]` возвращает `64`.
            #         Это делается для того, чтобы получить шестнадцатеричное представление числа без префикса `0x`.
            opacity = hex(int(2.55 * k_value))[2:]

            # Вычисляем цвет ребра и добавляем уровень непрозрачности в шестнадцатеричном формате
            edge_color = self.create_edge_color(record["type"]) + opacity

            # Добавление нового ребра в список ребер.
            edges.append(
                {
                    "from": record["device__name"],
                    "to": next_device_id,
                    "title": self.create_edge_title(record),
                    "value": k_value,
                    "color": edge_color,
                }
            )
            vlans_count.setdefault(record["vlan"], 0)
            vlans_count[record["vlan"]] += 1

        vlan_names = self.get_vlan_names(list(vlans_count.keys()))

        vlans_count_list = []
        for vid, count in vlans_count.items():
            vlan_info = vlan_names.get(vid)
            vlans_count_list.append(
                {
                    "vid": vid,
                    "count": count,
                    "name": vlan_info["name"] if vlan_info else "",
                    "description": vlan_info["description"] if vlan_info else "",
                }
            )

        return {
            "nodes": nodes,
            "edges": edges,
            "vlansInfo": vlans_count_list,
        }

    @staticmethod
    def get_vlan_names(vlans: list[int]) -> dict[int, dict[str, str]]:
        qs = VlanName.objects.all().only("name", "vid", "description").filter(vid__in=vlans)
        return {vlan.vid: {"name": vlan.name or "", "description": vlan.description} for vlan in qs}

    def reformatting(self, name: str):
        """
        ### Форматируем строку с названием оборудования, приводя его в единый стандарт, указанный в DescNameFormat
        """
        if (new_name := self._reformatting_cache.get(name)) is not None:
            return new_name

        for reformat in self.desc_name_list:
            if reformat.standard == name:
                # Если имя совпадает с правильным, то отправляем его
                self._reformatting_cache[name] = name
                return name

            for pattern in reformat.replacement.split(", "):
                # Если паттерн содержится в исходном имени
                if re.search(pattern, name, flags=re.IGNORECASE):
                    # Заменяем совпадение "pattern" в названии "name" на правильное "n"
                    new_name = re.sub(pattern, reformat.standard, name, flags=re.IGNORECASE)
                    self._reformatting_cache[name] = new_name
                    return new_name

        # Если не требуется замены
        self._reformatting_cache[name] = name
        return name

    @staticmethod
    def create_edge_title(mac_object: MacQueryValues) -> str:
        """
        ### Эта функция принимает объект MAC-адреса и возвращает строку, являющуюся заголовком ребра.
        """
        if mac_object["type"] == "D":
            type_ = '<span class="px-2 rounded text-white bg-primary" style="vertical-align: middle;">dynamic</span>'
        elif mac_object["type"] == "S":
            type_ = '<span class="px-2 rounded bg-secondary" style="vertical-align: middle;">static</span>'
        elif mac_object["type"] == "E":
            type_ = '<span class="px-2 rounded bg-warning text-dark" style="vertical-align: middle;">security</span>'
        else:
            type_ = (
                '<span class="px-2 rounded bg-light text-dark" style="vertical-align: middle;">none</span>'
            )

        return f"""
        <div class="p-3 rounded font-mono" style="font-size: 16px;">
            <div>From: <b>{mac_object["device__name"]}</b>; Port: <b>{mac_object["port"]}</b></div>
            <div>To: "{mac_object["desc"]}"</div>
            <div>
                VLAN: <span class="px-2 rounded text-white bg-primary">{mac_object["vlan"]}</span>
            </div>
            <div>
                Type: {type_}
            </div>
            <div>
                Обнаружен <b>{naturaltime(mac_object["datetime"])}</b>
            </div>
        </div>
        """

    @staticmethod
    def create_edge_color(mac_type: str) -> str:
        """
        ### Принимает MAC-адрес и возвращает цвет ребра основываясь на типе MAC.

        :param mac_type: Тип MAC `D`, `S` или `E`. Dynamic, static или security.
        :return: Цвет ребра.
        """

        if mac_type == "D":
            return "#73beff"
        if mac_type == "E":
            return "#ffbb56"

        return "#ffffff"

    def get_next_device(self, mac_address: MacQueryValues) -> tuple[str, str]:
        """
        ### Принимает объект mac_address и возвращает кортеж строк, где первая строка — это имя следующего устройства, а
        вторая строка — описание следующего устройства.

        :param mac_address: MacAddress — объект, содержащий MAC-адрес и описание порта, на котором он расположен.
        :return: Кортеж из двух строк.
        """
        # Ищем в описании на порту следующее устройство по паттерну
        next_device_match = re.findall(self.find_device_pattern, self.reformatting(mac_address["desc"]))
        # Если нашли в описании следующее оборудование
        if next_device_match:
            next_device_id = next_device_label = next_device_match[0]

        # Если следующее устройство не найдено в описании,
        # то следующему устройству присваивается имя текущего устройства и номер порта.
        else:
            next_device_id = mac_address["device__name"] + "-" + mac_address["port"]
            next_device_label = mac_address["desc"] or "<no desc>"

        return next_device_id, next_device_label
