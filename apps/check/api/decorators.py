from functools import wraps

import pexpect
from django.conf import settings
from requests import exceptions

from devicemanager.exceptions import BaseDeviceException
from ecstasy_project.error_handler import DeviceConnectionProblem


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
        except pexpect.EOF as exc:
            raise DeviceConnectionProblem(
                {
                    "detail": f"EOF при считывании данных с оборудования. {contact}",
                    "reason": "eof",
                }
            ) from exc
        except pexpect.TIMEOUT as exc:
            raise DeviceConnectionProblem(
                {
                    "detail": f"Timeout при выполнении команды на оборудовании. {contact}",
                    "reason": "timeout",
                }
            ) from exc
        except (BaseDeviceException, exceptions.ConnectionError) as exc:
            raise DeviceConnectionProblem(
                {
                    "detail": f"{exc}. {contact}",
                    "reason": exc.__class__.__name__,
                }
            ) from exc

    return wrapper
