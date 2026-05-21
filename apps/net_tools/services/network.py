import re
from dataclasses import dataclass

from django.core.cache import cache

from ..models import TracerouteNodeKind, TracerouteNodeStyleRule
from ..services.finder import TracerouteResult


def build_traceroute_options(nodes_count: int, edges_count: int) -> dict:
    """Build vis-network options based on visible graph size."""
    nodes_count = max(nodes_count, 1)
    edges_count = max(edges_count, 0)
    density = edges_count / nodes_count
    is_large_graph = nodes_count > 300 or edges_count > 600
    is_huge_graph = nodes_count > 1200 or edges_count > 2500

    if is_large_graph:
        node_distance = max(130, min(220, int(125 + nodes_count * 0.03 + density * 16)))
        return {
            "layout": {"randomSeed": 12345, "improvedLayout": not is_huge_graph},
            "edges": {"smooth": {"enabled": not is_huge_graph, "type": "dynamic"}},
            "physics": {
                "enabled": True,
                "solver": "repulsion",
                "repulsion": {
                    "centralGravity": 0.06 if density < 2 else 0.08,
                    "damping": 0.84 if density > 2 else 0.88,
                    "nodeDistance": node_distance,
                    "springConstant": 0.04 if density > 2 else 0.05,
                    "springLength": max(130, min(240, int(node_distance * 1.1))),
                },
                "stabilization": {
                    "enabled": True,
                    "fit": True,
                    "iterations": max(600, min(2800, nodes_count * 2 + edges_count)),
                    "onlyDynamicEdges": False,
                    "updateInterval": 50,
                },
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


@dataclass
class _PreparedRule:
    priority: int
    node_kind_code: str | None
    match_type: str
    pattern: str
    group_id: int | None
    color_background: str
    color_border: str
    color_font: str
    shape: str | None
    fixed_value: int | None
    stop_processing: bool
    regex: re.Pattern[str] | None = None


class VlanNetwork:
    def __init__(self) -> None:
        self._nodes: list[dict] = []
        self._edges: list[dict] = []
        self._node_ids: set[str | int] = set()
        self._options: dict = build_traceroute_options(1, 0)

    @property
    def nodes(self):
        return self._nodes

    @property
    def edges(self):
        return self._edges

    @property
    def options(self):
        return self._options

    def create_network(
        self,
        data: list[TracerouteResult],
        show_admin_down_ports: bool = False,
        nodes_only: bool = False,
    ):
        for i in range(10):
            self._add_node(i, i, {"title": "", "group": i, "hidden": True, "shape": "dot"})

        degree_by_node = self._create_nodes(data, show_admin_down_ports, nodes_only)
        suspicious_node_ids = self._get_suspicious_node_ids()
        visible_nodes_count = sum(1 for node in self._nodes if not node.get("hidden"))
        edges_count = len(self._edges)
        self._options = build_traceroute_options(visible_nodes_count, edges_count)

        for node in self._nodes:
            if node.get("hidden"):
                continue
            if node["id"] in suspicious_node_ids:
                self._mark_node_as_suspicious(node)
            if node.get("fixed_value") is not None:
                node["value"] = node.pop("fixed_value")
                continue
            node["value"] = degree_by_node.get(node["id"], 0) * 3

    @staticmethod
    def _get_kinds_and_rules() -> tuple[dict[str, dict], list[_PreparedRule]]:
        cache_key = "net_tools:vlan_network:node_kinds_rules:v1"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        kinds_qs = TracerouteNodeKind.objects.all()
        rules_qs = TracerouteNodeStyleRule.objects.filter(is_active=True).select_related("node_kind")

        kinds: dict[str, dict] = {}
        for kind in kinds_qs:
            kinds[kind.code] = {
                "marker_prefix": kind.marker_prefix,
                "marker_suffix": kind.marker_suffix,
                "value_source": kind.value_source,
                "hide_when_nodes_only": kind.hide_when_nodes_only,
            }

        rules: list[_PreparedRule] = []
        for rule in rules_qs:
            regex = None
            if rule.match_type == TracerouteNodeStyleRule.MatchType.REGEX and rule.pattern:
                regex = re.compile(rule.pattern, flags=re.IGNORECASE)
            rules.append(
                _PreparedRule(
                    priority=rule.priority,
                    node_kind_code=rule.node_kind.code if rule.node_kind else None,
                    match_type=rule.match_type,
                    pattern=rule.pattern or "",
                    group_id=rule.group_id,
                    color_background=rule.color_background,
                    color_border=rule.color_border,
                    color_font=rule.color_font,
                    shape=rule.shape,
                    fixed_value=rule.fixed_value,
                    stop_processing=rule.stop_processing,
                    regex=regex,
                )
            )

        rules.sort(key=lambda item: item.priority)
        cache.set(cache_key, (kinds, rules), 60)
        return kinds, rules

    @staticmethod
    def _extract_kind(raw: str, kinds: dict[str, dict]) -> tuple[str | None, str]:
        for code, data in kinds.items():
            prefix = str(data["marker_prefix"])
            suffix = str(data["marker_suffix"])
            if not prefix:
                continue
            if prefix not in raw:
                continue

            if data["value_source"] == TracerouteNodeKind.ValueSource.MARKER_BODY:
                if suffix and suffix in raw:
                    start = raw.find(prefix) + len(prefix)
                    end = raw.rfind(suffix)
                    if end >= start:
                        return code, raw[start:end]
                start = raw.find(prefix) + len(prefix)
                return code, raw[start:]

            if data["value_source"] == TracerouteNodeKind.ValueSource.AFTER_ARROW:
                start = raw.find(prefix) + len(prefix)
                return code, raw[start:]

            return code, raw
        return None, raw

    @staticmethod
    def _matches_rule(raw: str, raw_lower: str, rule: _PreparedRule) -> bool:
        if not rule.pattern:
            return True
        if rule.match_type == TracerouteNodeStyleRule.MatchType.EXACT:
            return raw_lower == rule.pattern.casefold()
        if rule.match_type == TracerouteNodeStyleRule.MatchType.STARTS_WITH:
            return raw_lower.startswith(rule.pattern.casefold())
        if rule.match_type == TracerouteNodeStyleRule.MatchType.ENDS_WITH:
            return raw_lower.endswith(rule.pattern.casefold())
        if rule.match_type == TracerouteNodeStyleRule.MatchType.REGEX:
            return bool(rule.regex and rule.regex.search(raw))
        return rule.pattern.casefold() in raw_lower

    def _resolve_node_style(self, raw: str, nodes_only: bool) -> dict:
        kinds, rules = self._get_kinds_and_rules()
        kind_code, label = self._extract_kind(raw, kinds)

        if nodes_only and kind_code and kinds.get(kind_code, {}).get("hide_when_nodes_only"):
            return {"hidden": True}

        style: dict = {
            "group": None,
            "shape": "dot",
            "label": label.strip(),
            "fixed_value": None,
            "color": None,
            "font_color": None,
        }
        raw_lower = raw.casefold()
        for rule in rules:
            if rule.node_kind_code and rule.node_kind_code != kind_code:
                continue
            if not self._matches_rule(raw, raw_lower, rule):
                continue
            if rule.group_id is not None:
                style["group"] = rule.group_id
            if rule.color_background or rule.color_border or rule.color_font:
                style["color"] = {
                    "background": rule.color_background or "#97C2FC",
                    "border": rule.color_border or "#2B7CE9",
                    "highlight": {
                        "background": rule.color_background or "#A9D3FF",
                        "border": rule.color_border or "#2B7CE9",
                    },
                    "hover": {
                        "background": rule.color_background or "#A9D3FF",
                        "border": rule.color_border or "#2B7CE9",
                    },
                }
                if rule.color_font:
                    style["font_color"] = rule.color_font
            if rule.shape:
                style["shape"] = rule.shape
            if rule.fixed_value is not None:
                style["fixed_value"] = rule.fixed_value
            if rule.stop_processing:
                break
        return style

    def _create_nodes(
        self, result: list[TracerouteResult], show_admin_down_ports: bool, nodes_only: bool
    ) -> dict[str, int]:
        """Создает элементы и связи между ними для карты VLAN."""
        existing_nodes = set(self._node_ids)
        existing_edges: dict[tuple[str, str], int] = {}
        style_cache: dict[str, dict] = {}
        degree_by_node: dict[str, int] = {}

        for e in result:
            src_node = str(e.node).strip()
            dst_node = str(e.next_node).strip()
            edge_title = e.line_description

            src_style = self._get_cached_node_style(src_node, nodes_only, style_cache)
            dst_style = self._get_cached_node_style(dst_node, nodes_only, style_cache)
            if src_style.get("hidden") or dst_style.get("hidden"):
                continue

            line_width: int | float = e.line_width
            if show_admin_down_ports and e.admin_down_status == "down":
                line_width = 0.5
            edge_options = self._get_edge_options(edge_title)

            if src_node not in existing_nodes:
                node_data = {
                    "title": src_style["label"],
                    "shape": src_style["shape"],
                }
                if src_style["group"] is not None:
                    node_data["group"] = src_style["group"]
                if src_style["color"] is not None:
                    node_data["color"] = src_style["color"]
                if src_style.get("font_color"):
                    node_data["font"] = {"color": src_style["font_color"]}
                if src_style["fixed_value"] is not None:
                    node_data["fixed_value"] = src_style["fixed_value"]
                self._add_node(src_node, src_style["label"], node_data)
                existing_nodes.add(src_node)

            if dst_node not in existing_nodes:
                node_data = {
                    "title": dst_style["label"],
                    "shape": dst_style["shape"],
                }
                if dst_style["group"] is not None:
                    node_data["group"] = dst_style["group"]
                if dst_style["color"] is not None:
                    node_data["color"] = dst_style["color"]
                if dst_style.get("font_color"):
                    node_data["font"] = {"color": dst_style["font_color"]}
                if dst_style["fixed_value"] is not None:
                    node_data["fixed_value"] = dst_style["fixed_value"]
                self._add_node(dst_node, dst_style["label"], node_data)
                existing_nodes.add(dst_node)

            edge_key = self._edge_pair_key(src_node, dst_node)
            if edge_key in existing_edges:
                self._replace_edge_with_better_match(
                    existing_edges[edge_key], src_node, dst_node, line_width, edge_title
                )
                continue
            existing_edges[edge_key] = len(self._edges)
            self._add_edge(src_node, dst_node, line_width, edge_title, edge_options)
            if src_node == dst_node:
                degree_by_node[src_node] = degree_by_node.get(src_node, 0) + 1
            else:
                degree_by_node[src_node] = degree_by_node.get(src_node, 0) + 1
                degree_by_node[dst_node] = degree_by_node.get(dst_node, 0) + 1

        return degree_by_node

    def _get_cached_node_style(self, node_id: str, nodes_only: bool, style_cache: dict[str, dict]) -> dict:
        """Return cached node style for repeated traceroute links."""
        style = style_cache.get(node_id)
        if style is None:
            style = self._resolve_node_style(node_id, nodes_only)
            style_cache[node_id] = style
        return style

    @staticmethod
    def _edge_pair_key(src_node: str, dst_node: str) -> tuple[str, str]:
        """Return undirected edge key for graph edge deduplication."""
        if src_node <= dst_node:
            return src_node, dst_node
        return dst_node, src_node

    def _add_node(self, node_id: str | int, label: str | int, node_data: dict) -> None:
        """Add a node to the traceroute graph payload."""
        node_options = dict(node_data)
        node_options["id"] = node_id
        node_options["label"] = label
        node_options["shape"] = node_data["shape"]
        if "group" not in node_options and "color" not in node_options:
            node_options["color"] = "#97c2fc"
        node_options["font"] = {"color": "white"}

        self._nodes.append(node_options)
        self._node_ids.add(node_id)

    @staticmethod
    def _get_edge_options(edge_title: dict) -> dict:
        """Возвращает визуальные настройки ребра по качеству VLAN-совпадения."""
        confidence = str(edge_title.get("vlan_match", {}).get("confidence", ""))
        if confidence == "exact":
            return {
                "color": {"color": "#22c55e", "highlight": "#16a34a", "hover": "#86efac"},
                "dashes": False,
            }
        if confidence == "low":
            return {
                "color": {"color": "#94a3b8", "highlight": "#f97316", "hover": "#cbd5e1"},
                "dashes": [6, 5],
            }
        if confidence == "medium":
            return {
                "color": {"color": "#f59e0b", "highlight": "#f97316", "hover": "#fbbf24"},
                "dashes": [8, 4],
            }
        return {}

    @staticmethod
    def _get_edge_confidence_rank(edge_title: dict) -> int:
        """Возвращает ранг точности VLAN-совпадения для выбора лучшего ребра."""
        confidence = str(edge_title.get("vlan_match", {}).get("confidence", "normal"))
        return {"low": 0, "medium": 1, "normal": 2, "high": 3, "exact": 4}.get(confidence, 2)

    @classmethod
    def _is_suspicious_edge(cls, edge: dict) -> bool:
        """Проверяет, считается ли ребро сомнительным."""
        return cls._get_edge_confidence_rank(edge["title"]) <= 1

    @staticmethod
    def _is_network_device_node(node_id: str) -> bool:
        """Проверяет, похож ли узел на сетевое устройство, а не на порт или описание."""
        lowered = str(node_id).casefold()
        return " p:(" not in lowered and " d:(" not in lowered

    def _get_suspicious_node_ids(self) -> set[str]:
        """Возвращает узлы, у которых все связи имеют низкую или среднюю уверенность."""
        total_edges_by_node: dict[str, int] = {}
        suspicious_edges_by_node: dict[str, int] = {}

        for edge in self._edges:
            is_suspicious = self._is_suspicious_edge(edge)
            for node_id in (str(edge["from"]), str(edge["to"])):
                if not self._is_network_device_node(node_id):
                    continue
                total_edges_by_node[node_id] = total_edges_by_node.get(node_id, 0) + 1
                if is_suspicious:
                    suspicious_edges_by_node[node_id] = suspicious_edges_by_node.get(node_id, 0) + 1

        return {
            node_id
            for node_id, total in total_edges_by_node.items()
            if total > 0 and suspicious_edges_by_node.get(node_id, 0) == total
        }

    @staticmethod
    def _mark_node_as_suspicious(node: dict) -> None:
        """Добавляет визуальную метку сомнительного узла."""
        node["suspicious"] = True
        node["opacity"] = 0.5
        node["shape"] = "diamond"
        color = node.get("color")
        if isinstance(color, dict):
            color["background"] = "rgba(124, 58, 237, 0.5)"
            color.setdefault("highlight", {})["background"] = "rgba(124, 58, 237, 0.65)"
            color.setdefault("hover", {})["background"] = "rgba(124, 58, 237, 0.65)"
            return
        node["color"] = {
            "background": "rgba(124, 58, 237, 0.5)",
            "highlight": {"background": "rgba(124, 58, 237, 0.65)"},
            "hover": {"background": "rgba(124, 58, 237, 0.65)"},
        }

    def _replace_edge_with_better_match(
        self,
        edge_index: int,
        src_node: str,
        dst_node: str,
        line_width: int | float,
        edge_title: dict,
    ) -> None:
        """Заменяет дубль ребра, если новое VLAN-совпадение точнее текущего."""
        existing_edge = self._edges[edge_index]
        if self._get_edge_confidence_rank(edge_title) <= self._get_edge_confidence_rank(existing_edge["title"]):
            return

        data = self._build_edge_data(src_node, dst_node, line_width, edge_title, self._get_edge_options(edge_title))
        existing_edge.clear()
        existing_edge.update(data)

    @staticmethod
    def _build_edge_data(
        src_node: str,
        dst_node: str,
        line_width: int | float,
        edge_title: dict,
        edge_options: dict | None = None,
    ) -> dict:
        """Собирает payload ребра графа."""
        data = {
            "from": src_node,
            "to": dst_node,
            "value": line_width,
            "title": edge_title,
        }
        if edge_options:
            data.update(edge_options)
        return data

    def _add_edge(
        self,
        src_node: str,
        dst_node: str,
        line_width: int | float,
        edge_title: dict,
        edge_options: dict | None = None,
    ) -> None:
        """Add an edge to the traceroute graph payload."""
        self._edges.append(self._build_edge_data(src_node, dst_node, line_width, edge_title, edge_options))


TracerouteNetwork = VlanNetwork
