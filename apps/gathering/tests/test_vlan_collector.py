from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.check.models import AuthGroup, DeviceGroup, Devices, User
from apps.gathering.models import MacAddress, Vlan, VlanPort
from apps.gathering.services.vlan.collector import VlanTableGather
from devicemanager.vendors.dlink import Dlink


class VlanTableGatherTests(TestCase):
    """Tests for storing collected VLAN table data."""

    def setUp(self) -> None:
        """Create a device used by VLAN collector tests."""
        group = DeviceGroup.objects.create(name="ASW")
        auth_group = AuthGroup.objects.create(name="auth", login="login", password="password")
        self.device = Devices.objects.create(
            ip="192.0.2.10",
            name="sw1",
            group=group,
            auth_group=auth_group,
        )

    def test_save_vlan_info_stores_port_rows_and_removes_stale_rows(self):
        """Store every VLAN port separately and delete stale ports/VLANs."""
        old_vlan = Vlan.objects.create(device=self.device, vlan=30, desc="old")
        vlan = Vlan.objects.create(device=self.device, vlan=10, desc="old")
        VlanPort.objects.create(vlan=vlan, port="3", desc="stale")
        VlanPort.objects.create(vlan=old_vlan, port="1", desc="stale")

        gather = VlanTableGather.__new__(VlanTableGather)  # noqa
        gather.device = self.device
        gather.table = [(10, ["1", "2", "3"], "users")]
        gather.interfaces_desc = {
            "1": "abon 1",
            "2": "abon 2",
            "3": "",
        }
        gather.normalize_interface = lambda port: port

        self.assertEqual(gather._save_vlan_info(gather.table), 3)

        vlan.refresh_from_db()
        self.assertEqual(vlan.desc, "users")
        self.assertFalse(Vlan.objects.filter(device=self.device, vlan=30).exists())
        self.assertQuerySetEqual(
            VlanPort.objects.filter(vlan=vlan).order_by("port").values_list("port", "desc"),
            [
                ("1", "abon 1"),
                ("2", "abon 2"),
                ("3", ""),
            ],
        )


class DlinkVlanParserTests(TestCase):
    """Tests for D-Link VLAN table parsing."""

    def test_get_vlan_table_expands_ranges_and_strips_port_suffixes(self):
        """Parse D-Link show vlan output into collector table entries."""
        device = Dlink.__new__(Dlink)  # noqa
        device.lock = False
        device.send_command = lambda *args, **kwargs: ("""
command: show vlan


VID             : 1           VLAN Name       : default
VLAN Type       : Static      Advertisement   : Disabled
Member Ports    :                     
Static Ports    :                     
Current Tagged Ports   :                     
Current Untagged Ports :                     
Static Tagged Ports    :                     
Static Untagged Ports  :                     
Forbidden Ports        :                     

VID             : 10          VLAN Name       : users vlan
VLAN Type       : Static      Advertisement   : Disabled
Member Ports    : 1-3,26(C), 28(F)

VID             : 20          VLAN Name       : uplink
VLAN Type       : Static      Advertisement   : Disabled
Member Ports    :
""")

        self.assertEqual(
            device.get_vlan_table(),
            [
                (10, ["1", "2", "3", "26", "28"], "users vlan"),
                (20, [], "uplink"),
            ],
        )


class VlanAPITests(APITestCase):
    """Tests for collected VLAN API endpoints."""

    def setUp(self) -> None:
        """Create VLAN rows for an allowed and forbidden device."""
        self.user = User.objects.create_user(username="user", password="password")
        self.allowed_group = DeviceGroup.objects.create(name="allowed")
        self.forbidden_group = DeviceGroup.objects.create(name="forbidden")
        self.auth_group = AuthGroup.objects.create(name="auth", login="login", password="password")
        self.user.profile.devices_groups.add(self.allowed_group)

        self.device = Devices.objects.create(
            ip="192.0.2.20",
            name="sw-allowed",
            group=self.allowed_group,
            auth_group=self.auth_group,
        )
        forbidden_device = Devices.objects.create(
            ip="192.0.2.30",
            name="sw-forbidden",
            group=self.forbidden_group,
            auth_group=self.auth_group,
        )
        self.vlan = Vlan.objects.create(device=self.device, vlan=10, desc="users")
        VlanPort.objects.create(vlan=self.vlan, port="1", desc="abon 1")
        VlanPort.objects.create(vlan=self.vlan, port="2", desc="")
        self.mac_address = MacAddress.objects.create(
            device=self.device,
            address="001122334455",
            vlan=10,
            type="D",
            port="1",
            desc="abon 1",
        )

        forbidden_vlan = Vlan.objects.create(device=forbidden_device, vlan=20, desc="hidden")
        VlanPort.objects.create(vlan=forbidden_vlan, port="1", desc="hidden")
        self.forbidden_mac_address = MacAddress.objects.create(
            device=forbidden_device,
            address="aabbccddeeff",
            vlan=20,
            type="D",
            port="1",
            desc="hidden",
        )

    def test_mac_address_list_returns_only_allowed_devices(self):
        """Return MAC address rows only for devices available to the current user."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("gathering-api:mac-address-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["address"], "001122334455")
        self.assertEqual(response.data["results"][0]["device_name"], "sw-allowed")

    def test_mac_address_list_filters_by_port(self):
        """Filter MAC address rows by port."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("gathering-api:mac-address-list"), {"port": "1"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["port"], "1")
        self.assertEqual(response.data["results"][0]["vlan"], 10)

    def test_mac_address_list_filters_by_full_normalized_address(self):
        """Filter MAC address rows by full MAC address with separators."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse("gathering-api:mac-address-list"), {"address": "00:11:22:33:44:55"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["address"], "001122334455")

    def test_mac_address_list_filters_by_partial_normalized_address(self):
        """Filter MAC address rows by partial normalized MAC address."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("gathering-api:mac-address-list"), {"address": "11-22-33"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["address"], "001122334455")

    def test_mac_address_detail_denies_forbidden_device(self):
        """Do not expose MAC address rows from unavailable device groups."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse("gathering-api:mac-address-detail", args=[self.forbidden_mac_address.id])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_mac_address_api_is_read_only(self):
        """Do not allow creating MAC address rows through the API."""
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("gathering-api:mac-address-list"),
            {
                "device_id": self.device.id,
                "address": "ffffffffffff",
                "vlan": 10,
                "type": "D",
                "port": "1",
                "desc": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_vlan_list_returns_only_allowed_devices(self):
        """Return VLANs only for devices available to the current user."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("gathering-api:vlan-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["vlan"], 10)
        self.assertEqual(response.data["results"][0]["device_name"], "sw-allowed")
        self.assertEqual([port["port"] for port in response.data["results"][0]["ports"]], ["1", "2"])

    def test_vlan_port_list_filters_by_port(self):
        """Filter VLAN port rows by exact port."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("gathering-api:vlan-port-list"), {"port": "2"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["port"], "2")
        self.assertEqual(response.data["results"][0]["vlan"], 10)

    def test_vlan_detail_denies_forbidden_device(self):
        """Do not expose VLAN rows from unavailable device groups."""
        forbidden_vlan = Vlan.objects.get(vlan=20)
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("gathering-api:vlan-detail", args=[forbidden_vlan.id]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
