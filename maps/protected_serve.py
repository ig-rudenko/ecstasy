import re

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpRequest

from ecstasy_project.protected_serve import BaseServeLimitation


class MapMediaServeLimitation(BaseServeLimitation):
    """
    Запрещает просматривать файлы слоев для карты пользователям не имеющим возможность
    заходить в панель администратора и просматривать модель `Layers`
    """

    @staticmethod
    def check(request: WSGIRequest | HttpRequest, path, document_root=None, show_indexes=False) -> bool:
        if (
            request.user.is_superuser
            or request.user.has_perm("maps.view_layers")
            or request.user.has_perm("maps.add_layers")
            or request.user.has_perm("maps.change_layers")
            or request.user.has_perm("maps.delete_layers")
        ):
            return True
        if re.match("^map_layer_files", path):
            return False
        return True
