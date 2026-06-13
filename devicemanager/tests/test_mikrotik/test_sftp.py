import os
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from django.test import SimpleTestCase

from devicemanager.vendors.mikrotik import MikroTik


class TestMikroTikSFTP(SimpleTestCase):
    """Tests for downloading MikroTik backups over SFTP."""

    @patch.dict(os.environ, {"CONFIG_FOLDER_PATH": "test-configs"})
    @patch("devicemanager.vendors.mikrotik.datetime")
    @patch("devicemanager.vendors.mikrotik.paramiko.SSHClient")
    def test_get_current_configuration_downloads_and_removes_backup(
        self,
        ssh_client_class,
        datetime_mock,
    ):
        """Download the generated backup and remove its remote copy."""
        datetime_mock.now.return_value = datetime(2026, 6, 13, 14, 5)
        ssh_client = ssh_client_class.return_value.__enter__.return_value
        sftp_client = ssh_client.open_sftp.return_value.__enter__.return_value
        device = MikroTik.__new__(MikroTik)
        device.ip = "192.0.2.10"
        device.auth = {
            "login": "admin",
            "password": "secret",
            "privilege_mode_password": "",
        }
        device.send_command = MagicMock()

        result = device.get_current_configuration()

        backup_name = "backup_14:05-13.06.2026.backup"
        expected_path = Path("test-configs") / backup_name
        self.assertEqual(result, expected_path)
        device.send_command.assert_has_calls(
            [
                call("system backup save dont-encrypt=yes name=backup_14:05-13.06.2026"),
                call(f"file remove {backup_name}"),
            ]
        )
        ssh_client.load_system_host_keys.assert_called_once_with()
        ssh_client.set_missing_host_key_policy.assert_not_called()
        ssh_client.connect.assert_called_once_with(
            hostname="192.0.2.10",
            username="admin",
            password="secret",
        )
        sftp_client.get.assert_called_once_with(backup_name, str(expected_path.absolute()))
