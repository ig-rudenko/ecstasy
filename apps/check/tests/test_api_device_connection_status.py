from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from ..models import AuthGroup, DeviceGroup, Devices, User


class DeviceConnectionStatusAPIViewTests(APITestCase):
    """Tests for device connector status and SSH host key confirmation."""

    def setUp(self) -> None:
        """Create a device and users with access to its group."""

        self.group = DeviceGroup.objects.create(name="ASW")
        self.auth_group = AuthGroup.objects.create(name="test", login="test", password="test")
        self.device = Devices.objects.create(
            ip="192.0.2.10",
            name="dev1",
            group=self.group,
            auth_group=self.auth_group,
            cmd_protocol="ssh",
            port_scan_protocol="snmp",
        )
        self.user = User.objects.create_user(username="user", password="password")
        self.staff_user = User.objects.create_user(
            username="staff",
            password="password",
            is_staff=True,
        )
        self.user.profile.devices_groups.add(self.group)
        self.staff_user.profile.devices_groups.add(self.group)
        self.pool_url = f"/api/v1/devices/{self.device.name}/pool"
        self.confirm_url = f"/api/v1/devices/{self.device.name}/ssh-host-key"

    @patch("apps.check.api.views.device_manager.pool_controller.get_connection_status")
    def test_pool_status_includes_connector_error_and_ssh_host_key_change(self, get_connection_status):
        """GET returns connector diagnostics together with pool statuses."""

        get_connection_status.return_value = {
            "statuses": [True, False],
            "connections": [
                {"active": True, "protocol": "ssh"},
                {"active": False, "protocol": "telnet"},
            ],
            "error": {
                "type": "SSHConnectionError",
                "message": "SSH HOST IDENTIFICATION HAS CHANGED",
                "occurredAt": "2026-06-10T12:00:00+00:00",
            },
            "sshHostKeyChange": {
                "detectedAt": "2026-06-10T12:00:00+00:00",
                "port": 22,
                "previousKeys": [{"type": "ssh-ed25519", "fingerprint": "SHA256:old"}],
                "newKeys": [{"type": "ssh-ed25519", "fingerprint": "SHA256:new"}],
            },
        }
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.pool_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["connectionPoolSize"], self.device.connection_pool_size)
        self.assertEqual(response.data["statuses"], [True, False])
        self.assertEqual(response.data["connections"][0]["protocol"], "ssh")
        self.assertEqual(response.data["portScanProtocol"], "snmp")
        self.assertEqual(response.data["commandProtocol"], "ssh")
        self.assertEqual(response.data["error"]["type"], "SSHConnectionError")
        self.assertEqual(
            response.data["sshHostKeyChange"]["newKeys"][0]["fingerprint"],
            "SHA256:new",
        )
        get_connection_status.assert_called_once_with(self.device.ip)

    @patch("apps.check.api.views.device_manager.pool_controller.confirm_ssh_host_key")
    def test_non_staff_user_cannot_confirm_ssh_host_key(self, confirm_ssh_host_key):
        """Only staff users can accept a changed SSH host key."""

        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.confirm_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        confirm_ssh_host_key.assert_not_called()

    @patch("apps.check.api.views.device_manager.pool_controller.confirm_ssh_host_key")
    def test_staff_user_can_confirm_ssh_host_key(self, confirm_ssh_host_key):
        """Staff confirmation updates known_hosts and resets the current pool."""

        confirm_ssh_host_key.return_value = status.HTTP_204_NO_CONTENT
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(self.confirm_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        confirm_ssh_host_key.assert_called_once_with(self.device.ip)

    @patch("apps.check.api.views.device_manager.pool_controller.confirm_ssh_host_key")
    def test_connector_failure_during_confirmation_returns_bad_gateway(self, confirm_ssh_host_key):
        """A known_hosts write failure is not reported as a missing pending key."""

        confirm_ssh_host_key.return_value = status.HTTP_500_INTERNAL_SERVER_ERROR
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(self.confirm_url)

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
