from typing import Any, cast
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.check.services.zabbix import DeviceCoords
from apps.net_tools.services.finder import MultipleTraceroute, Traceroute, TracerouteResult
from apps.net_tools.services.network import VlanNetwork
from apps.net_tools.services.traceroute import build_traceroute_map_data
from devicemanager.device.interfaces import Interface, Interfaces


class FakeDevicesQuerySet:
    """Минимальная замена queryset для проверки обхода стартовых устройств."""

    def __init__(self, names: list[str]) -> None:
        self._names = names

    def values_list(self, field_name: str, flat: bool = False) -> list[str]:
        """Возвращает имена устройств так же, как queryset.values_list."""
        if field_name != "name" or not flat:
            raise ValueError("FakeDevicesQuerySet supports only flat name values.")
        return self._names


class StubTraceroute(Traceroute):
    """Тестовый VlanTraceroute без обращений к базе данных."""

    def __init__(self) -> None:
        self.result: list[TracerouteResult] = []
        self._result_keys: set[tuple[str, str, str, str]] = set()
        self._desc_name_list = []
        self._desc_name_formats_loaded = True
        self._desc_name_standards: set[str] = set()
        self._desc_name_patterns = []
        self.passed_devices: set[str] = set()
        self._devices_vlans_info: dict[str, str | None] = {}
        self._device_interfaces_cache: dict[str, Interfaces] = {}
        self._device_ip_names: dict[str, str] = {}
        self._cache_timeout = 0
        self._reformatting_cache: dict[str, str] = {}
        self._pattern_cache = {}
        self._device_name_pattern_cache = {}
        self._interfaces_by_device: dict[str, Interfaces] = {
            "dev-a": Interfaces([Interface(name="eth1", status="up", desc="dev-b", vlan=[100])]),
            "dev-b": Interfaces([Interface(name="eth2", status="up", desc="dev-c", vlan=[100])]),
            "dev-c": Interfaces([Interface(name="eth3", status="up", desc="", vlan=[100])]),
        }

    def _get_device_interfaces(self, device_name: str) -> Interfaces:
        """Возвращает интерфейсы из тестового словаря."""
        return self._interfaces_by_device.get(device_name, Interfaces())


class TracerouteTraversalTestCase(SimpleTestCase):
    def _make_finder(self) -> StubTraceroute:
        """Создает finder без обращения к базе данных."""
        return StubTraceroute()

    def test_find_vlan_keeps_recursive_traversal(self) -> None:
        """Трассировка рекурсивно обходит связанный подграф."""
        finder = self._make_finder()

        finder.find_vlan(
            device="dev-a",
            vlan_to_find=100,
            empty_ports=False,
            only_admin_up=False,
            find_device_pattern=r"dev-[a-z]",
            double_check=False,
        )

        self.assertEqual(finder.passed_devices, {"dev-a", "dev-b", "dev-c"})
        self.assertEqual(
            [(edge.node, edge.next_node) for edge in finder.result],
            [("dev-a", "dev-b"), ("dev-b", "dev-c")],
        )

    def test_find_vlan_applies_device_name_filter_to_internal_edges(self) -> None:
        """Device-name filter limits edges found after the root queryset is selected."""
        finder = self._make_finder()

        finder.find_vlan(
            device="dev-a",
            vlan_to_find=100,
            empty_ports=False,
            only_admin_up=False,
            find_device_pattern=r"dev-[a-z]",
            double_check=False,
            device_name_filter="dev-a",
        )

        self.assertEqual(finder.passed_devices, {"dev-a", "dev-b"})
        self.assertEqual(
            [(edge.node, edge.next_node) for edge in finder.result],
            [("dev-a", "dev-b")],
        )

    def test_find_vlan_skips_ports_over_vlan_count_limit(self) -> None:
        """VLAN трассировка пропускает trunk-порты с количеством VLAN больше лимита."""
        finder = self._make_finder()
        finder._interfaces_by_device["dev-a"] = Interfaces(
            [
                Interface(name="eth1", status="up", desc="dev-b", vlan=list(range(1, 3502))),
                Interface(name="eth2", status="up", desc="dev-c", vlan=[100]),
            ]
        )

        finder.find_vlan(
            device="dev-a",
            vlan_to_find=100,
            empty_ports=False,
            only_admin_up=False,
            find_device_pattern=r"dev-[a-z]",
            double_check=False,
            max_port_vlans=3000,
        )

        self.assertEqual(
            [(edge.node, edge.next_node) for edge in finder.result],
            [("dev-a", "dev-c")],
        )

    def test_find_vlan_marks_broad_trunk_ports(self) -> None:
        """VLAN трассировка помечает широкие trunk-порты как низкую уверенность."""
        finder = self._make_finder()
        finder._interfaces_by_device["dev-a"] = Interfaces(
            [Interface(name="eth1", status="up", desc="dev-b", vlan=list(range(1, 711)))]
        )

        finder.find_vlan(
            device="dev-a",
            vlan_to_find=100,
            empty_ports=False,
            only_admin_up=False,
            find_device_pattern=r"dev-[a-z]",
            double_check=False,
            trunk_filter_mode="mark_broad",
        )

        self.assertEqual(finder.result[0].line_description["vlan_match"]["confidence"], "low")
        self.assertTrue(finder.result[0].line_description["vlan_match"]["src"]["broad_trunk"])

    def test_find_vlan_marks_small_vlan_set_as_exact_match(self) -> None:
        """VLAN трассировка помечает порт с малым набором VLAN как точное совпадение."""
        finder = self._make_finder()
        finder._interfaces_by_device["dev-a"] = Interfaces(
            [Interface(name="eth1", status="up", desc="dev-b", vlan=[98, 99, 100, 101, 102])]
        )

        finder.find_vlan(
            device="dev-a",
            vlan_to_find=100,
            empty_ports=False,
            only_admin_up=False,
            find_device_pattern=r"dev-[a-z]",
            double_check=False,
            trunk_filter_mode="mark_broad",
        )

        vlan_match = finder.result[0].line_description["vlan_match"]
        self.assertEqual(vlan_match["confidence"], "exact")
        self.assertTrue(vlan_match["exact_match"])
        self.assertTrue(vlan_match["src"]["exact_match"])
        self.assertEqual(vlan_match["src"]["reason"], "small_vlan_set_exact_match")

    def test_find_vlan_marks_single_vlan_as_exact_match(self) -> None:
        """VLAN трассировка помечает одиночный VLAN на порту как точное совпадение."""
        finder = self._make_finder()
        finder._interfaces_by_device["dev-a"] = Interfaces(
            [Interface(name="eth1", status="up", desc="dev-b", vlan=[100])]
        )

        finder.find_vlan(
            device="dev-a",
            vlan_to_find=100,
            empty_ports=False,
            only_admin_up=False,
            find_device_pattern=r"dev-[a-z]",
            double_check=False,
            trunk_filter_mode="mark_broad",
        )

        vlan_match = finder.result[0].line_description["vlan_match"]
        self.assertEqual(vlan_match["confidence"], "exact")
        self.assertEqual(vlan_match["src"]["reason"], "single_vlan_exact_match")

    def test_find_vlan_requires_both_checked_ports_for_exact_link(self) -> None:
        """При double-check связь точная только если обе стороны имеют малый набор VLAN."""
        finder = self._make_finder()
        finder._interfaces_by_device["dev-a"] = Interfaces(
            [Interface(name="eth1", status="up", desc="dev-b", vlan=[100])]
        )
        finder._interfaces_by_device["dev-b"] = Interfaces(
            [Interface(name="eth2", status="up", desc="dev-a", vlan=list(range(90, 111)))]
        )

        finder.find_vlan(
            device="dev-a",
            vlan_to_find=100,
            empty_ports=False,
            only_admin_up=False,
            find_device_pattern=r"dev-[a-z]",
            double_check=True,
            trunk_filter_mode="mark_broad",
        )

        vlan_match = finder.result[0].line_description["vlan_match"]
        self.assertEqual(vlan_match["confidence"], "high")
        self.assertFalse(vlan_match["exact_match"])

    def test_find_vlan_keeps_specific_range_on_large_vlan_port_confident(self) -> None:
        """Большой список VLAN не считается broad trunk, если искомый VLAN в малом диапазоне."""
        finder = self._make_finder()
        scattered_vlans = [
            8,
            23,
            36,
            63,
            101,
            106,
            110,
            119,
            *range(195, 236),
            *range(242, 518),
            *range(1943, 1948),
            1949,
            1959,
            1961,
            1962,
            1969,
            1990,
            1991,
            1993,
            1994,
            2000,
            2005,
            2496,
            2562,
            2620,
            2676,
            2846,
            2848,
            2849,
            2850,
            3000,
            3438,
            3500,
            3715,
            3720,
            3900,
            3927,
            3928,
            3929,
            3966,
            3972,
            4007,
            4016,
            4017,
            4018,
            4021,
            4022,
            4023,
            4024,
            4025,
        ]
        finder._interfaces_by_device["dev-a"] = Interfaces(
            [Interface(name="eth1", status="up", desc="dev-b", vlan=scattered_vlans)]
        )

        finder.find_vlan(
            device="dev-a",
            vlan_to_find=1944,
            empty_ports=False,
            only_admin_up=False,
            find_device_pattern=r"dev-[a-z]",
            double_check=False,
            trunk_filter_mode="mark_broad",
        )

        vlan_match = finder.result[0].line_description["vlan_match"]
        self.assertEqual(vlan_match["confidence"], "high")
        self.assertFalse(vlan_match["src"]["broad_trunk"])
        self.assertEqual(vlan_match["src"]["matched_range"], {"from": 1943, "to": 1947})

    def test_find_vlan_hides_broad_trunk_ports(self) -> None:
        """VLAN трассировка может скрывать широкие trunk-порты."""
        finder = self._make_finder()
        finder._interfaces_by_device["dev-a"] = Interfaces(
            [Interface(name="eth1", status="up", desc="dev-b", vlan=list(range(1, 711)))]
        )

        finder.find_vlan(
            device="dev-a",
            vlan_to_find=100,
            empty_ports=False,
            only_admin_up=False,
            find_device_pattern=r"dev-[a-z]",
            double_check=False,
            trunk_filter_mode="hide_broad",
        )

        self.assertEqual(finder.result, [])


class MultipleTracerouteTestCase(SimpleTestCase):
    def test_execute_traceroute_skips_already_processed_roots(self) -> None:
        """Повторные стартовые устройства из уже обработанного подграфа пропускаются."""
        finder = self._make_fake_finder()
        traceroute = MultipleTraceroute(
            finder=finder, devices_queryset=cast(Any, FakeDevicesQuerySet(["dev-a", "dev-b"]))
        )

        traceroute.execute_traceroute(
            vlan=100,
            empty_ports=False,
            only_admin_up=False,
            find_device_pattern=r"dev-[a-z]",
            double_check=False,
            graph_min_length=0,
            device_name_filter="",
        )

        self.assertEqual(finder.calls, ["dev-a"])

    @staticmethod
    def _make_fake_finder():
        """Создает объект с интерфейсом VlanTraceroute для проверки MultipleVlanTraceroute."""

        class FakeFinder:
            def __init__(self) -> None:
                self.result: list[TracerouteResult] = []
                self.passed_devices: set[str] = set()
                self.calls: list[str] = []

            def reset_state(self) -> None:
                """Сбрасывает состояние перед новым стартовым устройством."""
                self.result = []
                self.passed_devices = set()

            def find_vlan(self, **kwargs) -> None:
                """Имитирует обход компоненты dev-a -> dev-b."""
                self.calls.append(kwargs["device"])
                self.passed_devices.update({"dev-a", "dev-b"})

        return FakeFinder()


class TracerouteMapDataTestCase(SimpleTestCase):
    def test_build_map_data_uses_only_nodes_with_coordinates(self) -> None:
        """Географическая трассировка отбрасывает узлы без координат Zabbix."""
        graph_data = {
            "nodes": [
                {"id": "dev-a", "label": "dev-a"},
                {"id": "dev-b", "label": "dev-b"},
                {"id": "dev-a-port", "label": "eth1"},
            ],
            "edges": [
                {"from": "dev-a", "to": "dev-b", "value": 2},
                {"from": "dev-a", "to": "dev-a-port", "value": 1},
            ],
            "vlansInfo": [{"vlan": 100, "count": 2}],
        }

        device_info = {
            "dev-a": {
                "name": "dev-a",
                "ip": "192.0.2.1",
                "vendor": "Huawei",
                "model": "S5320",
                "group": "Access",
                "serial_number": "SN1",
                "os_version": "VRP",
                "url": "/device/dev-a",
            }
        }

        with (
            patch(
                "apps.net_tools.services.traceroute.get_devices_coordinates",
                return_value={
                    "dev-a": DeviceCoords(lat=44.1, lon=33.2),
                    "dev-b": DeviceCoords(lat=44.2, lon=33.3),
                },
            ),
            patch("apps.net_tools.services.traceroute._get_traceroute_map_devices", return_value=device_info),
        ):
            result = build_traceroute_map_data(graph_data)

        self.assertEqual([node["id"] for node in result["nodes"]], ["dev-a", "dev-b", "dev-a-port"])
        self.assertEqual(result["nodes"][0]["device"], device_info["dev-a"])
        self.assertIsNone(result["nodes"][1]["device"])
        self.assertEqual(result["nodes"][2]["inherited_from"], "dev-a")
        self.assertEqual(result["nodes"][2]["kind"], "inherited")
        self.assertEqual(result["edges"], graph_data["edges"])
        self.assertEqual(result["skipped_nodes"], [])
        self.assertEqual(result["vlansInfo"], graph_data["vlansInfo"])


class VlanNetworkTestCase(SimpleTestCase):
    def test_create_network_deduplicates_undirected_edges(self) -> None:
        """VLAN graph keeps undirected edge deduplication."""
        data = [
            TracerouteResult(
                node="dev-a",
                next_node="dev-b",
                line_width=10,
                line_description={"from": "dev-a", "to": "dev-b"},
                admin_down_status="up",
            ),
            TracerouteResult(
                node="dev-b",
                next_node="dev-a",
                line_width=5,
                line_description={"from": "dev-b", "to": "dev-a"},
                admin_down_status="up",
            ),
        ]
        network = VlanNetwork()

        with patch.object(VlanNetwork, "_get_kinds_and_rules", return_value=({}, [])):
            network.create_network(data)

        visible_nodes = [node for node in network.nodes if not node.get("hidden")]
        self.assertEqual(len(visible_nodes), 2)
        self.assertEqual(len(network.edges), 1)
        self.assertEqual({node["id"]: node["value"] for node in visible_nodes}, {"dev-a": 3, "dev-b": 3})

    def test_create_network_prefers_more_specific_duplicate_edge(self) -> None:
        """VLAN graph keeps the most specific edge when duplicate device links exist."""
        data = [
            TracerouteResult(
                node="dev-a",
                next_node="dev-b",
                line_width=10,
                line_description={
                    "kind": "link",
                    "vlan_match": {"confidence": "low"},
                },
                admin_down_status="up",
            ),
            TracerouteResult(
                node="dev-a",
                next_node="dev-b",
                line_width=10,
                line_description={
                    "kind": "link",
                    "vlan_match": {"confidence": "high"},
                },
                admin_down_status="up",
            ),
        ]
        network = VlanNetwork()

        with patch.object(VlanNetwork, "_get_kinds_and_rules", return_value=({}, [])):
            network.create_network(data)

        self.assertEqual(len(network.edges), 1)
        self.assertEqual(network.edges[0]["title"]["vlan_match"]["confidence"], "high")
        self.assertNotIn("dashes", network.edges[0])

    def test_create_network_prefers_exact_duplicate_edge(self) -> None:
        """VLAN graph keeps exact edges over other confident duplicate edges."""
        data = [
            TracerouteResult(
                node="dev-a",
                next_node="dev-b",
                line_width=10,
                line_description={
                    "kind": "link",
                    "vlan_match": {"confidence": "high"},
                },
                admin_down_status="up",
            ),
            TracerouteResult(
                node="dev-a",
                next_node="dev-b",
                line_width=10,
                line_description={
                    "kind": "link",
                    "vlan_match": {"confidence": "exact"},
                },
                admin_down_status="up",
            ),
        ]
        network = VlanNetwork()

        with patch.object(VlanNetwork, "_get_kinds_and_rules", return_value=({}, [])):
            network.create_network(data)

        self.assertEqual(len(network.edges), 1)
        self.assertEqual(network.edges[0]["title"]["vlan_match"]["confidence"], "exact")
        self.assertEqual(network.edges[0]["color"]["color"], "#22c55e")

    def test_create_network_marks_nodes_with_only_suspicious_edges(self) -> None:
        """VLAN graph marks nodes whose every edge is suspicious."""
        data = [
            TracerouteResult(
                node="dev-a",
                next_node="dev-b",
                line_width=10,
                line_description={
                    "kind": "link",
                    "vlan_match": {"confidence": "low"},
                },
                admin_down_status="up",
            ),
            TracerouteResult(
                node="dev-b",
                next_node="dev-c",
                line_width=10,
                line_description={
                    "kind": "link",
                    "vlan_match": {"confidence": "high"},
                },
                admin_down_status="up",
            ),
        ]
        network = VlanNetwork()

        with patch.object(VlanNetwork, "_get_kinds_and_rules", return_value=({}, [])):
            network.create_network(data)

        nodes = {node["id"]: node for node in network.nodes if not node.get("hidden")}
        self.assertTrue(nodes["dev-a"]["suspicious"])
        self.assertNotIn("suspicious", nodes["dev-b"])
        self.assertNotIn("suspicious", nodes["dev-c"])
