from pyvis.network import Network

from ..services.finder import TracerouteResult


def build_traceroute_options(nodes_count: int, edges_count: int) -> dict:
    """Build vis-network options based on visible graph size."""
    nodes_count = max(nodes_count, 1)
    edges_count = max(edges_count, 0)
    density = edges_count / nodes_count
    is_large_graph = nodes_count > 300 or edges_count > 600
    is_huge_graph = nodes_count > 1200 or edges_count > 2500

    if is_large_graph:
        spring_length = max(120, min(420, int(70 + nodes_count * 0.08 + density * 25)))
        gravitational_constant = -max(500, min(12000, int(nodes_count * 2.4 + edges_count * 0.35)))
        return {
            "layout": {"randomSeed": 12345, "improvedLayout": not is_huge_graph},
            "edges": {"smooth": {"enabled": not is_huge_graph, "type": "continuous"}},
            "physics": {
                "enabled": True,
                "solver": "forceAtlas2Based",
                "forceAtlas2Based": {
                    "avoidOverlap": 0.35 if nodes_count < 800 else 0.15,
                    "centralGravity": 0.012 if density < 2 else 0.02,
                    "damping": 0.62,
                    "gravitationalConstant": gravitational_constant,
                    "springConstant": 0.025 if density < 2 else 0.04,
                    "springLength": spring_length,
                },
                "stabilization": {
                    "enabled": True,
                    "fit": True,
                    "iterations": max(600, min(3500, nodes_count * 3 + edges_count)),
                    "onlyDynamicEdges": False,
                    "updateInterval": 50,
                },
                "timestep": 0.45,
            },
        }

    node_distance = max(130, min(360, int(110 + nodes_count * 0.45 + density * 30)))
    return {
        "layout": {"randomSeed": 12345, "improvedLayout": True},
        "edges": {"smooth": {"enabled": True, "type": "dynamic"}},
        "physics": {
            "enabled": True,
            "solver": "repulsion",
            "repulsion": {
                "centralGravity": 0.08 if nodes_count > 80 else 0.18,
                "damping": 0.82 if density > 2 else 0.88,
                "nodeDistance": node_distance,
                "springConstant": 0.04 if density > 2 else 0.055,
                "springLength": max(120, min(260, int(node_distance * 1.15))),
            },
            "stabilization": {
                "enabled": True,
                "fit": True,
                "iterations": max(350, min(1800, nodes_count * 8 + edges_count * 2)),
                "onlyDynamicEdges": False,
                "updateInterval": 50,
            },
        },
    }


class VlanNetwork:
    def __init__(self, network: Network):
        self._net = network
        self._options: dict = build_traceroute_options(1, 0)

    @property
    def nodes(self):
        return self._net.nodes

    @property
    def edges(self):
        return self._net.edges

    @property
    def options(self):
        return self._options

    def create_network(
        self,
        data: list[TracerouteResult],
        show_admin_down_ports: bool = False,
        nodes_only: bool = False,
    ):
        # Создаем невидимые элементы, для инициализации групп 0-9
        # 0 - голубой;      1 - желтый;     2 - красный;    3 - зеленый;            4 - розовый;
        # 5 - пурпурный;    6 - оранжевый;  7 - синий;      8 - светло-красный;     9 - светло-зеленый
        for i in range(10):
            self._net.add_node(i, i, title="", group=i, hidden=True)

        # Создаем элементы и связи между ними
        self._create_nodes(data, show_admin_down_ports, nodes_only)

        neighbor_map = self._net.get_adj_list()
        visible_nodes_count = sum(1 for node in self._net.nodes if not node.get("hidden"))
        edges_count = len(self._net.edges)
        self._options = build_traceroute_options(visible_nodes_count, edges_count)

        # Настройка физики для карты сети.

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

    def _create_nodes(self, result: list[TracerouteResult], show_admin_down_ports: bool, nodes_only: bool):
        """
        ## Создает элементы и связи между ними для карты VLAN
        """

        existing_nodes = set(self._net.get_nodes())

        for e in result:
            if nodes_only and ("p:(" in e.node.lower() or "p:(" in e.next_node.lower()):
                continue
            if nodes_only and ("d:(" in e.node.lower() or "d:(" in e.next_node.lower()):
                continue
            # По умолчанию зеленый цвет, форма точки
            src_gr = 3
            dst_gr = 3
            src_shape = "dot"
            dst_shape = "dot"
            src_label = e.node
            dst_label = e.next_node
            line_width: int | float = e.line_width

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

            # Создаем узлы, если их не было
            if e.node not in existing_nodes:
                self._net.add_node(e.node, src_label, title=src_label, group=src_gr, shape=src_shape)
                existing_nodes.add(e.node)

            if e.next_node not in existing_nodes:
                self._net.add_node(
                    e.next_node,
                    dst_label,
                    title=dst_label,
                    group=dst_gr,
                    shape=dst_shape,
                )
                existing_nodes.add(e.next_node)

            # Добавление ребра между двумя узлами.
            self._net.add_edge(e.node, e.next_node, value=line_width, title=e.line_description)

    @staticmethod
    def _add_node_neighbors(node, neighbor_list: list[str]):
        title = node["title"] + " Соединено:"

        for i, dev in enumerate(neighbor_list, 1):
            title += f"""<br>{i}. <span>{dev}</span>"""

        node["title"] = title


TracerouteNetwork = VlanNetwork
