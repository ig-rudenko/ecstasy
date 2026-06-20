from django.contrib.auth.models import AnonymousUser, User
from django.db.models import Q
from rest_framework import permissions
from rest_framework.request import Request

from ..models import DeviceMedia, Devices, InterfacesComments


def has_user_access_to_device(user: User | AnonymousUser, device: Devices) -> bool:
    """Объединённая проверка доступа: через профиль или AccessGroup"""
    if not user.is_authenticated:
        return False
    qs = (
        Devices.objects.filter(
            Q(id=device.id)
            & (
                Q(group__profile__user=user)
                | Q(access_groups__users=user)
                | Q(access_groups__user_groups__user=user)
            )
        )
        .exclude(Q(forbidden_access_groups__users=user) | Q(forbidden_access_groups__user_groups__user=user))
        .only("id")
    )
    return qs.exists()


class DevicePermission(permissions.BasePermission):
    """Разрешение на использование оборудования"""

    def has_object_permission(self, request: Request, view, obj: Devices) -> bool:
        return has_user_access_to_device(request.user, obj)


class DeviceMediaPermission(permissions.BasePermission):
    """Разрешение на изменение медиафайла"""

    def has_object_permission(self, request: Request, view, obj: DeviceMedia) -> bool:
        return request.user.is_staff and has_user_access_to_device(request.user, obj.device)


class DeviceCommentPermission(permissions.BasePermission):
    """Разрешение на изменение комментария к порту на оборудовании"""

    def has_object_permission(self, request: Request, view, obj: InterfacesComments) -> bool:
        return request.user.is_superuser or (
            request.user == obj.user and has_user_access_to_device(request.user, obj.device)
        )


class DevicesAdminPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method is permissions.SAFE_METHODS or request.user.is_superuser:
            return True
        if request.method == "POST" and request.user.is_staff and request.user.has_perm("check.add_devices"):
            return True
        if (
            request.method in {"PUT", "PATCH"}
            and request.user.is_staff
            and request.user.has_perm("check.change_devices")
        ):
            return True
        return bool(
            request.method == "DELETE"
            and request.user.is_staff
            and request.user.has_perm("check.change_devices")
        )


class BulkDeviceCommandExecutionPermission(permissions.BasePermission):
    def has_permission(self, request: Request, view):
        perm = "auth.access_bulk_device_cmd"
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_superuser or request.user.has_perm(perm))
        )
