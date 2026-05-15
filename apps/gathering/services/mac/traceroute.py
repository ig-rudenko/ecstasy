import re
from datetime import datetime
from typing import TypedDict

from django.contrib.humanize.templatetags.humanize import naturaltime
from django.utils import timezone

from apps.app_settings.models import VlanTracerouteConfig
from apps.net_tools.models import DescNameFormat, VlanName
from apps.net_tools.services.network import build_traceroute_options

from ...models import MacAddress


class MacQueryValues(TypedDict):
    type: str
    vlan: int
    port: str
    desc: str
    datetime: datetime
    device__name: str
    device__group__name: str


class MacTraceroute:
    def __init__(self) -> None:
        self.desc_name_list: list[DescNameFormat] = list(DescNameFormat.objects.all())
        # Регулярное выражение, используемое для поиска следующего устройства в описании порта.
        self.find_device_pattern = VlanTracerouteConfig.load().find_device_pattern

        self._reformatting_cache: dict[str, str] = {}

    def get_mac_graph(
        self,
        mac: str,
        vlan: int | None = None,
        device_name_filter: str = "",
        group_filter: str = "",
        show_empty_ports: bool = False,
        graph_min_length: int = 0,
        nodes_only: bool = False,
    ) -> dict:
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
        macs_objects = MacAddress.objects.filter(address=mac).values(
            "type", "vlan", "port", "desc", "datetime", "device__name", "device__group__name"
        )
        if vlan:
            macs_objects = macs_objects.filter(vlan=vlan)
        if device_name_filter:
            macs_objects = macs_objects.filter(device__name__icontains=device_name_filter)
        if group_filter:
            macs_objects = macs_objects.filter(device__group__name__icontains=group_filter)

        nodes = []
        edges = []
        vlans_count: dict[int, int] = {}

        # Создание списка всех устройств, которые были найдены в traceroute.
        found_devices_names = {record["device__name"] for record in macs_objects}
        exist_nodes_id: set[str] = set()
        current_timestamp = timezone.now().timestamp()

        for record in macs_objects:  # type: MacQueryValues
            next_device_id, next_device_label = self.get_next_device(record)
            if not show_empty_ports and not record["desc"]:
                continue
            if nodes_only and next_device_id == f"{record['device__name']}-{record['port']}":
                continue
            if not self._matches_device_name_filter(
                record["device__name"],
                next_device_id,
                record["desc"],
                device_name_filter,
            ):
                continue
            edge_title = self.create_edge_title(record)

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
                exist_nodes_id.add(next_device_id)

            # Проверка наличия имени устройства в списке созданных узлов.
            if record["device__name"] not in exist_nodes_id:
                # Добавление нового узла в список узлов.
                nodes.append(
                    {
                        "id": record["device__name"],
                        "title": edge_title,
                        "label": record["device__name"],
                        "shape": "dot",
                        "color": "blue",
                    }
                )
                # Добавление имени устройства в список существующих узлов.
                exist_nodes_id.add(record["device__name"])

            # Он вычисляет разницу во времени между текущим временем и временем создания записи.
            time_delta = current_timestamp - record["datetime"].timestamp()
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
                    "title": edge_title,
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

        if graph_min_length:
            nodes, edges = self._filter_graph_min_length(nodes, edges, graph_min_length)

        return {
            "nodes": nodes,
            "edges": edges,
            "options": build_traceroute_options(len(nodes), len(edges)),
            "vlansInfo": vlans_count_list,
        }

    @staticmethod
    def _matches_device_name_filter(
        device: str,
        next_device: str,
        description: str,
        device_name_filter: str,
    ) -> bool:
        """Check that a MAC graph edge matches the device-name filter."""
        if not device_name_filter:
            return True

        filter_value = device_name_filter.casefold()
        return (
            filter_value in device.casefold()
            or filter_value in next_device.casefold()
            or filter_value in description.casefold()
        )

    @staticmethod
    def _filter_graph_min_length(nodes: list[dict], edges: list[dict], graph_min_length: int) -> tuple[list[dict], list[dict]]:
        """Drop connected components with fewer nodes than graph_min_length."""
        if not nodes or not edges:
            return nodes, edges

        adjacency: dict[str, set[str]] = {}
        for edge in edges:
            source = edge["from"]
            target = edge["to"]
            adjacency.setdefault(source, set()).add(target)
            adjacency.setdefault(target, set()).add(source)

        allowed_nodes: set[str] = set()
        visited: set[str] = set()
        for node_id in adjacency:
            if node_id in visited:
                continue

            stack = [node_id]
            component: set[str] = set()
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                component.add(current)
                stack.extend(adjacency.get(current, set()) - visited)

            if len(component) >= graph_min_length:
                allowed_nodes.update(component)

        return (
            [node for node in nodes if node["id"] in allowed_nodes],
            [edge for edge in edges if edge["from"] in allowed_nodes and edge["to"] in allowed_nodes],
        )

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
