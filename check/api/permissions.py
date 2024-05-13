from rest_framework import permissions
from rest_framework.request import Request

from check.models import Devices, DeviceMedia, Profile


def get_user_devices_groups(user_id) -> list[int]:
    try:
        profile = Profile.objects.get(user_id=user_id)
    except Profile.DoesNotExist:
        return []

    return list(profile.devices_groups.all().values_list("id", flat=True))


class DevicePermission(permissions.BasePermission):
    """Разрешение на использование оборудования"""

    def has_object_permission(self, request: Request, view, obj: Devices) -> bool:
        """
        ## Определяет, имеет ли пользователь "user" право взаимодействовать с оборудованием
        """
        user_available_groups = get_user_devices_groups(request.user.id)
        if obj.group_id in user_available_groups:
            return True
        return False


class DeviceMediaPermission(permissions.BasePermission):
    """Разрешение на изменение медиафайла"""

    def has_object_permission(self, request: Request, view, obj: DeviceMedia) -> bool:
        user_available_groups = get_user_devices_groups(request.user.id)
        if request.user.is_staff and obj.device.group_id in user_available_groups:
            return True
        return False
