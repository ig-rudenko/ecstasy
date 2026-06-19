from datetime import timedelta
from threading import get_ident
from unittest.mock import patch

from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from django_celery_beat.models import PeriodicTask

from apps.check.models import AuthGroup, DeviceGroup
from apps.discovery.apps import register_task
from apps.discovery.models import DiscoveryAttempt, DiscoveryCandidate, DiscoveryProfile, DiscoveryRun
from apps.discovery.services.dataclasses import DeviceFingerprint
from apps.discovery.tasks import cleanup_discovery_runs_task, discovery_run_task, should_auto_create


class DiscoveryCleanupTaskTests(TestCase):
    """Тесты очистки старых запусков discovery."""

    def setUp(self) -> None:
        """Создать профиль discovery."""

        self.group = DeviceGroup.objects.create(name="Access")
        self.profile = DiscoveryProfile.objects.create(
            name="access-net",
            networks=["192.0.2.0/30"],
            device_group=self.group,
        )

    def test_cleanup_discovery_runs_task_deletes_old_finished_runs_and_attempts(self) -> None:
        """Cleanup удаляет только старые завершенные запуски и их попытки."""

        old_finished = DiscoveryRun.objects.create(
            profile=self.profile,
            status=DiscoveryRun.Status.SUCCESS,
            finished_at=timezone.now(),
        )
        recent_finished = DiscoveryRun.objects.create(
            profile=self.profile,
            status=DiscoveryRun.Status.SUCCESS,
            finished_at=timezone.now(),
        )
        old_active = DiscoveryRun.objects.create(
            profile=self.profile,
            status=DiscoveryRun.Status.PROGRESS,
            finished_at=timezone.now(),
        )
        DiscoveryAttempt.objects.create(
            run=old_finished,
            ip="192.0.2.10",
            method=DiscoveryAttempt.Method.PING,
            status=DiscoveryAttempt.Status.SUCCESS,
        )
        DiscoveryAttempt.objects.create(
            run=recent_finished,
            ip="192.0.2.11",
            method=DiscoveryAttempt.Method.PING,
            status=DiscoveryAttempt.Status.SUCCESS,
        )
        old_finished_at = timezone.now() - timedelta(days=31)
        recent_finished_at = timezone.now() - timedelta(days=5)
        DiscoveryRun.objects.filter(id=old_finished.id).update(finished_at=old_finished_at)
        DiscoveryRun.objects.filter(id=recent_finished.id).update(finished_at=recent_finished_at)
        DiscoveryRun.objects.filter(id=old_active.id).update(finished_at=old_finished_at)

        result = cleanup_discovery_runs_task(30)

        self.assertEqual(result["deletedRuns"], 1)
        self.assertFalse(DiscoveryRun.objects.filter(id=old_finished.id).exists())
        self.assertFalse(DiscoveryAttempt.objects.filter(run_id=old_finished.id).exists())
        self.assertTrue(DiscoveryRun.objects.filter(id=recent_finished.id).exists())
        self.assertTrue(DiscoveryRun.objects.filter(id=old_active.id).exists())


class DiscoveryTasksRegistrationTestCase(TestCase):
    """Тесты регистрации фоновых задач discovery."""

    def test_register_task_creates_discovery_cleanup_periodic_task(self) -> None:
        """Post-migrate registration создает задачу очистки старых discovery runs."""

        register_task()

        task = PeriodicTask.objects.get(name="Очистка старых запусков discovery")
        self.assertEqual(task.task, cleanup_discovery_runs_task.name)
        self.assertTrue(task.enabled)
        self.assertEqual(task.kwargs, '{"retention_days": 14}')
        self.assertEqual(task.crontab.minute, "30")
        self.assertEqual(task.crontab.hour, "4")


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
