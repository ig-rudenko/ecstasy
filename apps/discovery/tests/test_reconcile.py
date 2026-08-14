from django.test import TestCase

from apps.check.models import AuthGroup, DeviceGroup, Devices
from apps.discovery.models import DiscoveryCandidate, DiscoveryProfile
from apps.discovery.services.dataclasses import DeviceFingerprint
from apps.discovery.services.reconcile import calculate_confidence, upsert_candidate


class DiscoveryReconcileTests(TestCase):
    """Тесты reconcile discovery candidates."""

    def setUp(self) -> None:
        """Создать общие объекты для тестов."""

        self.group = DeviceGroup.objects.create(name="Access")
        self.auth_group = AuthGroup.objects.create(name="default", login="u", password="p")
        self.profile = DiscoveryProfile.objects.create(
            name="test",
            auto_create=True,
            networks=[],
            device_group=self.group,
            cmd_protocol="auto",
            port_scan_protocol="auto",
        )

    def create_created_candidate(
        self,
        ip: str,
        *,
        cmd_protocol: str,
        port_scan_protocol: str,
    ) -> tuple[DiscoveryCandidate, Devices]:
        """Создать CREATED-кандидата со связанным оборудованием."""

        device = Devices.objects.create(
            ip=ip,
            name=f"known-{ip.rsplit('.', 1)[-1]}",
            group=self.group,
            auth_group=self.auth_group,
            cmd_protocol=cmd_protocol,
            port_scan_protocol=port_scan_protocol,
        )
        candidate = DiscoveryCandidate.objects.create(
            ip=device.ip,
            name=device.name,
            status=DiscoveryCandidate.Status.CREATED,
            device=device,
        )
        return candidate, device

    def test_upsert_candidate_marks_ready_when_identity_is_reliable(self):
        """Fingerprint с vendor/model/auth становится READY."""

        fingerprint = DeviceFingerprint(
            ip="192.0.2.10",
            name="sw-1",
            vendor="Eltex",
            model="MES",
            detected_protocols={"ping": True, "ssh": True},
            selected_auth_group=self.auth_group,
        )

        candidate = upsert_candidate(self.profile, fingerprint)

        self.assertEqual(candidate.status, DiscoveryCandidate.Status.READY)
        self.assertEqual(candidate.confidence, 70)
        self.assertEqual(candidate.name, "sw-1")

    def test_upsert_candidate_marks_duplicate_by_ip(self):
        """Кандидат с уже существующим IP получает DUPLICATE."""

        device = Devices.objects.create(
            ip="192.0.2.11",
            name="known",
            group=self.group,
            auth_group=self.auth_group,
        )
        fingerprint = DeviceFingerprint(
            ip=device.ip,
            name="known-new",
            vendor="Cisco",
            detected_protocols={"ping": True},
        )

        candidate = upsert_candidate(self.profile, fingerprint)

        self.assertEqual(candidate.status, DiscoveryCandidate.Status.DUPLICATE)
        self.assertEqual(candidate.device, device)

    def test_upsert_candidate_does_not_mark_duplicate_by_name(self):
        """Кандидат с совпадающим именем и новым IP не получает DUPLICATE."""

        device = Devices.objects.create(
            ip="192.0.2.13",
            name="known",
            group=self.group,
            auth_group=self.auth_group,
        )
        existing_candidate = DiscoveryCandidate.objects.create(
            ip=device.ip,
            name=device.name,
            status=DiscoveryCandidate.Status.DUPLICATE,
            device=device,
        )
        fingerprint = DeviceFingerprint(
            ip="192.0.2.14",
            name=device.name,
            vendor="Cisco",
            detected_protocols={"ping": True},
        )

        candidate = upsert_candidate(self.profile, fingerprint)

        self.assertEqual(candidate.status, DiscoveryCandidate.Status.READY)
        self.assertIsNone(candidate.device)
        self.assertNotIn("duplicateDeviceId", candidate.raw_fingerprint)
        existing_candidate.refresh_from_db()
        self.assertEqual(existing_candidate.device, device)

    def test_upsert_candidate_does_not_mark_duplicate_by_serial_number(self):
        """Кандидат с совпадающим серийным номером и новым IP не получает DUPLICATE."""

        Devices.objects.create(
            ip="192.0.2.15",
            name="known-serial",
            group=self.group,
            auth_group=self.auth_group,
            serial_number="SERIAL-1",
        )
        fingerprint = DeviceFingerprint(
            ip="192.0.2.16",
            name="new-device",
            vendor="Cisco",
            serial_number="SERIAL-1",
            detected_protocols={"ping": True},
        )

        candidate = upsert_candidate(self.profile, fingerprint)

        self.assertEqual(candidate.status, DiscoveryCandidate.Status.READY)
        self.assertIsNone(candidate.device)
        self.assertNotIn("duplicateDeviceId", candidate.raw_fingerprint)

    def test_upsert_created_candidate_keeps_available_cli_protocols(self):
        """Доступные CLI-протоколы существующего оборудования не изменяются."""

        candidate, device = self.create_created_candidate(
            "192.0.2.30",
            cmd_protocol="telnet",
            port_scan_protocol="telnet",
        )
        fingerprint = DeviceFingerprint(
            ip=candidate.ip,
            detected_protocols={"snmp": False, "ssh": True, "telnet": True},
            raw={"cliProtocol": "ssh"},
        )

        updated_candidate = upsert_candidate(self.profile, fingerprint)

        device.refresh_from_db()
        self.assertEqual(updated_candidate.status, DiscoveryCandidate.Status.CREATED)
        self.assertEqual(device.cmd_protocol, "telnet")
        self.assertEqual(device.port_scan_protocol, "telnet")

    def test_upsert_created_candidate_switches_unavailable_cli_protocols(self):
        """Недоступный SSH существующего оборудования заменяется на Telnet."""

        candidate, device = self.create_created_candidate(
            "192.0.2.31",
            cmd_protocol="ssh",
            port_scan_protocol="ssh",
        )
        fingerprint = DeviceFingerprint(
            ip=candidate.ip,
            detected_protocols={"snmp": False, "ssh": False, "telnet": True},
            raw={"cliProtocol": "telnet"},
        )

        updated_candidate = upsert_candidate(self.profile, fingerprint)

        device.refresh_from_db()
        self.assertEqual(updated_candidate.status, DiscoveryCandidate.Status.CREATED)
        self.assertEqual(device.cmd_protocol, "telnet")
        self.assertEqual(device.port_scan_protocol, "telnet")

    def test_upsert_created_candidate_switches_unavailable_telnet_to_ssh(self):
        """Недоступный Telnet существующего оборудования заменяется на SSH."""

        candidate, device = self.create_created_candidate(
            "192.0.2.36",
            cmd_protocol="telnet",
            port_scan_protocol="telnet",
        )
        fingerprint = DeviceFingerprint(
            ip=candidate.ip,
            detected_protocols={"snmp": False, "ssh": True, "telnet": False},
            raw={"cliProtocol": "ssh"},
        )

        upsert_candidate(self.profile, fingerprint)

        device.refresh_from_db()
        self.assertEqual(device.cmd_protocol, "ssh")
        self.assertEqual(device.port_scan_protocol, "ssh")

    def test_upsert_created_candidate_keeps_available_snmp_protocol(self):
        """Доступный SNMP сохраняется как протокол сбора интерфейсов."""

        candidate, device = self.create_created_candidate(
            "192.0.2.32",
            cmd_protocol="telnet",
            port_scan_protocol="snmp",
        )
        fingerprint = DeviceFingerprint(
            ip=candidate.ip,
            detected_protocols={"snmp": True, "ssh": True, "telnet": True},
            raw={"cliProtocol": "ssh"},
        )

        upsert_candidate(self.profile, fingerprint)

        device.refresh_from_db()
        self.assertEqual(device.cmd_protocol, "telnet")
        self.assertEqual(device.port_scan_protocol, "snmp")

    def test_upsert_created_candidate_switches_unavailable_snmp_to_cli(self):
        """Недоступный SNMP заменяется на доступный CLI-протокол."""

        candidate, device = self.create_created_candidate(
            "192.0.2.33",
            cmd_protocol="telnet",
            port_scan_protocol="snmp",
        )
        fingerprint = DeviceFingerprint(
            ip=candidate.ip,
            detected_protocols={"snmp": False, "ssh": True, "telnet": True},
            raw={"cliProtocol": "ssh"},
        )

        upsert_candidate(self.profile, fingerprint)

        device.refresh_from_db()
        self.assertEqual(device.cmd_protocol, "telnet")
        self.assertEqual(device.port_scan_protocol, "ssh")

    def test_upsert_created_candidate_does_not_switch_unchecked_protocol(self):
        """Отсутствующий результат проверки не считается недоступностью протокола."""

        candidate, device = self.create_created_candidate(
            "192.0.2.34",
            cmd_protocol="ssh",
            port_scan_protocol="ssh",
        )
        fingerprint = DeviceFingerprint(
            ip=candidate.ip,
            detected_protocols={"snmp": False, "telnet": True},
            raw={"cliProtocol": "telnet"},
        )

        upsert_candidate(self.profile, fingerprint)

        device.refresh_from_db()
        self.assertEqual(device.cmd_protocol, "ssh")
        self.assertEqual(device.port_scan_protocol, "ssh")

    def test_upsert_created_candidate_keeps_protocols_without_available_cli(self):
        """Протоколы сохраняются, когда доступной CLI-альтернативы нет."""

        candidate, device = self.create_created_candidate(
            "192.0.2.35",
            cmd_protocol="ssh",
            port_scan_protocol="snmp",
        )
        fingerprint = DeviceFingerprint(
            ip=candidate.ip,
            detected_protocols={"snmp": False, "ssh": False, "telnet": False},
        )

        upsert_candidate(self.profile, fingerprint)

        device.refresh_from_db()
        self.assertEqual(device.cmd_protocol, "ssh")
        self.assertEqual(device.port_scan_protocol, "snmp")

    def test_calculate_confidence_clamps_duplicate_penalty(self):
        """Confidence не уходит ниже нуля после штрафа за дубли."""

        fingerprint = DeviceFingerprint(ip="192.0.2.12", detected_protocols={})

        self.assertEqual(calculate_confidence(fingerprint, duplicate=True), 0)
