from django.apps import AppConfig
from django.db.models.signals import post_migrate


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifications"

    def ready(self):
        # pylint: disable-next=import-outside-toplevel
        from .models import NotificationTrigger

        def create_triggers(*args, **kwargs):
            NotificationTrigger.objects.bulk_create(
                [
                    NotificationTrigger(name="port:reload", description="Был перезагружен порт"),
                    NotificationTrigger(name="port:down", description="Был включён порт"),
                    NotificationTrigger(name="port:up", description="Был выключен порт"),
                ],
                update_fields=["description"],
                unique_fields=["name"],
                update_conflicts=True,
            )

        post_migrate.connect(create_triggers, sender=self)
