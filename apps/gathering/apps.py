from django.apps import AppConfig
from django.db.models.signals import post_migrate


class FindDescConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.gathering"

    def ready(self):
        def register_task(sender, **kwargs):
            # pylint: disable-next=import-outside-toplevel
            from .tasks import (
                ConfigurationGatherTask,
                DevicesComplexGatherTask,
                MacTablesGatherTask,
                VlanTablesGatherTask,
            )

            ConfigurationGatherTask.register_task()
            MacTablesGatherTask.register_task()
            VlanTablesGatherTask.register_task()
            DevicesComplexGatherTask.register_task()

        post_migrate.connect(register_task, sender=self)
