from rest_framework import permissions
from rest_framework.request import Request


class GatheringResultsPermission(permissions.BasePermission):
    """Разрешить чтение истории периодического сбора."""

    def has_permission(self, request: Request, view) -> bool:
        """Проверить наличие специального права или статуса суперпользователя."""

        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or user.has_perm("accounting.access_gathering_results"))
        )
