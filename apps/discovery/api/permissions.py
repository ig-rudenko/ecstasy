from rest_framework import permissions
from rest_framework.request import Request


class DiscoveryAdminPermission(permissions.BasePermission):
    """Разрешение на управление auto discovery."""

    def has_permission(self, request: Request, view) -> bool:
        """Проверить доступ пользователя к discovery API."""

        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.has_perm("auth.access_discovery")
