from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from django_celery_beat.models import PeriodicTask

from apps.check.models import AuthGroup, DeviceGroup, Devices
from apps.gathering.apps import register_tasks
from apps.gathering.models import DeviceGatheringResult, GatheringTask
from apps.gathering.services.collectors import ThreadUpdatedStatusDeviceTask
from apps.gathering.tasks import cleanup_gathering_tasks_task, reconcile_stale_gathering_tasks_task
from ecstasy_project.celery import app


class SuccessfulGatheringTask(ThreadUpdatedStatusDeviceTask):
    """Тестовая задача с успешным результатом оборудования."""

    name = "successful_gathering_task"
    queryset = Devices.objects.none()
    max_workers = 1

    def thread_task(self, obj: Devices, **kwargs) -> str:
        """Вернуть успешный статус результата."""

        return DeviceGatheringResult.Status.SUCCESS


class FailingGatheringTask(ThreadUpdatedStatusDeviceTask):
    """Тестовая задача с ошибкой опроса оборудования."""

    name = "failing_gathering_task"
    queryset = Devices.objects.none()
    max_workers = 1

    def thread_task(self, obj: Devices, **kwargs) -> str:
        """Сымитировать ошибку опроса оборудования."""

        raise RuntimeError("boom")


class SkippedGatheringTask(ThreadUpdatedStatusDeviceTask):
    """Тестовая задача с пропущенным недоступным оборудованием."""

    name = "skipped_gathering_task"
    queryset = Devices.objects.none()
    max_workers = 1

    def thread_task(self, obj: Devices, **kwargs) -> str:
        """Вернуть статус пропущенного оборудования."""

        return DeviceGatheringResult.Status.SKIPPED


class GatheringTaskLoggingTests(TransactionTestCase):
    """Тесты журналирования потоковых задач сбора данных."""

    def setUp(self) -> None:
        """Создать оборудование для тестового опроса."""

        group = DeviceGroup.objects.create(name="Access")
        auth_group = AuthGroup.objects.create(name="default", login="user", password="password")
        self.device = Devices.objects.create(
            group=group,
            auth_group=auth_group,
            ip="192.0.2.10",
            name="switch-10",
        )

    def test_successful_task_creates_run_and_device_result(self) -> None:
        """Успешный запуск сохраняет один успешный результат оборудования."""

        task = SuccessfulGatheringTask()
        task.bind(app)
        task.queryset = Devices.objects.filter(id=self.device.id)
        task_id = str(uuid4())

        task.push_request(id=task_id, args=(), kwargs={})
        try:
            with patch.object(task, "update_state"):
                result = task.run()
        finally:
            task.pop_request()

        self.assertEqual(result, 1)
        gathering_task = GatheringTask.objects.get(task_id=task_id)
        self.assertEqual(gathering_task.status, GatheringTask.Status.SUCCESS)
        self.assertEqual(gathering_task.total_devices, 1)
        self.assertIsNotNone(gathering_task.finished_at)
        device_result = gathering_task.device_results.get(device=self.device)
        self.assertEqual(device_result.status, DeviceGatheringResult.Status.SUCCESS)
        self.assertEqual(device_result.error_type, "")
        self.assertEqual(device_result.error_message, "")
        self.assertIsNotNone(device_result.finished_at)

    def test_device_error_is_logged_and_marks_run_partial(self) -> None:
        """Ошибка одного устройства сохраняется и не прерывает обработку пула."""

        task = FailingGatheringTask()
        task.bind(app)
        task.queryset = Devices.objects.filter(id=self.device.id)
        task_id = str(uuid4())

        task.push_request(id=task_id, args=(), kwargs={})
        try:
            with patch.object(task, "update_state"):
                result = task.run()
        finally:
            task.pop_request()

        self.assertEqual(result, 1)
        gathering_task = GatheringTask.objects.get(task_id=task_id)
        self.assertEqual(gathering_task.status, GatheringTask.Status.PARTIAL)
        device_result = gathering_task.device_results.get(device=self.device)
        self.assertEqual(device_result.status, DeviceGatheringResult.Status.FAILURE)
        self.assertEqual(device_result.error_type, "RuntimeError")
        self.assertEqual(device_result.error_message, "boom")

    def test_skipped_device_is_logged_as_unavailable(self) -> None:
        """Недоступное оборудование сохраняется как явный пропущенный результат."""

        task = SkippedGatheringTask()
        task.bind(app)
        task.queryset = Devices.objects.filter(id=self.device.id)
        task_id = str(uuid4())
        task.push_request(id=task_id, args=(), kwargs={})
        try:
            with patch.object(task, "update_state"):
                task.run()
        finally:
            task.pop_request()

        gathering_task = GatheringTask.objects.get(task_id=task_id)
        self.assertEqual(gathering_task.status, GatheringTask.Status.PARTIAL)
        device_result = gathering_task.device_results.get(device=self.device)
        self.assertEqual(device_result.status, DeviceGatheringResult.Status.SKIPPED)
        self.assertEqual(device_result.error_type, "Unavailable")
        self.assertEqual(device_result.error_message, "")

    def test_deleting_device_deletes_its_gathering_results(self) -> None:
        """Удаление оборудования каскадно удаляет историю его опросов."""

        gathering_task = GatheringTask.objects.create(
            task_id=str(uuid4()),
            name="test_task",
            status=GatheringTask.Status.SUCCESS,
            total_devices=1,
            finished_at=timezone.now(),
        )
        result = DeviceGatheringResult.objects.create(
            task=gathering_task,
            device=self.device,
            status=DeviceGatheringResult.Status.SUCCESS,
            finished_at=timezone.now(),
        )

        self.device.delete()

        self.assertFalse(DeviceGatheringResult.objects.filter(id=result.id).exists())


class GatheringCleanupTaskTests(TestCase):
    """Тесты очистки истории периодических опросов."""

    def test_cleanup_deletes_only_old_finished_tasks_and_results(self) -> None:
        """Cleanup удаляет старые завершённые запуски вместе с результатами."""

        old_finished = GatheringTask.objects.create(
            task_id=str(uuid4()),
            name="old",
            status=GatheringTask.Status.SUCCESS,
            total_devices=0,
            finished_at=timezone.now() - timedelta(days=15),
        )
        recent_finished = GatheringTask.objects.create(
            task_id=str(uuid4()),
            name="recent",
            status=GatheringTask.Status.SUCCESS,
            total_devices=0,
            finished_at=timezone.now() - timedelta(days=5),
        )
        active = GatheringTask.objects.create(
            task_id=str(uuid4()),
            name="active",
            status=GatheringTask.Status.RUNNING,
            total_devices=0,
        )
        group = DeviceGroup.objects.create(name="Cleanup")
        auth_group = AuthGroup.objects.create(name="cleanup", login="user", password="password")
        device = Devices.objects.create(
            group=group,
            auth_group=auth_group,
            ip="192.0.2.20",
            name="switch-20",
        )
        old_result = DeviceGatheringResult.objects.create(
            task=old_finished,
            device=device,
            status=DeviceGatheringResult.Status.SUCCESS,
            finished_at=old_finished.finished_at,
        )

        result = cleanup_gathering_tasks_task(14)

        self.assertEqual(result, {"deletedCount": 1, "retentionDays": 14})
        self.assertFalse(GatheringTask.objects.filter(id=old_finished.id).exists())
        self.assertFalse(DeviceGatheringResult.objects.filter(id=old_result.id).exists())
        self.assertTrue(GatheringTask.objects.filter(id=recent_finished.id).exists())
        self.assertTrue(GatheringTask.objects.filter(id=active.id).exists())

    def test_cleanup_rejects_non_positive_retention(self) -> None:
        """Cleanup запрещает отключать срок хранения нулём или отрицательным числом."""

        with self.assertRaisesMessage(ValueError, "retention_days must be positive"):
            cleanup_gathering_tasks_task(0)


class StaleGatheringTaskTests(TestCase):
    """Тесты завершения зависших запусков сбора."""

    @patch("apps.gathering.tasks.app.control.inspect")
    def test_reconcile_sets_success_and_last_device_finish_time(self, inspect) -> None:
        """Отсутствующий на воркере запуск получает успешный итог."""

        inspect.return_value.active.return_value = {"worker": []}

        finished_at = timezone.now() - timedelta(minutes=1)
        task = GatheringTask.objects.create(
            task_id=str(uuid4()), name="completed", total_devices=1,
            started_at=finished_at - timedelta(minutes=1),
        )
        group = DeviceGroup.objects.create(name="Reconcile")
        auth_group = AuthGroup.objects.create(name="reconcile", login="user", password="password")
        device = Devices.objects.create(
            group=group, auth_group=auth_group, ip="192.0.2.30", name="switch-30",
        )
        DeviceGatheringResult.objects.create(
            task=task, device=device, status=DeviceGatheringResult.Status.SUCCESS,
            finished_at=finished_at,
        )

        reconcile_stale_gathering_tasks_task()

        task.refresh_from_db()
        self.assertEqual(task.status, GatheringTask.Status.SUCCESS)
        self.assertEqual(task.finished_at, finished_at)

    @patch("apps.gathering.tasks.app.control.inspect")
    def test_reconcile_marks_incomplete_task_partial(self, inspect) -> None:
        """Отсутствующий запуск с частью завершённых устройств получает частичный статус."""

        inspect.return_value.active.return_value = {"worker": []}

        task = GatheringTask.objects.create(
            task_id=str(uuid4()), name="partial", total_devices=2,
            started_at=timezone.now() - timedelta(hours=25),
        )
        group = DeviceGroup.objects.create(name="Partial")
        auth_group = AuthGroup.objects.create(name="partial", login="user", password="password")
        device = Devices.objects.create(
            group=group, auth_group=auth_group, ip="192.0.2.31", name="switch-31",
        )
        DeviceGatheringResult.objects.create(
            task=task, device=device, status=DeviceGatheringResult.Status.FAILURE,
            finished_at=timezone.now() - timedelta(hours=24),
        )

        reconcile_stale_gathering_tasks_task()

        task.refresh_from_db()
        self.assertEqual(task.status, GatheringTask.Status.PARTIAL)
        self.assertIsNotNone(task.finished_at)

    @patch("apps.gathering.tasks.app.control.inspect")
    def test_reconcile_marks_task_without_finished_devices_failure(self, inspect) -> None:
        """Отсутствующий запуск без завершённых устройств получает ошибку."""

        inspect.return_value.active.return_value = {"worker": []}

        task = GatheringTask.objects.create(
            task_id=str(uuid4()), name="failed", total_devices=1,
            started_at=timezone.now() - timedelta(hours=25),
        )

        reconcile_stale_gathering_tasks_task()

        task.refresh_from_db()
        self.assertEqual(task.status, GatheringTask.Status.FAILURE)
        self.assertIsNotNone(task.finished_at)

    @patch("apps.gathering.tasks.app.control.inspect")
    def test_reconcile_leaves_active_and_already_finished_tasks_untouched(self, inspect) -> None:
        """Активные и ранее завершённые запуски не меняются."""

        recent = GatheringTask.objects.create(task_id=str(uuid4()), name="recent")
        finished = GatheringTask.objects.create(
            task_id=str(uuid4()), name="finished", status=GatheringTask.Status.SUCCESS,
            started_at=timezone.now() - timedelta(hours=25), finished_at=timezone.now(),
        )
        inspect.return_value.active.return_value = {"worker": [{"id": recent.task_id}]}

        reconcile_stale_gathering_tasks_task()

        recent.refresh_from_db()
        finished.refresh_from_db()
        self.assertEqual(recent.status, GatheringTask.Status.RUNNING)
        self.assertIsNone(recent.finished_at)
        self.assertEqual(finished.status, GatheringTask.Status.SUCCESS)

    @patch("apps.gathering.tasks.app.control.inspect")
    def test_reconcile_does_nothing_when_workers_do_not_reply(self, inspect) -> None:
        """Недоступный inspect не позволяет считать отсутствие задачи доказанным."""

        inspect.return_value.active.return_value = None
        task = GatheringTask.objects.create(task_id=str(uuid4()), name="unknown")

        self.assertEqual(reconcile_stale_gathering_tasks_task(), {"updatedCount": 0})

        task.refresh_from_db()
        self.assertEqual(task.status, GatheringTask.Status.RUNNING)
        self.assertIsNone(task.finished_at)


class GatheringTasksRegistrationTests(TestCase):
    """Тесты регистрации периодических задач gathering."""

    def test_register_tasks_creates_cleanup_periodic_task(self) -> None:
        """Post-migrate регистрация создаёт ежедневную задачу очистки истории."""

        register_tasks()

        task = PeriodicTask.objects.get(name="Очистка старых результатов опроса оборудования")
        self.assertEqual(task.task, cleanup_gathering_tasks_task.name)
        self.assertTrue(task.enabled)
        self.assertEqual(task.kwargs, '{"retention_days": 14}')
        self.assertEqual(task.crontab.minute, "30")
        self.assertEqual(task.crontab.hour, "4")

    def test_register_tasks_creates_stale_task_reconciliation(self) -> None:
        """Post-migrate регистрация создаёт ежедневную проверку зависших задач."""

        register_tasks()

        task = PeriodicTask.objects.get(name="Завершение зависших задач сбора оборудования")
        self.assertEqual(task.task, reconcile_stale_gathering_tasks_task.name)
        self.assertTrue(task.enabled)
        self.assertEqual(task.crontab.minute, "*/5")
