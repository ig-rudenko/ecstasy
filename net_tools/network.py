from typing import List

from pyvis.network import Network

from net_tools.finder import VlanTracerouteResult


class VlanNetwork:
    def __init__(self, network: Network):
        self._net = network

    @property
    def nodes(self):
        return self._net.nodes

    @property
    def edges(self):
        return self._net.edges

    @property
    def options(self):
        return self._net.options

    def create_network(
        self, data: List[VlanTracerouteResult], show_admin_down_ports: bool = False
    ):

        # Создаем невидимые элементы, для инициализации групп 0-9
        # 0 - голубой;      1 - желтый;     2 - красный;    3 - зеленый;            4 - розовый;
        # 5 - пурпурный;    6 - оранжевый;  7 - синий;      8 - светло-красный;     9 - светло-зеленый
        for i in range(10):
            self._net.add_node(i, i, title="", group=i, hidden=True)

        # Создаем элементы и связи между ними
        self._create_nodes(data, show_admin_down_ports)

        neighbor_map = self._net.get_adj_list()
        nodes_count = len(self._net.nodes)

        # Настройка физики для карты сети.
        self._net.repulsion(
            node_distance=nodes_count if nodes_count > 130 else 130, damping=0.89
        )

        # Итерация по всем узлам в сети.
        for node in self._net.nodes:
            # Установка размера узла на основе количества соседей.
            node["value"] = len(neighbor_map[node["id"]]) * 3
            if "core" in node["title"].lower():
                node["value"] = 70
            if "-cr" in node["title"].lower():
                node["value"] = 100
            # Пустой порт.
            # Устанавливаем размер узла равным 1, если узел является портом.
            if "p:(" in node["title"]:
                node["value"] = 1
            # Добавление списка соседей в заголовок узла.
            self._add_node_neighbors(node, neighbor_map[node["id"]])

        # Установка сглаживания краев на динамическое.
        self._net.set_edge_smooth("dynamic")

    def _create_nodes(
        self, result: List[VlanTracerouteResult], show_admin_down_ports: bool
    ):
        """
        ## Создает элементы и связи между ними для карты VLAN
        """

        for e in result:
            # По умолчанию зеленый цвет, форма точки
            src_gr = 3
            dst_gr = 3
            src_shape = "dot"
            dst_shape = "dot"
            src_label = e.node
            dst_label = e.next_node
            line_width = e.line_width

            # ASW: желтый
            if "ASW" in e.node:
                src_gr = 1
            if "ASW" in e.next_node:
                dst_gr = 1

            # SSW: голубой
            if "SSW" in e.node:
                src_gr = 0
            if "SSW" in e.next_node:
                dst_gr = 0

            # Порт: зеленый, форма треугольника - △
            if "-->" in e.node.lower():
                src_gr = 3
                src_shape = "triangle"
                src_label = e.node.split("-->")[1]
            if "-->" in e.next_node.lower():
                dst_gr = 3
                dst_shape = "triangle"
                dst_label = e.node.split("-->")[1]

            # DSL: оранжевый, форма квадрата - ☐
            if "DSL" in e.node:
                src_gr = 6
                src_shape = "square"
            if "DSL" in e.next_node:
                dst_gr = 6
                dst_shape = "square"

            # CORE: розовый, форма ромба - ◊
            if "SVSL-99-GP15-SSW" in e.node or "SVSL-99-GP15-SSW" in e.next_node:
                src_gr = 4
                src_shape = "diamond"
            if "core" in e.node.lower() or "-cr" in e.next_node.lower():
                src_gr = 4
                src_shape = "diamond"
            if "core" in e.next_node.lower() or "-cr" in e.node.lower():
                dst_gr = 4
                dst_shape = "diamond"

            # Пустой порт: светло-зеленый, форма треугольника - △
            if "p:(" in e.node.lower():
                src_gr = 9
                src_shape = "triangle"
                src_label = e.node.split("p:(")[1][:-1]
            if "p:(" in e.next_node.lower():
                dst_gr = 9
                dst_shape = "triangle"
                dst_label = e.next_node.split("p:(")[1][:-1]

            # Только описание: зеленый
            if "d:(" in e.node.lower():
                src_gr = 3
                src_label = e.node.split("d:(")[1][:-1]
            if "d:(" in e.next_node.lower():
                dst_gr = 3
                dst_label = e.next_node.split("d:(")[1][:-1]

            # Если стиль отображения admin down status
            if show_admin_down_ports and e.admin_down_status == "down":
                line_width = 0.5  # ширина линии связи
            # print(src, admin_status)

            all_nodes = self._net.get_nodes()
            # Создаем узлы, если их не было
            if e.node not in all_nodes:
                self._net.add_node(
                    e.node, src_label, title=src_label, group=src_gr, shape=src_shape
                )

            if e.next_node not in all_nodes:
                self._net.add_node(
                    e.next_node,
                    dst_label,
                    title=dst_label,
                    group=dst_gr,
                    shape=dst_shape,
                )

            # Добавление ребра между двумя узлами.
            self._net.add_edge(
                e.node, e.next_node, value=line_width, title=e.line_description
            )

    @staticmethod
    def _add_node_neighbors(node, neighbor_list: List[str]):
        title = node["title"] + " Соединено:"

        for i, dev in enumerate(neighbor_list, 1):
            title += f"""<br>{i}. <span>{dev}</span>"""

        node["title"] = title
