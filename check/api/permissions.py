from rest_framework import permissions
from check.models import Devices, DeviceMedia


class DevicePermission(permissions.BasePermission):
    """Разрешение на использование оборудования"""

    def has_object_permission(self, request, view, obj: Devices) -> bool:
        """
        ## Определяет, имеет ли пользователь "user" право взаимодействовать с оборудованием
        """
        user_available_groups = request.user.profile.devices_groups.all().values_list(
            "id", flat=True
        )
        if obj.group_id in user_available_groups:
            return True
        return False


class DeviceMediaPermission(permissions.BasePermission):
    """Разрешение на изменение медиафайла"""

    def has_object_permission(self, request, view, obj: DeviceMedia) -> bool:
        user_available_groups = request.user.profile.devices_groups.all().values_list(
            "id", flat=True
        )
        if request.user.is_staff and obj.device.group_id in user_available_groups:
            return True
        return False
