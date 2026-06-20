from django.apps import AppConfig
from django.db.models.signals import post_migrate


class GponConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.gpon"

    def ready(self):
        # pylint: disable-next=import-outside-toplevel
        from .default_groups import create_groups

        post_migrate.connect(create_groups, sender=self)
