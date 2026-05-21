from django.test import TestCase
from rest_framework.exceptions import ValidationError

from apps.check.models import AuthGroup, DeviceGroup, Devices, User
from apps.discovery.models import DiscoveryCandidate
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
