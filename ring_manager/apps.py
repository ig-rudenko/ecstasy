from django.apps import AppConfig
from django.db.models.signals import post_migrate


class RingManagerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ring_manager"

    def ready(self):
        from .new_permissions import create_permission

        post_migrate.connect(create_permission, sender=self)
