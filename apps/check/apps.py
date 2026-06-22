from django.apps import AppConfig
from django.db.models.signals import post_migrate


def register_task(*args, **kwargs) -> None:
    """Register periodic/background tasks after migrations."""
    # pylint: disable-next=import-outside-toplevel
    from django_celery_beat.models import CrontabSchedule, PeriodicTask

    crontab, _ = CrontabSchedule.objects.get_or_create(
        minute="30",
        hour="3",
    )
    PeriodicTask.objects.get_or_create(
        name="Синхронизация координат оборудования с Zabbix",
        defaults={
            "task": "sync_device_coordinates_with_zabbix_task",
            "crontab": crontab,
            "enabled": False,
        },
    )


class CheckConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.check"
    verbose_name = "_Управление оборудованием"

    def ready(self):
        """Connect post-migrate hooks for check app tasks."""
        from .new_permissions import create_groups_with_permissions, create_permission

        post_migrate.connect(
            register_task,
            sender=self,
            weak=False,
            dispatch_uid="check.register_task",
        )
        post_migrate.connect(
            create_permission,
            sender=self,
            weak=False,
            dispatch_uid="check.create_permission",
        )
        post_migrate.connect(
            create_groups_with_permissions,
            sender=self,
            weak=False,
            dispatch_uid="check.create_groups_with_permissions",
        )
