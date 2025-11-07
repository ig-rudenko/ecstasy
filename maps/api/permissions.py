from rest_framework.permissions import BasePermission

from maps.models import Maps


class MapPermission(BasePermission):
    def has_object_permission(self, request, view, obj: Maps) -> bool:
        # Проверяет, есть ли пользователь в списке пользователей карты.
        return request.user.is_superuser or obj.users.contains(request.user)


class LayerModelPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            return request.user.is_authenticated and request.user.has_perm("maps.add_layers")
        if request.method == "PUT":
            return request.user.is_authenticated and request.user.has_perm("maps.change_layers")
        if request.method == "DELETE":
            return request.user.is_authenticated and request.user.has_perm("maps.delete_layers")
        return request.user.is_authenticated and request.user.has_perm("maps.view_layers")
