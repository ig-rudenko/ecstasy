from rest_framework.permissions import BasePermission

from maps.models import Maps


class MapPermission(BasePermission):
    def has_object_permission(self, request, view, obj: Maps) -> bool:
        # Проверяет, есть ли пользователь в списке пользователей карты.
        return obj.users.contains(request.user)
