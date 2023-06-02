from functools import wraps

from .helpers import interface_normal_view


def validate_and_format_port(if_invalid_return=None, validator=None):
    """
    ## Базовый декоратор для проверки правильности порта на основе функции.

    :param if_invalid_return: Что нужно вернуть, если порт неверный.
    :param validator: Функция, для валидации порта, которая вернет его требуемое значение либо None,
     если порт неверный.
    """

    if if_invalid_return is None:
        if_invalid_return = "Неверный порт"

    def validate(func):
        @wraps(func)
        def wrapper(self, port, *args, **kwargs):
            port = validator(port)
            if not port:
                # Неверный порт
                return if_invalid_return

            # Вызываем метод
            return func(self, port, *args, **kwargs)

        return wrapper

    return validate


def validate_and_format_port_as_normal(if_invalid_return=None):
    """
    ## Декоратор для проверки правильности порта и форматирования его
    на основе функции `interface_normal_view`.

    Valid:
        "eth12" -> "Ethernet 12"

        "gi 1/0/1" -> "GigabitEthernet 1/0/1"

    :param if_invalid_return: Что нужно вернуть, если порт неверный.
    """
    return validate_and_format_port(
        if_invalid_return=if_invalid_return, validator=interface_normal_view
    )


def validate_and_format_port_only_digit(if_invalid_return=None):
    """
    ## Декоратор для проверки правильности только порта, указанного цифровыми символами.

    Valid:
        " 1" -> "1"

        "23" -> "23"

    :param if_invalid_return: Что нужно вернуть, если порт неверный.
    """
    return validate_and_format_port(
        if_invalid_return=if_invalid_return,
        validator=lambda port: port.strip() if port.strip().isdigit() else None,
    )
