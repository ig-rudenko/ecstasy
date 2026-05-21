from django.apps import AppConfig
from django.db.models.signals import post_migrate


class DiscoveryConfig(AppConfig):
    """Конфигурация приложения auto discovery."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.discovery"
    verbose_name = "Auto Discovery"

    def ready(self) -> None:
        """Подключить создание custom permissions после миграций."""

        from .new_permissions import create_permission

        post_migrate.connect(
            create_permission,
            sender=self,
            weak=False,
            dispatch_uid="discovery.create_permission",
        )
