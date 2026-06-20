from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from .models import Profile


def create_permission(sender, **kwargs) -> None:
    """Create device access permissions."""
    content_type = ContentType.objects.get_for_model(Profile)

    for codename, name in Profile.PERMS:
        Permission.objects.get_or_create(codename=codename, name=name, content_type=content_type)


def get_device_permission(codename: str) -> Permission:
    """Return one check profile permission by codename."""
    content_type = ContentType.objects.get_for_model(Profile)
    return Permission.objects.get(codename=codename, content_type=content_type)


def create_groups_with_permissions(sender, **kwargs):
    """Create default groups for device access permissions."""
    create_permission(sender, **kwargs)

    g, _ = Group.objects.get_or_create(name="Device | Перезагрузка интерфейсов оборудования")
    g.permissions.add(
        get_device_permission(Profile.INTERFACE_REBOOT),
    )
    g, _ = Group.objects.get_or_create(name="Device | Изменение статуса интерфейсов оборудования")
    g.permissions.add(
        get_device_permission(Profile.INTERFACE_UP_DOWN),
    )
    g, _ = Group.objects.get_or_create(name="Device | BRAS | Просмотр сессий")
    g.permissions.add(
        get_device_permission(Profile.BRAS_READ),
    )
    g, _ = Group.objects.get_or_create(name="Device | BRAS | Сброс сессий")
    g.permissions.add(
        get_device_permission(Profile.BRAS_READ),
        get_device_permission(Profile.BRAS_READ_WRITE),
    )
    g, _ = Group.objects.get_or_create(name="Device | Просмотр конфигураций оборудования")
    g.permissions.add(
        get_device_permission(Profile.CONFIG_VIEW),
    )
    g, _ = Group.objects.get_or_create(name="Device | Сбор конфигураций оборудования")
    g.permissions.add(
        get_device_permission(Profile.CONFIG_VIEW),
        get_device_permission(Profile.CONFIG_COLLECT),
    )
    g, _ = Group.objects.get_or_create(name="Device | Удаление конфигураций оборудования")
    g.permissions.add(
        get_device_permission(Profile.CONFIG_VIEW),
        get_device_permission(Profile.CONFIG_DELETE),
    )
    g, _ = Group.objects.get_or_create(name="Device | Выполнение команд на оборудовании")
    g.permissions.add(
        get_device_permission(Profile.CMD_RUN),
    )
