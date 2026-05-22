from django.apps import AppConfig
from django.db import connection
from django.db.models.signals import post_migrate

from apps.notifications.services.triggers import TriggerNames


def get_notification_trigger_bulk_create_kwargs() -> dict:
    """Return kwargs for NotificationTrigger bulk_create compatible with current DB backend."""
    kwargs = {
        "update_fields": ["description"],
        "update_conflicts": True,
    }
    if connection.features.supports_update_conflicts_with_target:
        kwargs["unique_fields"] = ["name"]
    return kwargs


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notifications"

    def ready(self):
        # pylint: disable-next=import-outside-toplevel
        from .models import NotificationTrigger

        def create_triggers(*args, **kwargs):
            """Create or update default notification triggers after migrations."""
            NotificationTrigger.objects.bulk_create(
                [
                    NotificationTrigger(
                        name=TriggerNames.device_port_reload,
                        description="Был перезагружен порт",
                    ),
                    NotificationTrigger(
                        name=TriggerNames.device_port_down,
                        description="Был включён порт",
                    ),
                    NotificationTrigger(
                        name=TriggerNames.device_port_up,
                        description="Был выключен порт",
                    ),
                    NotificationTrigger(
                        name=TriggerNames.device_port_change_description,
                        description="Было изменено описание порта",
                    ),
                    NotificationTrigger(
                        name=TriggerNames.device_port_set_poe_status,
                        description="Был изменен статус PoE на порту",
                    ),
                    NotificationTrigger(
                        name=TriggerNames.device_port_change_adsl_profile,
                        description="Был изменен профиль ADSL",
                    ),
                ],
                **get_notification_trigger_bulk_create_kwargs(),
            )

        post_migrate.connect(create_triggers, sender=self)
