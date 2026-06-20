from django.apps import AppConfig
from django.db.models.signals import post_migrate


class AppSettingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.app_settings"
    verbose_name = "App settings"

    def ready(self):
        post_migrate.connect(
            register_task,
            sender=self,
            weak=False,
            dispatch_uid="app_settings.register_task",
        )


def register_task(*args, **kwargs) -> None:
    """Registers periodic/background tasks after migrations."""
    from django_celery_beat.models import CrontabSchedule, PeriodicTask

    from .tasks import flush_expired_cookie_sessions, flush_expired_tokens

    crontab, _ = CrontabSchedule.objects.get_or_create(minute="0", hour="4")
    PeriodicTask.objects.get_or_create(
        name="Очистка истёкших JWT",
        defaults={
            "task": flush_expired_tokens.name,
            "crontab": crontab,
            "enabled": True,
        },
    )
    PeriodicTask.objects.get_or_create(
        name="Очистка истёкших Cookies",
        defaults={
            "task": flush_expired_cookie_sessions.name,
            "crontab": crontab,
            "enabled": True,
        },
    )
