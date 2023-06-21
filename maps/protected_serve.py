import re

from django.http import HttpRequest

from ecstasy_project.protected_serve import BaseServeLimitation


class MapMediaServeLimitation(BaseServeLimitation):
    """
    Запрещает просматривать файлы слоев для карты пользователям не имеющим возможность
    заходить в панель администратора и просматривать модель `Layers`
    """

    @staticmethod
    def check(request: HttpRequest, path, document_root=None, show_indexes=False) -> bool:
        has_permission = False
        for group in request.user.groups.all():
            has_permission = (
                group.permissions.filter(
                    codename__in=["add_layers", "change_layers", "delete_layers", "view_layers"]
                ).count()
                > 0
            )
            if has_permission:
                break

        if request.user and (request.user.is_superuser or has_permission):
            return True
        if re.match("^map_layer_files", path):
            return False
        return True
