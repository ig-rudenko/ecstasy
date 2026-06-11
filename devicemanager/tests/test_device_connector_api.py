from unittest.mock import patch

from django.test import SimpleTestCase

import device_connector
from devicemanager.exceptions import SSHConnectionError


class DeviceConnectorAPITests(SimpleTestCase):
    """Tests for device-connector diagnostics endpoints."""

    def setUp(self):
        """Create a Flask test client authenticated with the service token."""

        self.client = device_connector.app.test_client()
        self.headers = {"Token": device_connector.TOKEN}

    @patch("device_connector.CONNECTION_STATUSES.record_error")
    @patch("device_connector.DeviceSessionFactory.perform_method")
    def test_connector_records_failed_device_request(self, perform_method, record_error):
        """A failed device request is added to connection diagnostics."""

        error = SSHConnectionError("SSH недоступен", ip="192.0.2.10")
        perform_method.side_effect = error

        response = self.client.post(
            "/connector/192.0.2.10/get_system_info",
            headers=self.headers,
            json={
                "connection": {
                    "cmd_protocol": "ssh",
                    "port_scan_protocol": "ssh",
                    "snmp_community": "public",
                    "pool_size": 1,
                    "make_session_global": True,
                    "ssh_port": 2222,
                },
                "auth": {"login": "user", "password": "password", "secret": ""},
                "params": {},
            },
        )

        self.assertEqual(response.status_code, 500)
        record_error.assert_called_once_with("192.0.2.10", error, ssh_port=2222)

    @patch("device_connector.CONNECTION_STATUSES.get_status")
    @patch("device_connector.DEVICE_SESSIONS.get_pool_status")
    def test_pool_endpoint_returns_connection_diagnostics(self, get_pool_status, get_status):
        """Pool status includes the latest error and SSH key change."""

        get_pool_status.return_value = [True]
        get_status.return_value = {
            "error": {"type": "SSHConnectionError", "message": "error", "occurredAt": "now"},
            "sshHostKeyChange": {"port": 22},
        }

        response = self.client.get("/pool/192.0.2.10", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["statuses"], [True])
        self.assertEqual(response.json["error"]["type"], "SSHConnectionError")
        self.assertEqual(response.json["sshHostKeyChange"]["port"], 22)

    @patch("device_connector.CONNECTION_STATUSES.confirm_ssh_host_key")
    def test_ssh_host_key_confirmation_requires_service_token(self, confirm_ssh_host_key):
        """The internal confirmation endpoint rejects unauthenticated requests."""

        response = self.client.post("/ssh-host-key/192.0.2.10")

        self.assertEqual(response.status_code, 401)
        confirm_ssh_host_key.assert_not_called()
