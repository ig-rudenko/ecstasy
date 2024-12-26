from functools import wraps

from django.http import HttpResponseForbidden, HttpResponse

from . import models


def has_permission_to_device(device_to_check: models.Devices, user: models.User):
    """
    ## Определяет, имеет ли пользователь "user" право взаимодействовать с оборудованием "device_to_check"
    """

    if device_to_check.group_id in user.profile.devices_groups.all().values_list("id", flat=True):
        return True
    return False


def profile_permission(required_perm=models.Profile.READ):
    """
    ## Декоратор для определения прав пользователя

    :param required_perm: "read", "reboot", "up_down", "bras"
    """

    all_permissions = models.Profile.permissions_level

    def decorator(func):
        @wraps(func)
        def _wrapper(request, *args, **kwargs):
            # Проверяем авторизацию пользователя
            if not request.user.is_authenticated:
                return HttpResponse(status=401)  # Неавторизованный

            required_perm_idx = all_permissions.index(required_perm)

            # Если суперпользователь или его уровень привилегий равен или выше требуемых
            if request.user.is_superuser or request.user.profile.perm_level >= required_perm_idx:
                return func(request, *args, **kwargs)  # Выполняем функцию

            return HttpResponseForbidden()  # Недостаточно прав

        return _wrapper

    return decorator
