from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from requests import RequestException

from apps.check.models import AuthGroup, DeviceGroup, Devices
from apps.net_tools.services.arp_find import MacIpFindResult
from devicemanager.vendors.base.types import ArpInfoResult


class IpMacInfoViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Создает пользователя и оборудование для проверки WTF API."""
        cls.user = User.objects.create_superuser(username="wtf_admin", password="password")
        cls.group = DeviceGroup.objects.create(name="WTF")
        cls.auth_group = AuthGroup.objects.create(name="test", login="test", password="test")
        cls.search_device = Devices.objects.create(
            name="search-device",
            ip="192.0.2.1",
            group=cls.group,
            auth_group=cls.auth_group,
        )
        cls.target_device = Devices.objects.create(
            name="target-device",
            ip="192.0.2.10",
            group=cls.group,
            auth_group=cls.auth_group,
            vendor="Huawei",
            model="S5320",
        )

    def setUp(self):
        """Авторизует тестового пользователя."""
        self.client.force_login(self.user)

    @patch("apps.net_tools.api.views.zabbix_api.connect", side_effect=RequestException)
    @patch("apps.net_tools.api.views.find_mac_or_ip")
    def test_ip_mac_info_returns_ecstasy_device_for_arp_result_ip(self, find_mac_or_ip_mock, _zabbix_mock):
        """API возвращает оборудование Ecstasy по IP из ARP-результатов."""
        find_mac_or_ip_mock.return_value = [
            MacIpFindResult(
                device=self.search_device,
                results=[
                    ArpInfoResult(
                        ip=self.target_device.ip,
                        mac="0011.2233.4455",
                        vlan="10",
                        device_name="client",
                        port="eth1",
                    )
                ],
            )
        ]

        response = self.client.get("/api/v1/tools/ip-mac-info/001122334455")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["ecstasy_devices"],
            [
                {
                    "id": self.target_device.id,
                    "name": self.target_device.name,
                    "ip": self.target_device.ip,
                    "url": self.target_device.get_absolute_url(),
                    "group": self.group.name,
                    "vendor": self.target_device.vendor,
                    "model": self.target_device.model,
                    "active": True,
                }
            ],
        )

    @patch("apps.net_tools.api.views.find_mac_or_ip", return_value=[])
    def test_ip_mac_info_returns_ecstasy_device_for_requested_ip(self, _find_mac_or_ip_mock):
        """API возвращает оборудование Ecstasy по введенному IP даже без ARP-совпадений."""
        response = self.client.get(f"/api/v1/tools/ip-mac-info/{self.target_device.ip}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["ecstasy_devices"][0]["name"], self.target_device.name)
