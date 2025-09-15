from functools import wraps
from typing import Callable, Optional, Any

from django.core.cache import cache


def cached(
    timeout: int,
    *,
    key: str | Callable[..., str] | None = None,
    variable_positions: Optional[list[int]] = None,
    delimiter: str = ":",
) -> Callable[..., Any]:
    """
    Декоратор кэширования функции.

    :param timeout: Время жизни кэш.
    :param key: Ключ кэша, если не указан будет взято имя функции.
    :param variable_positions: Список позиций аргументов, которые будут добавлены в ключ через str().
    :param delimiter: Разделитель позиций аргументов.

    :return: Декоратор функции.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if callable(key):
                cache_key = key(*args, **kwargs)
            else:
                cache_key: str = key if key is not None else func.__name__

            # Добавляем в название ключа значение аргументов
            if not callable(key) and variable_positions is not None:
                for pos in variable_positions:
                    if len(args) >= pos:
                        cache_key += delimiter + str(args[pos - 1])
                    elif len(kwargs) >= pos - len(args):
                        values = list(kwargs.values())
                        cache_key += delimiter + str(values[pos - len(args) - 1])

            value = cache.get(cache_key)
            if value is not None:
                return value
            value = func(*args, **kwargs)
            cache.set(cache_key, value, timeout)
            return value

        return wrapper

    return decorator
