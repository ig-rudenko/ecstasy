from django.apps import AppConfig
from django.db.models.signals import post_migrate


class FindDescConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.gathering"

    def ready(self) -> None:
        """Подключить регистрацию периодических задач после миграций."""

        post_migrate.connect(register_tasks, sender=self, weak=False, dispatch_uid="gathering.register_tasks")


def register_tasks(*args, **kwargs) -> None:
    """Создать периодические задачи сбора и очистки истории."""

    # pylint: disable-next=import-outside-toplevel
    from django_celery_beat.models import PeriodicTask

    from ecstasy_project.celery_schedules import get_crontab_schedule

    from .tasks import (
        ConfigurationGatherTask,
        DevicesComplexGatherTask,
        MacTablesGatherTask,
        VlanTablesGatherTask,
        cleanup_gathering_tasks_task,
    )

    ConfigurationGatherTask.register_task()
    MacTablesGatherTask.register_task()
    VlanTablesGatherTask.register_task()
    DevicesComplexGatherTask.register_task()

    crontab = get_crontab_schedule(minute="30", hour="4")
    PeriodicTask.objects.get_or_create(
        name="Очистка старых результатов опроса оборудования",
        defaults={
            "task": cleanup_gathering_tasks_task.name,
            "crontab": crontab,
            "kwargs": '{"retention_days": 14}',
            "enabled": True,
            "description": "Удаляет старые запуски сбора и связанные результаты оборудования. "
            "В аргументе указывается количество дней хранения.",
        },
    )
