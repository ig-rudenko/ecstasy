from unittest.mock import patch

from django.test import TestCase

from apps.check.models import AuthGroup, DeviceGroup
from apps.discovery.models import DiscoveryCandidate, DiscoveryProfile, DiscoveryRun
from apps.discovery.services.dataclasses import DeviceFingerprint
from apps.discovery.tasks import discovery_run_task, should_auto_create


class DiscoveryTaskTests(TestCase):
    """Тесты Celery-задачи discovery без реальной сети."""

    def setUp(self) -> None:
        """Создать профиль discovery."""

        self.group = DeviceGroup.objects.create(name="Access")
        self.auth_group = AuthGroup.objects.create(name="default", login="u", password="p")
        self.profile = DiscoveryProfile.objects.create(
            name="access-net",
            networks=["192.0.2.0/30"],
            device_group=self.group,
            try_protocols=["ssh"],
            snmp_communities=["public"],
            max_workers=1,
            timeout_seconds=1,
        )
        self.profile.auth_groups.add(self.auth_group)

    @patch("apps.discovery.tasks.DeviceFingerprinter")
    @patch("apps.discovery.tasks.preflight_address")
    def test_discovery_run_task_creates_candidate(self, mock_preflight, mock_fingerprinter):
        """Discovery task создает кандидата по fingerprint."""

        mock_preflight.return_value = ({"ping": True, "ssh": True}, [])
        mock_fingerprinter.return_value.collect.side_effect = lambda ip, detected: (
            DeviceFingerprint(
                ip=ip,
                name=f"sw-{ip.rsplit('.', 1)[-1]}",
                vendor="Eltex",
                model="MES",
                detected_protocols=detected,
                selected_auth_group=self.auth_group,
                source=DiscoveryCandidate.Source.CLI,
            ),
            [],
        )
        run = DiscoveryRun.objects.create(profile=self.profile)

        result = discovery_run_task(run.id)

        run.refresh_from_db()
        mock_fingerprinter.assert_called_with(self.profile, include_cli=True)
        self.assertEqual(run.status, DiscoveryRun.Status.SUCCESS)
        self.assertEqual(run.total, 2)
        self.assertEqual(run.processed, 2)
        self.assertEqual(run.found, 2)
        self.assertEqual(result["found"], 2)
        self.assertEqual(DiscoveryCandidate.objects.count(), 2)

    def test_should_auto_create_requires_verified_auth_group(self):
        """Auto create не должен создавать Devices без рабочей AuthGroup кандидата."""

        self.profile.auto_create = True
        self.profile.auto_create_min_confidence = 40
        self.profile.save(update_fields=["auto_create", "auto_create_min_confidence"])

        candidate = DiscoveryCandidate.objects.create(
            ip="192.0.2.50",
            name="sw-50",
            status=DiscoveryCandidate.Status.READY,
            confidence=80,
            selected_auth_group=None,
        )

        self.assertFalse(should_auto_create(self.profile, candidate, dry_run=False))
