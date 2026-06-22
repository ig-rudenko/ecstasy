from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


def create_permission(sender, **kwargs):
    content_type = ContentType.objects.get_for_model(get_user_model())
    extra_permissions = [
        ("access_wtf_search", "Can use wtf search"),
        ("access_desc_search", "Can use desc search"),
        ("access_traceroute", "Can use traceroute"),
        ("access_bulk_device_cmd", "Can execute bulk device commands"),
        ("access_run_interfaces_gather", "Can run interfaces gather"),
        ("access_run_mac_gather", "Can run mac gather"),
    ]

    for codename, name in extra_permissions:
        Permission.objects.get_or_create(codename=codename, name=name, content_type=content_type)


def create_groups_with_permissions(sender, **kwargs):
    g, _ = Group.objects.get_or_create(name="Доступ к WTF")
    g.permissions.add(
        Permission.objects.get(codename="access_wtf_search"),
    )

    g, _ = Group.objects.get_or_create(name="Доступ к поиску по описанию порта")
    g.permissions.add(
        Permission.objects.get(codename="access_desc_search"),
    )

    g, _ = Group.objects.get_or_create(name="Доступ к трассировке")
    g.permissions.add(
        Permission.objects.get(codename="access_traceroute"),
    )

    g, _ = Group.objects.get_or_create(name="Доступ к множественному выполнению команд")
    g.permissions.add(
        Permission.objects.get(codename="access_bulk_device_cmd"),
    )
