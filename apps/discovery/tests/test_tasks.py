from threading import get_ident
from unittest.mock import patch

from django.test import TransactionTestCase

from apps.check.models import AuthGroup, DeviceGroup
from apps.discovery.models import DiscoveryCandidate, DiscoveryProfile, DiscoveryRun
from apps.discovery.services.dataclasses import DeviceFingerprint
from apps.discovery.tasks import discovery_run_task, should_auto_create


class DiscoveryTaskTests(TransactionTestCase):
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
        mock_fingerprinter.assert_called_with(
            self.profile,
            auth_groups=[self.auth_group],
            include_cli=True,
        )
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

    @patch("apps.discovery.tasks.DeviceFingerprinter")
    @patch("apps.discovery.tasks.preflight_address")
    def test_discovery_run_task_updates_existing_candidate_by_ip(self, mock_preflight, mock_fingerprinter):
        """Повторный discovery по IP обновляет существующего кандидата без дубля."""

        candidate = DiscoveryCandidate.objects.create(
            ip="192.0.2.60",
            name="old-name",
            status=DiscoveryCandidate.Status.NEW,
        )
        mock_preflight.return_value = ({"ping": True, "ssh": True}, [])
        mock_fingerprinter.return_value.collect.return_value = (
            DeviceFingerprint(
                ip=candidate.ip,
                name="new-name",
                vendor="Eltex",
                model="MES",
                detected_protocols={"ping": True, "ssh": True},
                selected_auth_group=self.auth_group,
                source=DiscoveryCandidate.Source.CLI,
            ),
            [],
        )
        run = DiscoveryRun.objects.create(profile=self.profile, dry_run=True)

        discovery_run_task(run.id, [candidate.ip])

        candidate.refresh_from_db()
        self.assertEqual(DiscoveryCandidate.objects.filter(ip=candidate.ip).count(), 1)
        self.assertEqual(candidate.name, "new-name")
        self.assertEqual(candidate.status, DiscoveryCandidate.Status.READY)

    @patch("apps.discovery.tasks.save_attempts")
    @patch("apps.discovery.tasks.upsert_candidate")
    @patch("apps.discovery.tasks.DeviceFingerprinter")
    @patch("apps.discovery.tasks.preflight_address")
    def test_discovery_run_task_keeps_database_writes_in_task_thread(
        self,
        mock_preflight,
        mock_fingerprinter,
        mock_upsert_candidate,
        mock_save_attempts,
    ):
        """ORM-сохранение discovery выполняется вне сетевых worker-потоков."""

        self.profile.max_workers = 2
        self.profile.save(update_fields=["max_workers"])
        task_thread_id = get_ident()
        network_thread_ids = []
        database_thread_ids = []

        def preflight(ip, protocols, timeout):
            """Зафиксировать поток сетевого опроса."""

            network_thread_ids.append(get_ident())
            return {"ping": True, "ssh": True}, []

        def save_attempts(run, candidate, attempts):
            """Зафиксировать поток сохранения попыток."""

            database_thread_ids.append(get_ident())

        candidate = DiscoveryCandidate(
            ip="192.0.2.70",
            status=DiscoveryCandidate.Status.READY,
            confidence=80,
            selected_auth_group=self.auth_group,
        )
        mock_preflight.side_effect = preflight
        mock_fingerprinter.return_value.collect.side_effect = lambda ip, detected: (
            DeviceFingerprint(
                ip=ip,
                vendor="Eltex",
                model="MES",
                detected_protocols=detected,
                selected_auth_group=self.auth_group,
            ),
            [],
        )
        mock_upsert_candidate.side_effect = lambda fingerprint: (
            database_thread_ids.append(get_ident()) or candidate
        )
        mock_save_attempts.side_effect = save_attempts
        run = DiscoveryRun.objects.create(profile=self.profile, dry_run=True)

        discovery_run_task(run.id, ["192.0.2.70", "192.0.2.71"])

        self.assertTrue(network_thread_ids)
        self.assertTrue(all(thread_id != task_thread_id for thread_id in network_thread_ids))
        self.assertTrue(database_thread_ids)
        self.assertTrue(all(thread_id == task_thread_id for thread_id in database_thread_ids))
