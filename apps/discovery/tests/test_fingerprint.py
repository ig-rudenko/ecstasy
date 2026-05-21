import subprocess
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.discovery.models import DiscoveryAttempt
from apps.discovery.services.fingerprint import SnmpFingerprinter


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
