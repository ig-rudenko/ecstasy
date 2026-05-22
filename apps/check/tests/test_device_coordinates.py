from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from apps.check.models import AuthGroup, DeviceGroup, Devices
from apps.check.services.device_coordinates import (
    get_devices_coordinates,
    sync_device_coordinates_with_zabbix,
)
from apps.check.services.zabbix import DeviceCoords, ZabbixHostCoordinates


class DeviceCoordinatesServiceTestCase(TestCase):
    def setUp(self) -> None:
        self.group = DeviceGroup.objects.create(name="coords")
        self.auth_group = AuthGroup.objects.create(name="coords", login="login", password="password")

    def create_device(
        self,
        name: str,
        ip: str,
        latitude: Decimal | None = None,
        longitude: Decimal | None = None,
    ) -> Devices:
        """Create a device for coordinate service tests."""
        return Devices.objects.create(
            name=name,
            ip=ip,
            group=self.group,
            auth_group=self.auth_group,
            latitude=latitude,
            longitude=longitude,
        )

    @patch("apps.check.services.device_coordinates.get_zabbix_hosts_coordinates")
    def test_get_devices_coordinates_prefers_database_and_falls_back_to_zabbix(self, zabbix_coords) -> None:
        """Coordinates are read from DB first, then from Zabbix for missing devices."""
        self.create_device("db-device", "192.0.2.10", Decimal("44.1"), Decimal("33.2"))
        self.create_device("zabbix-device", "192.0.2.11")
        zabbix_coords.return_value = {
            "zabbix-device": DeviceCoords(lat=45.1, lon=34.2),
            "unknown-device": DeviceCoords(lat=46.1, lon=35.2),
        }

        result = get_devices_coordinates(["db-device", "zabbix-device", "unknown-device"])

        self.assertEqual(result["db-device"], DeviceCoords(lat=44.1, lon=33.2))
        self.assertEqual(result["zabbix-device"], DeviceCoords(lat=45.1, lon=34.2))
        self.assertEqual(result["unknown-device"], DeviceCoords(lat=46.1, lon=35.2))
        zabbix_coords.assert_called_once_with(["zabbix-device", "unknown-device"])

    @patch("apps.check.services.device_coordinates.get_zabbix_hosts_coordinates_inventory")
    def test_sync_updates_ecstasy_when_only_zabbix_has_coordinates(self, zabbix_hosts) -> None:
        """Valid Zabbix coordinates fill empty Ecstasy coordinates."""
        device = self.create_device("edge-1", "192.0.2.20")
        zabbix_hosts.return_value = {
            "edge-1": ZabbixHostCoordinates(
                hostid="101",
                host="edge-1",
                name="edge-1",
                lat="44.123456",
                lon="33.654321",
            )
        }

        summary = sync_device_coordinates_with_zabbix(device_ids=[device.id])

        device.refresh_from_db()
        self.assertEqual(device.latitude, Decimal("44.123456"))
        self.assertEqual(device.longitude, Decimal("33.654321"))
        self.assertEqual(summary["updated_ecstasy"], 1)
        self.assertEqual(summary["updated_zabbix"], 0)

    @patch("apps.check.services.device_coordinates.update_zabbix_host_coordinates")
    @patch("apps.check.services.device_coordinates.get_zabbix_hosts_coordinates_inventory")
    def test_sync_updates_zabbix_when_only_ecstasy_has_coordinates(self, zabbix_hosts, update_coords) -> None:
        """Ecstasy coordinates are pushed to Zabbix when inventory coordinates are empty."""
        device = self.create_device("edge-2", "192.0.2.21", Decimal("44.2"), Decimal("33.3"))
        zabbix_hosts.return_value = {
            "edge-2": ZabbixHostCoordinates(hostid="102", host="edge-2", name="edge-2", lat="", lon="")
        }

        summary = sync_device_coordinates_with_zabbix(device_ids=[device.id])

        update_coords.assert_called_once_with("102", Decimal("44.2"), Decimal("33.3"))
        self.assertEqual(summary["updated_ecstasy"], 0)
        self.assertEqual(summary["updated_zabbix"], 1)

    @patch("apps.check.services.device_coordinates.update_zabbix_host_coordinates")
    @patch("apps.check.services.device_coordinates.get_zabbix_hosts_coordinates_inventory")
    def test_sync_does_not_touch_conflicting_coordinates(self, zabbix_hosts, update_coords) -> None:
        """Different coordinates on both sides are treated as a conflict."""
        device = self.create_device("edge-3", "192.0.2.22", Decimal("44.2"), Decimal("33.3"))
        zabbix_hosts.return_value = {
            "edge-3": ZabbixHostCoordinates(
                hostid="103",
                host="edge-3",
                name="edge-3",
                lat="45.2",
                lon="34.3",
            )
        }

        summary = sync_device_coordinates_with_zabbix(device_ids=[device.id])

        device.refresh_from_db()
        self.assertEqual(device.latitude, Decimal("44.2"))
        self.assertEqual(device.longitude, Decimal("33.3"))
        update_coords.assert_not_called()
        self.assertEqual(summary["conflicts"], 1)

    @patch("apps.check.services.device_coordinates.update_zabbix_host_coordinates")
    @patch("apps.check.services.device_coordinates.get_zabbix_hosts_coordinates_inventory")
    def test_sync_treats_zero_zero_zabbix_coordinates_as_invalid(self, zabbix_hosts, update_coords) -> None:
        """Zabbix 0,0 coordinates are invalid and do not overwrite either side."""
        device = self.create_device("edge-4", "192.0.2.23")
        zabbix_hosts.return_value = {
            "edge-4": ZabbixHostCoordinates(hostid="104", host="edge-4", name="edge-4", lat="0", lon="0")
        }

        summary = sync_device_coordinates_with_zabbix(device_ids=[device.id])

        device.refresh_from_db()
        self.assertIsNone(device.latitude)
        self.assertIsNone(device.longitude)
        update_coords.assert_not_called()
        self.assertEqual(summary["invalid_zabbix"], 1)
