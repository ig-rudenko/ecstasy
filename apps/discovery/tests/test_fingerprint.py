import subprocess
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from apps.check.models import AuthGroup
from apps.discovery.models import DiscoveryAttempt
from apps.discovery.services.fingerprint import CliFingerprinter, SnmpFingerprinter


class SnmpFingerprinterTests(SimpleTestCase):
    """Тесты SNMP fingerprint без реальной сети."""

    @patch("apps.discovery.services.fingerprint.snmp.get_system_identity")
    def test_snmp_timeout_returns_failed_attempt(self, mock_get_identity):
        """SNMP timeout не прерывает discovery scan целиком."""

        mock_get_identity.side_effect = subprocess.TimeoutExpired(cmd="snmpwalk", timeout=2)

        fingerprint, attempts = SnmpFingerprinter(["public"], timeout=1).collect("192.0.2.10")

        self.assertFalse(fingerprint.has_identity())
        self.assertEqual(fingerprint.detected_protocols, {"snmp": False})
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0].method, DiscoveryAttempt.Method.SNMP)
        self.assertEqual(attempts[0].status, DiscoveryAttempt.Status.FAILED)


class CliFingerprinterTests(TestCase):
    """Тесты CLI fingerprint без реального подключения к оборудованию."""

    def test_collect_prefers_ssh_regardless_of_profile_protocol_order(self):
        """SSH проверяется раньше Telnet независимо от порядка в профиле."""

        auth_group = AuthGroup.objects.create(name="default", login="user", password="password")

        with patch("apps.discovery.services.fingerprint.DeviceRemoteConnector") as mock_connector:
            mock_connector.return_value = _FakeConnector({"vendor": "Eltex", "model": "MES"})

            fingerprint, attempts = CliFingerprinter(["telnet", "ssh"], [auth_group]).collect("192.0.2.12")

        self.assertEqual(fingerprint.raw["cliProtocol"], "ssh")
        self.assertEqual(attempts[0].method, DiscoveryAttempt.Method.SSH)
        self.assertEqual(mock_connector.call_args.kwargs["protocol"], "ssh")

    def test_collect_falls_back_to_telnet_when_ssh_connection_fails(self):
        """После неудачного SSH выполняется попытка подключения по Telnet."""

        auth_group = AuthGroup.objects.create(name="default", login="user", password="password")

        with patch("apps.discovery.services.fingerprint.DeviceRemoteConnector") as mock_connector:
            mock_connector.side_effect = [
                Exception("SSH unavailable"),
                _FakeConnector({"vendor": "Eltex", "model": "MES"}),
            ]

            fingerprint, attempts = CliFingerprinter(["telnet", "ssh"], [auth_group]).collect("192.0.2.13")

        self.assertEqual(fingerprint.raw["cliProtocol"], "telnet")
        self.assertEqual(
            [attempt.method for attempt in attempts],
            [
                DiscoveryAttempt.Method.SSH,
                DiscoveryAttempt.Method.TELNET,
            ],
        )
        self.assertEqual(attempts[-1].status, DiscoveryAttempt.Status.SUCCESS)

    def test_collect_uses_first_auth_group_that_connects(self):
        """CLI fingerprint перебирает AuthGroup до первого успешного подключения."""

        wrong_auth = AuthGroup.objects.create(name="wrong", login="bad", password="bad")
        valid_auth = AuthGroup.objects.create(name="valid", login="good", password="good")

        with patch("apps.discovery.services.fingerprint.DeviceRemoteConnector") as mock_connector:
            mock_connector.side_effect = [
                Exception("логин неверный"),
                _FakeConnector({"vendor": "Eltex", "model": "MES", "serialno": "SN1"}),
            ]

            fingerprint, attempts = CliFingerprinter(["ssh"], [wrong_auth, valid_auth]).collect("192.0.2.10")

        self.assertEqual(fingerprint.selected_auth_group, valid_auth)
        self.assertEqual(fingerprint.raw["cliProtocol"], "ssh")
        self.assertEqual(attempts[0].status, DiscoveryAttempt.Status.AUTH_FAILED)
        self.assertEqual(attempts[1].status, DiscoveryAttempt.Status.SUCCESS)

    def test_collect_marks_auth_check_failed_when_no_auth_group_connects(self):
        """CLI fingerprint помечает кандидата, если все AuthGroup из профиля не подошли."""

        wrong_auth = AuthGroup.objects.create(name="wrong", login="bad", password="bad")

        with patch("apps.discovery.services.fingerprint.DeviceRemoteConnector") as mock_connector:
            mock_connector.side_effect = [Exception("логин неверный")]

            fingerprint, attempts = CliFingerprinter(["ssh"], [wrong_auth]).collect("192.0.2.11")

        self.assertIsNone(fingerprint.selected_auth_group)
        self.assertEqual(fingerprint.raw["authCheck"]["status"], "FAILED")
        self.assertIn(wrong_auth.id, fingerprint.raw["authCheck"]["attemptedAuthGroupIds"])
        self.assertTrue(fingerprint.last_error)
        self.assertEqual(attempts[0].status, DiscoveryAttempt.Status.AUTH_FAILED)


class _FakeConnector:
    """Минимальный context manager для имитации DeviceRemoteConnector."""

    def __init__(self, system_info: dict[str, str]) -> None:
        """Сохранить ответ system info."""

        self.system_info = system_info

    def __enter__(self):
        """Вернуть объект с get_system_info."""

        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        """Закрыть fake session."""

    def get_system_info(self) -> dict[str, str]:
        """Вернуть подготовленный system info."""

        return self.system_info
