from unittest.mock import patch

from django.test import SimpleTestCase

from apps.net_tools.services.arp_find import find_mac_or_ip
from devicemanager.vendors.base.types import ArpInfoResult


class FakeDevicesForMacSearchManager:
    """Минимальный manager для проверки find_mac_or_ip без базы данных."""

    def __init__(self, records):
        self.records = records

    def select_related(self, *fields):
        """Возвращает записи для поиска."""
        return self.records


class FakeDevicesForMacSearch:
    """Запись DevicesForMacSearch с нужным полем device."""

    def __init__(self, device):
        self.device = device


class FakeDevice:
    """Тестовое устройство с fake-сессией."""

    name = "search-device"
    ip = "192.0.2.1"

    def __init__(self):
        self.session = FakeSession()

    def connect(self):
        """Возвращает fake-сессию."""
        return self.session


class FakeSession:
    """Fake-сессия для проверки типа и значения поиска."""

    def __init__(self):
        self.calls = []

    def search_ip(self, ip_address):
        """Запоминает IP-поиск."""
        self.calls.append(("ip", ip_address))
        return [ArpInfoResult(ip=ip_address, mac="0011.2233.4455", vlan="10")]

    def search_mac(self, mac_address):
        """Запоминает MAC-поиск."""
        self.calls.append(("mac", mac_address))
        return [ArpInfoResult(ip="192.0.2.10", mac=mac_address, vlan="20")]


class FindMacOrIpTestCase(SimpleTestCase):
    def test_find_mac_or_ip_normalizes_ipv4_address(self):
        """IPv4 передается в search_ip в нормализованном виде."""
        device = FakeDevice()

        with patch(
            "apps.net_tools.services.arp_find.DevicesForMacSearch.objects",
            FakeDevicesForMacSearchManager([FakeDevicesForMacSearch(device)]),
        ):
            result = find_mac_or_ip(" 192.0.2.10 ")

        self.assertEqual(device.session.calls, [("ip", "192.0.2.10")])
        self.assertEqual(result[0].results[0].ip, "192.0.2.10")

    def test_find_mac_or_ip_normalizes_mac_address(self):
        """MAC передается в search_mac только hex-символами в нижнем регистре."""
        device = FakeDevice()

        with patch(
            "apps.net_tools.services.arp_find.DevicesForMacSearch.objects",
            FakeDevicesForMacSearchManager([FakeDevicesForMacSearch(device)]),
        ):
            result = find_mac_or_ip("00:11-22.33:44:55")

        self.assertEqual(device.session.calls, [("mac", "001122334455")])
        self.assertEqual(result[0].results[0].mac, "001122334455")

    def test_find_mac_or_ip_rejects_invalid_ipv4_address(self):
        """Невалидный IPv4 не запускает поиск как MAC."""
        device = FakeDevice()

        with patch(
            "apps.net_tools.services.arp_find.DevicesForMacSearch.objects",
            FakeDevicesForMacSearchManager([FakeDevicesForMacSearch(device)]),
        ):
            result = find_mac_or_ip("999.0.2.10")

        self.assertEqual(device.session.calls, [])
        self.assertEqual(result, [])
