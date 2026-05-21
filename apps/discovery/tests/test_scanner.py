from unittest.mock import patch

from django.test import SimpleTestCase

from apps.discovery.services.scanner import build_scan_hosts, preflight_address


class DiscoveryScannerTests(SimpleTestCase):
    """Тесты сетевого scanner без реальной сети."""

    def test_build_scan_hosts_enforces_max_cidr(self):
        """Discovery не принимает подсети шире /24."""

        with self.assertRaisesMessage(ValueError, "Максимальный размер подсети"):
            build_scan_hosts(["10.0.0.0/23"])

    def test_build_scan_hosts_excludes_addresses(self):
        """Scanner исключает IP из списка exclude_ips."""

        hosts = build_scan_hosts(["192.0.2.0/30"], excludes=["192.0.2.1"])

        self.assertEqual(hosts, ["192.0.2.2"])

    @patch("apps.discovery.services.scanner.tcp_is_open")
    @patch("apps.discovery.services.scanner.ping_host")
    def test_preflight_address_returns_detected_protocols(self, mock_ping, mock_tcp):
        """Preflight возвращает состояние ping и CLI TCP-портов."""

        mock_ping.return_value = True
        mock_tcp.side_effect = [True, False]

        detected, attempts = preflight_address("192.0.2.10", ["ssh", "telnet"], timeout=1)

        self.assertEqual(detected, {"ping": True, "ssh": True, "telnet": False})
        self.assertEqual([attempt.method for attempt in attempts], ["PING", "TCP_22", "TCP_23"])
