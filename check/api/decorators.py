from functools import wraps

import pexpect
from rest_framework.response import Response
from devicemanager.exceptions import UnknownDeviceError, TelnetLoginError, TelnetConnectionError


def device_connection(handler):
    """
    Декоратор, который оборачивает функцию-обработчик и перехватывает определенные
    исключения, связанные с ошибками подключения устройства, возвращая соответствующий ответ.
    """

    @wraps(handler)
    def wrapper(*args, **kwargs):
        try:
            return handler(*args, **kwargs)
        except pexpect.EOF:
            return Response({"error": "EOF при считывании данных с оборудования"}, status=500)
        except pexpect.TIMEOUT:
            return Response({"error": "Timeout при выполнении команды на оборудовании"}, status=500)
        except TelnetConnectionError:
            return Response({"error": "Telnet недоступен"}, status=500)
        except TelnetLoginError:
            return Response({"error": "Неверный Логин/Пароль"}, status=500)
        except UnknownDeviceError:
            return Response({"error": "Неизвестный тип оборудования"}, status=500)

    return wrapper
