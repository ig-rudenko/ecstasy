from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from devicemanager.device_connector.connection_status import (
    ConnectionStatusStore,
    PendingSSHHostKeyChange,
    SSHKeyInfo,
    SSHKnownHostsStore,
)
from devicemanager.exceptions import SSHConnectionError, TelnetConnectionError


class ConnectionStatusStoreTests(SimpleTestCase):
    """Tests for connection diagnostics stored by device-connector."""

    def setUp(self):
        """Create a store with deterministic time and host key operations."""

        self.host_key_store = Mock()
        self.now = datetime(2026, 6, 10, 12, 0, tzinfo=UTC)
        self.store = ConnectionStatusStore(
            host_key_store=self.host_key_store,
            now=lambda: self.now,
        )

    def test_records_latest_connection_error(self):
        """A regular connection error is exposed without an SSH key change."""

        self.store.record_error(
            "192.0.2.10",
            TelnetConnectionError("Telnet недоступен", ip="192.0.2.10"),
            ssh_port=22,
        )

        status = self.store.get_status("192.0.2.10")

        self.assertEqual(status["error"]["type"], "TelnetConnectionError")
        self.assertEqual(status["error"]["message"], "Telnet недоступен")
        self.assertEqual(status["error"]["occurredAt"], self.now.isoformat())
        self.assertIsNone(status["sshHostKeyChange"])
        self.host_key_store.inspect.assert_not_called()

    def test_records_pending_ssh_host_key_change(self):
        """A changed host key stores old and newly scanned fingerprints."""

        pending_change = PendingSSHHostKeyChange(
            ip="192.0.2.10",
            port=2222,
            detected_at=self.now,
            previous_keys=(SSHKeyInfo(type="ssh-ed25519", fingerprint="SHA256:old"),),
            new_keys=(SSHKeyInfo(type="ssh-ed25519", fingerprint="SHA256:new"),),
            new_key_lines=("[192.0.2.10]:2222 ssh-ed25519 AAAAnew",),
        )
        self.host_key_store.inspect.return_value = pending_change

        self.store.record_error(
            "192.0.2.10",
            SSHConnectionError("SSH HOST IDENTIFICATION HAS CHANGED", ip="192.0.2.10"),
            ssh_port=2222,
        )

        status = self.store.get_status("192.0.2.10")
        self.assertEqual(
            status["sshHostKeyChange"]["previousKeys"],
            [{"type": "ssh-ed25519", "fingerprint": "SHA256:old"}],
        )
        self.assertEqual(
            status["sshHostKeyChange"]["newKeys"],
            [{"type": "ssh-ed25519", "fingerprint": "SHA256:new"}],
        )
        self.host_key_store.inspect.assert_called_once_with("192.0.2.10", 2222, self.now)

    def test_confirmation_applies_pending_key_and_clears_status(self):
        """Confirmation uses the recorded key material and removes diagnostics."""

        pending_change = PendingSSHHostKeyChange(
            ip="192.0.2.10",
            port=22,
            detected_at=self.now,
            previous_keys=(),
            new_keys=(SSHKeyInfo(type="ssh-ed25519", fingerprint="SHA256:new"),),
            new_key_lines=("192.0.2.10 ssh-ed25519 AAAAnew",),
        )
        self.host_key_store.inspect.return_value = pending_change
        self.store.record_error(
            "192.0.2.10",
            SSHConnectionError("SSH HOST IDENTIFICATION HAS CHANGED", ip="192.0.2.10"),
            ssh_port=22,
        )

        confirmed = self.store.confirm_ssh_host_key("192.0.2.10")

        self.assertTrue(confirmed)
        self.host_key_store.confirm.assert_called_once_with(pending_change)
        self.assertEqual(
            self.store.get_status("192.0.2.10"),
            {"error": None, "sshHostKeyChange": None},
        )


class SSHKnownHostsStoreTests(SimpleTestCase):
    """Tests for safe known_hosts replacement."""

    @staticmethod
    def make_change() -> PendingSSHHostKeyChange:
        """Return a pending host key change for known_hosts tests."""

        return PendingSSHHostKeyChange(
            ip="192.0.2.10",
            port=2222,
            detected_at=datetime(2026, 6, 10, 12, 0, tzinfo=UTC),
            previous_keys=(),
            new_keys=(SSHKeyInfo(type="ssh-ed25519", fingerprint="SHA256:new"),),
            new_key_lines=("[192.0.2.10]:2222 ssh-ed25519 AAAAnew",),
        )

    @patch("devicemanager.device_connector.connection_status.subprocess.run")
    def test_confirmation_appends_only_previously_scanned_key_lines(self, run):
        """Confirmation writes the exact pending key material without a rescan."""

        run.return_value = Mock(returncode=0, stderr="")
        with TemporaryDirectory() as temporary_directory:
            known_hosts_path = Path(temporary_directory) / ".ssh" / "known_hosts"
            store = SSHKnownHostsStore(known_hosts_path)

            store.confirm(self.make_change())

            self.assertEqual(
                known_hosts_path.read_text(encoding="utf-8"),
                "[192.0.2.10]:2222 ssh-ed25519 AAAAnew\n",
            )
            command = run.call_args.args[0]
            self.assertEqual(command[:3], ["ssh-keygen", "-R", "[192.0.2.10]:2222"])
            self.assertEqual(command[3], "-f")
            self.assertEqual(Path(command[4]).parent, known_hosts_path.parent)

    @patch("devicemanager.device_connector.connection_status.subprocess.run")
    def test_accept_current_scans_and_writes_key_in_one_operation(self, run):
        """Automatic acceptance writes the key scanned inside the locked operation."""

        command_results = iter(
            [
                Mock(
                    returncode=0,
                    stdout="192.0.2.10 ssh-ed25519 AAAAold\n",
                    stderr="",
                ),
                Mock(
                    returncode=0,
                    stdout="192.0.2.10 ssh-ed25519 AAAAnew\n",
                    stderr="",
                ),
                Mock(returncode=0, stdout="256 SHA256:old host (ED25519)\n", stderr=""),
                Mock(returncode=0, stdout="256 SHA256:new host (ED25519)\n", stderr=""),
            ]
        )

        def run_command(command, **kwargs):
            """Emulate ssh-keygen removal while returning prepared command output."""

            if command[:2] == ["ssh-keygen", "-R"]:
                Path(command[4]).write_text("", encoding="utf-8")
                return Mock(returncode=0, stdout="", stderr="")
            return next(command_results)

        run.side_effect = run_command
        with TemporaryDirectory() as temporary_directory:
            known_hosts_path = Path(temporary_directory) / ".ssh" / "known_hosts"
            known_hosts_path.parent.mkdir()
            known_hosts_path.write_text("192.0.2.10 ssh-ed25519 AAAAold\n", encoding="utf-8")
            store = SSHKnownHostsStore(known_hosts_path)

            change = store.accept_current("192.0.2.10", 22, self.make_change().detected_at)

            self.assertEqual(change.new_keys[0].fingerprint, "SHA256:new")
            self.assertEqual(
                known_hosts_path.read_text(encoding="utf-8"),
                "192.0.2.10 ssh-ed25519 AAAAnew\n",
            )

    @patch("devicemanager.device_connector.connection_status.subprocess.run")
    def test_failed_confirmation_keeps_original_known_hosts(self, run):
        """A failed replacement never removes the currently trusted key."""

        run.return_value = Mock(returncode=2, stderr="update failed")
        with TemporaryDirectory() as temporary_directory:
            known_hosts_path = Path(temporary_directory) / ".ssh" / "known_hosts"
            known_hosts_path.parent.mkdir()
            known_hosts_path.write_text("192.0.2.10 ssh-ed25519 AAAAold\n", encoding="utf-8")
            store = SSHKnownHostsStore(known_hosts_path)

            with self.assertRaises(RuntimeError):
                store.confirm(self.make_change())

            self.assertEqual(
                known_hosts_path.read_text(encoding="utf-8"),
                "192.0.2.10 ssh-ed25519 AAAAold\n",
            )
