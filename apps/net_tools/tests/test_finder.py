from typing import Any, cast

from django.test import SimpleTestCase

from apps.net_tools.services.finder import MultipleTraceroute, Traceroute, TracerouteResult
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
    def _make_finder(self) -> Traceroute:
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
