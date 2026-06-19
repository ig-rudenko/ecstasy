from django.apps import AppConfig
from django.db.models.signals import post_migrate


def register_task(*args, **kwargs) -> None:
    """Создать периодические задачи discovery после миграций."""

    # pylint: disable-next=import-outside-toplevel
    from django_celery_beat.models import CrontabSchedule, PeriodicTask

    from .tasks import cleanup_discovery_runs_task

    crontab, _ = CrontabSchedule.objects.get_or_create(
        minute="30",
        hour="4",
    )
    PeriodicTask.objects.get_or_create(
        name="Очистка старых запусков discovery",
        defaults={
            "task": cleanup_discovery_runs_task.name,
            "crontab": crontab,
            "kwargs": '{"retention_days": 14}',
            "enabled": True,
            "description": "Удаляет старые discovery. "
            "В аргументе указывается кол-во дней, старше которых discovery будут удалены.",
        },
    )


class DiscoveryConfig(AppConfig):
    """Конфигурация приложения auto discovery."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.discovery"
    verbose_name = "Auto Discovery"

    def ready(self) -> None:
        """Подключить post-migrate hooks discovery."""

        from .new_permissions import create_permission

        post_migrate.connect(
            create_permission,
            sender=self,
            weak=False,
            dispatch_uid="discovery.create_permission",
        )
        post_migrate.connect(
            register_task,
            sender=self,
            weak=False,
            dispatch_uid="discovery.register_task",
        )
