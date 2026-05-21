from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from devicemanager import snmp


class SnmpIdentityTests(SimpleTestCase):
    """Тесты легкого SNMP identity для discovery."""

    @patch("devicemanager.snmp.subprocess.run")
    def test_snmpwalk_single_value_limits_retries_and_process_timeout(self, mock_run):
        """SNMP identity ограничивает ретраи snmpwalk и timeout процесса."""

        mock_run.return_value = Mock(stdout='"switch-name"\n')

        value = snmp._snmpwalk_single_value(
            community="public",
            ip="192.0.2.10",
            port=161,
            mib="SNMPv2-MIB::sysName.0",
            timeout=2,
        )

        self.assertEqual(value, "switch-name")
        mock_run.assert_called_once_with(
            [
                "snmpwalk",
                "-Oqv",
                "-v2c",
                "-t",
                "2",
                "-r",
                "0",
                "-c",
                "public",
                "192.0.2.10:161",
                "SNMPv2-MIB::sysName.0",
            ],
            stdout=snmp.subprocess.PIPE,
            stderr=snmp.subprocess.DEVNULL,
            encoding="utf-8",
            errors="ignore",
            check=False,
            timeout=3,
        )
