from django.contrib.auth.models import AnonymousUser, User
from django.db.models import Q
from rest_framework import permissions
from rest_framework.request import Request

from check.models import AccessGroup, DeviceMedia, Devices, Profile


def has_access_by_profile(user_id: int, group_id: int) -> bool:
    """Проверка доступа пользователя через его профиль"""
    return Profile.objects.filter(user_id=user_id, devices_groups__id=group_id).exists()


def has_access_by_access_group(user: User, device: Devices) -> bool:
    """Проверка доступа через AccessGroup"""
    return (
        AccessGroup.objects.filter(devices=device)
        .filter(Q(users=user) | Q(user_groups__in=user.groups.all()))
        .exclude(forbidden_devices=device)
        .exists()
    )


def has_user_access_to_device(user: User | AnonymousUser, device: Devices) -> bool:
    """Объединённая проверка доступа: через профиль или AccessGroup"""
    if not user.is_authenticated:
        return False
    return has_access_by_profile(user.id, device.group_id) or has_access_by_access_group(user, device)


class DevicePermission(permissions.BasePermission):
    """Разрешение на использование оборудования"""

    def has_object_permission(self, request: Request, view, obj: Devices) -> bool:
        return has_user_access_to_device(request.user, obj)


class DeviceMediaPermission(permissions.BasePermission):
    """Разрешение на изменение медиафайла"""

    def has_object_permission(self, request: Request, view, obj: DeviceMedia) -> bool:
        return request.user.is_staff and has_user_access_to_device(request.user, obj.device)
