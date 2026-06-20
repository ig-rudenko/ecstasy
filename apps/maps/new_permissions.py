from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


def create_permission(sender, **kwargs):
    content_type = ContentType.objects.get_for_model(get_user_model())
    extra_permissions = [
        ("can_view_maps", "Can view maps"),
    ]

    for codename, name in extra_permissions:
        Permission.objects.get_or_create(codename=codename, name=name, content_type=content_type)


def create_groups_with_permissions(sender, **kwargs):
    g, _ = Group.objects.get_or_create(name="Доступ к картам")
    g.permissions.add(
        Permission.objects.get(codename="can_view_maps"),
    )
