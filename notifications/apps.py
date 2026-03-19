from django.apps import AppConfig
from django.db.models.signals import post_migrate

from notifications.services.triggers import TriggerNames


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifications"

    def ready(self):
        # pylint: disable-next=import-outside-toplevel
        from .models import NotificationTrigger

        def create_triggers(*args, **kwargs):
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
                update_fields=["description"],
                unique_fields=["name"],
                update_conflicts=True,
            )

        post_migrate.connect(create_triggers, sender=self)
