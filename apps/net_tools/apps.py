from django.apps import AppConfig
from django.db.models.signals import post_migrate, post_save


class FindDescConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.net_tools"

    def ready(self):
        # pylint: disable-next=import-outside-toplevel
        from .models import VlanName
        from .new_permissions import create_groups_with_permissions, create_permission
        from .services.default_objects import ensure_default_node_kinds
        from .services.vlan_names import VlanNamesCache

        post_migrate.connect(
            create_permission,
            sender=self,
            weak=False,
            dispatch_uid="net_tools.create_permission",
        )
        post_migrate.connect(
            create_groups_with_permissions,
            sender=self,
            weak=False,
            dispatch_uid="net_tools.create_groups_with_permissions",
        )
        post_migrate.connect(
            register_task,
            sender=self,
            weak=False,
            dispatch_uid="net_tools.register_task",
        )
        post_migrate.connect(
            ensure_default_node_kinds,
            sender=self,
            weak=False,
            dispatch_uid="net_tools.ensure_default_node_kinds",
        )
        post_save.connect(
            vlans_name_post_save_signal,
            sender=VlanName,
            weak=False,
            dispatch_uid=f"net_tools.{VlanNamesCache.cache_key}.clear_cache",
        )


def register_task(*args, **kwargs) -> None:
    """Registers periodic/background tasks after migrations."""
    # pylint: disable-next=import-outside-toplevel
    from .tasks import InterfacesScanTask

    InterfacesScanTask.register_task()


def vlans_name_post_save_signal(sender, instance, created, **kwargs):
    # pylint: disable-next=import-outside-toplevel
    from .services.vlan_names import VlanNamesCache

    VlanNamesCache.clear_cache()
