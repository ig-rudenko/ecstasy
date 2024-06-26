from functools import wraps

import pexpect
from django.conf import settings
from requests import exceptions
from rest_framework.response import Response

from devicemanager.exceptions import BaseDeviceException


def except_connection_errors(handler):
    """
    Декоратор, который оборачивает функцию-обработчик и перехватывает определенные
    исключения, связанные с ошибками подключения устройства, возвращая соответствующий ответ.
    """

    @wraps(handler)
    def wrapper(*args, **kwargs):
        contact = f"Пишите на почту: {settings.CONTACT_EMAIL}"
        try:
            return handler(*args, **kwargs)
        except pexpect.EOF:
            return Response(
                {"error": f"EOF при считывании данных с оборудования. {contact}"},
                status=500,
            )
        except pexpect.TIMEOUT:
            return Response(
                {"error": f"Timeout при выполнении команды на оборудовании. {contact}"},
                status=500,
            )
        except (BaseDeviceException, exceptions.ConnectionError) as exc:
            return Response(
                {"error": f"{exc}. {contact}"},
                status=500,
            )

    return wrapper
