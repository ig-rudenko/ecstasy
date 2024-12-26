from django.apps import AppConfig
from django.db.models.signals import post_migrate


class FindDescConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "net_tools"

    def ready(self):
        # pylint: disable-next=import-outside-toplevel
        from .new_permissions import create_permission

        post_migrate.connect(create_permission, sender=self)

        def register_task(sender, **kwargs):
            # pylint: disable-next=import-outside-toplevel
            from net_tools.tasks import InterfacesScanTask

            InterfacesScanTask.register_task()

        post_migrate.connect(register_task, sender=self)
