from typing import List

from django.http import HttpResponseForbidden, HttpRequest
from django.views.static import serve


class BaseServeLimitation:
    @staticmethod
    def check(request, path, document_root=None, show_indexes=False) -> bool:
        return True


class LoginRequiredLimitation(BaseServeLimitation):
    """
    Проверяет, аутентифицирован ли пользователь, прежде чем обслуживать запрос.
    """

    @staticmethod
    def check(request: HttpRequest, path, document_root=None, show_indexes=False) -> bool:
        if request.user and request.user.is_authenticated:
            return True
        return False


class ProtectedServe:
    """
    Проверяет наличие ограничений перед обслуживанием файлов (static, media)
    и возвращает сообщение об ошибке, если доступ запрещен.
    """

    def __init__(self):
        self._limitations: List[BaseServeLimitation] = []

    def add_limitation(self, limitation: BaseServeLimitation):
        self._limitations.append(limitation)

    def serve(self, request, path, document_root=None, show_indexes=False):
        """
        Эта функция проверяет наличие ограничений и обслуживает файл,
         если у пользователя есть необходимые разрешения, в противном случае возвращает 403.

        :param request: Объект запроса HTTP, который содержит информацию о запросе клиента,
         например запрошенный URL-адрес, заголовки и данные.
        :param path: Относительный путь к запрошенному файлу в корневом каталоге документа
        :param document_root: Параметр document_root — это строка, указывающая каталог, из которого следует обслуживать
         статические файлы. Это корневой каталог статических файлов, которые будут обслуживаться сервером. Например, если
         статические файлы расположены в каталоге "/var/www/static/", то для document_root следует установить значение "/
        :param show_indexes: Логическое значение, определяющее, следует ли отображать индекс каталога, если запрошенный
         URL-адрес является каталогом. Если установлено значение True, будет отображаться индекс каталога.
         Если установлено значение False, вместо этого будет возвращена ошибка 404, defaults to False (optional)
        :return: объект ответа HTTP. Если запрос пройдет все проверки ограничений, он вернет результат функции `serve` с
         заданными параметрами. В противном случае он вернет ответ HTTP 403 Forbidden.
        """

        for limitation in self._limitations:
            if not limitation.check(request, path, document_root, show_indexes):
                return HttpResponseForbidden("У вас нет прав для просмотра данного файла")
        return serve(request, path, document_root, show_indexes)


protected_serve = ProtectedServe()
