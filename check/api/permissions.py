from rest_framework import permissions
from check.models import Devices


class DevicePermission(permissions.BasePermission):
    """Разрешение на использование оборудования"""

    def has_object_permission(self, request, view, obj: Devices):
        """
        ## Определяет, имеет ли пользователь "user" право взаимодействовать с оборудованием
        """
        user_available_groups = request.user.profile.devices_groups.all().values("id")
        if obj.group_id in [g["id"] for g in user_available_groups]:
            return True
        return False
