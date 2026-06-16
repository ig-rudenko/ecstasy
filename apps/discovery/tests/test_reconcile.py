from django.test import TestCase

from apps.check.models import AuthGroup, DeviceGroup, Devices
from apps.discovery.models import DiscoveryCandidate
from apps.discovery.services.dataclasses import DeviceFingerprint
from apps.discovery.services.reconcile import calculate_confidence, upsert_candidate


class DiscoveryReconcileTests(TestCase):
    """Тесты reconcile discovery candidates."""

    def setUp(self) -> None:
        """Создать общие объекты для тестов."""

        self.group = DeviceGroup.objects.create(name="Access")
        self.auth_group = AuthGroup.objects.create(name="default", login="u", password="p")

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

        candidate = upsert_candidate(fingerprint)

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

        candidate = upsert_candidate(fingerprint)

        self.assertEqual(candidate.status, DiscoveryCandidate.Status.DUPLICATE)
        self.assertEqual(candidate.device, device)

    def test_upsert_candidate_does_not_reassign_device_from_existing_candidate(self):
        """Новый IP того же устройства не отбирает связь у существующего кандидата."""

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

        candidate = upsert_candidate(fingerprint)

        self.assertEqual(candidate.status, DiscoveryCandidate.Status.DUPLICATE)
        self.assertIsNone(candidate.device)
        self.assertEqual(candidate.raw_fingerprint["duplicateDeviceId"], device.id)
        existing_candidate.refresh_from_db()
        self.assertEqual(existing_candidate.device, device)

    def test_calculate_confidence_clamps_duplicate_penalty(self):
        """Confidence не уходит ниже нуля после штрафа за дубли."""

        fingerprint = DeviceFingerprint(ip="192.0.2.12", detected_protocols={})

        self.assertEqual(calculate_confidence(fingerprint, duplicate=True), 0)
