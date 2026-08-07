from django.test import TestCase
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from apps.app_settings.apps import register_task


class PeriodicTaskRegistrationTests(TestCase):
    """Тесты регистрации периодических задач приложения."""

    def test_register_task_handles_crontab_schedules_with_same_time(self):
        """Регистрация задач не падает при расписаниях с одинаковыми minute и hour."""

        CrontabSchedule.objects.create(minute="0", hour="4", timezone="UTC")
        CrontabSchedule.objects.create(minute="0", hour="4", timezone="Europe/Moscow")

        register_task()

        self.assertTrue(PeriodicTask.objects.filter(name="Очистка истёкших JWT").exists())
        self.assertTrue(PeriodicTask.objects.filter(name="Очистка истёкших Cookies").exists())
