from django.test import TestCase
from rest_framework.exceptions import ValidationError

from apps.check.models import AuthGroup, DeviceGroup, Devices, User
from apps.discovery.models import DiscoveryCandidate, DiscoveryProfile
from apps.discovery.services.provisioning import accept_candidate


class DiscoveryProvisioningTests(TestCase):
    """Тесты создания Devices из discovery candidates."""

    def setUp(self) -> None:
        """Создать группу, авторизацию и пользователя."""

        self.group = DeviceGroup.objects.create(name="Access")
        self.auth_group = AuthGroup.objects.create(name="default", login="u", password="p")
        self.user = User.objects.create_user(username="operator")

    def test_accept_candidate_creates_inactive_device(self):
        """Новое устройство создается inactive до успешного сбора интерфейсов."""

        candidate = DiscoveryCandidate.objects.create(
            ip="192.0.2.20",
            name="sw-20",
            vendor="Eltex",
            model="MES",
            status=DiscoveryCandidate.Status.READY,
            selected_auth_group=self.auth_group,
            selected_snmp_community="public",
        )

        device = accept_candidate(candidate, device_group=self.group, user=self.user)

        self.assertFalse(device.active)
        self.assertEqual(device.ip, candidate.ip)
        self.assertEqual(device.snmp_community, "public")
        candidate.refresh_from_db()
        self.assertEqual(candidate.status, DiscoveryCandidate.Status.CREATED)
        self.assertEqual(candidate.device, device)

    def test_accept_candidate_activates_device_when_profile_option_enabled(self):
        """Профиль может создавать оборудование сразу активным."""

        profile = DiscoveryProfile.objects.create(
            name="active-devices",
            networks=["192.0.2.0/24"],
            device_group=self.group,
            try_protocols=["ssh"],
            port_scan_protocol="snmp",
            cmd_protocol="ssh",
            max_workers=4,
            timeout_seconds=1,
            activate_created_devices=True,
        )
        candidate = DiscoveryCandidate.objects.create(
            ip="192.0.2.23",
            name="sw-23",
            status=DiscoveryCandidate.Status.READY,
            selected_auth_group=self.auth_group,
        )

        device = accept_candidate(candidate, profile=profile)

        self.assertTrue(device.active)

    def test_accept_candidate_uses_profile_protocols_when_snmp_is_detected(self):
        """Явные протоколы профиля имеют приоритет над обнаруженными."""

        profile = DiscoveryProfile.objects.create(
            name="telnet-devices",
            networks=["192.0.2.0/24"],
            device_group=self.group,
            try_protocols=["telnet"],
            port_scan_protocol="telnet",
            cmd_protocol="telnet",
            max_workers=4,
            timeout_seconds=1,
        )
        candidate = DiscoveryCandidate.objects.create(
            ip="192.0.2.24",
            name="sw-24",
            status=DiscoveryCandidate.Status.READY,
            selected_auth_group=self.auth_group,
            selected_snmp_community="public",
            detected_protocols={"snmp": True, "ssh": True, "telnet": True},
            raw_fingerprint={"cliProtocol": "ssh"},
        )

        device = accept_candidate(candidate, profile=profile)

        self.assertEqual(device.port_scan_protocol, "telnet")
        self.assertEqual(device.cmd_protocol, "telnet")
        self.assertEqual(device.snmp_community, "public")

    def test_deleted_device_returns_candidate_to_ready_for_recreation(self):
        """После удаления оборудования кандидата можно создать повторно."""

        candidate = DiscoveryCandidate.objects.create(
            ip="192.0.2.25",
            name="sw-25",
            status=DiscoveryCandidate.Status.READY,
            selected_auth_group=self.auth_group,
        )
        first_device = accept_candidate(candidate, device_group=self.group)

        first_device.delete()
        candidate.refresh_from_db()

        self.assertEqual(candidate.status, DiscoveryCandidate.Status.READY)
        self.assertIsNone(candidate.device_id)

        second_device = accept_candidate(candidate, device_group=self.group)

        self.assertNotEqual(second_device.pk, first_device.pk)
        candidate.refresh_from_db()
        self.assertEqual(candidate.status, DiscoveryCandidate.Status.CREATED)
        self.assertEqual(candidate.device, second_device)

    def test_accept_duplicate_candidate_is_rejected(self):
        """DUPLICATE candidate нельзя создать как новое устройство."""

        device = Devices.objects.create(
            ip="192.0.2.21",
            name="known",
            group=self.group,
            auth_group=self.auth_group,
        )
        candidate = DiscoveryCandidate.objects.create(
            ip=device.ip,
            name="known",
            status=DiscoveryCandidate.Status.DUPLICATE,
            device=device,
            selected_auth_group=self.auth_group,
        )

        with self.assertRaises(ValidationError):
            accept_candidate(candidate, device_group=self.group)

    def test_accept_candidate_with_profile_requires_verified_auth_group(self):
        """Создание через профиль не подставляет первую AuthGroup без проверки."""

        profile = DiscoveryProfile.objects.create(
            name="access-net",
            networks=["192.0.2.0/24"],
            device_group=self.group,
            try_protocols=["ssh"],
            port_scan_protocol="snmp",
            cmd_protocol="ssh",
            max_workers=4,
            timeout_seconds=1,
        )
        profile.auth_groups.add(self.auth_group)
        candidate = DiscoveryCandidate.objects.create(
            ip="192.0.2.22",
            name="sw-22",
            status=DiscoveryCandidate.Status.READY,
            raw_fingerprint={"authCheck": {"status": "FAILED"}},
        )

        with self.assertRaises(ValidationError):
            accept_candidate(candidate, profile=profile)
