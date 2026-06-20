from functools import wraps

from django.http import HttpResponse, HttpResponseForbidden

from . import models


def has_permission_to_device(device_to_check: models.Devices, user: models.User) -> bool:
    """
    ## Определяет, имеет ли пользователь "user" право взаимодействовать с оборудованием "device_to_check"
    """
    return bool(
        (device_to_check.group_id or 0) in user.profile.devices_groups.all().values_list("id", flat=True)
    )


def profile_permission(*required_perm: str):
    """
    ## Декоратор для определения прав пользователя

    :param required_perm: Profile device permission codename.
    """

    def decorator(func):
        @wraps(func)
        def _wrapper(request, *args, **kwargs):
            # Проверяем авторизацию пользователя
            if not request.user.is_authenticated:
                return HttpResponse(status=401)  # Неавторизованный

            # Если суперпользователь или у пользователя есть требуемое право.
            if request.user.is_superuser or any(
                request.user.profile.has_device_permission(permission) for permission in required_perm
            ):
                return func(request, *args, **kwargs)  # Выполняем функцию

            return HttpResponseForbidden()  # Недостаточно прав

        return _wrapper

    return decorator
