from django.test import TestCase
from django_celery_beat.models import PeriodicTask

from apps.check.apps import register_task


class CheckTasksRegistrationTestCase(TestCase):
    def test_register_task_creates_coordinates_sync_periodic_task(self) -> None:
        """Post-migrate registration creates disabled coordinates sync periodic task."""
        register_task()

        task = PeriodicTask.objects.get(name="Синхронизация координат оборудования с Zabbix")
        self.assertEqual(task.task, "sync_device_coordinates_with_zabbix_task")
        self.assertFalse(task.enabled)
        self.assertEqual(task.crontab.minute, "30")
        self.assertEqual(task.crontab.hour, "3")
