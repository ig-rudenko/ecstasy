"""
# Функции представления для взаимодействия с оборудованием
"""

import re
from functools import wraps
import pexpect
import ping3

from django.http import (
    HttpResponseForbidden,
    JsonResponse,
    HttpResponseRedirect,
    Http404,
)
from django.shortcuts import render, get_object_or_404, resolve_url
from django.contrib.auth.decorators import login_required

from devicemanager.exceptions import (
    TelnetConnectionError,
    TelnetLoginError,
    UnknownDeviceError,
)
from devicemanager import Device
from ecstasy_project.settings import django_actions_logger
from . import models


def log(user: models.User, model_device: (models.Devices, models.Bras), operation: str):
    """
    ## Записывает логи о действиях пользователя

    :param user: Пользователь, который совершил действие
    :param model_device: Оборудование, по отношению к которому было совершено действие
    :param operation: Описание действия
    :return: None
    """

    # Проверка того, НЕ является ли пользователь экземпляром класса models.User
    # или model_device НЕ является экземпляром класса models.Devices или models.Bras,
    # или операция НЕ является строкой.
    if (
        not isinstance(user, models.User)
        or not isinstance(model_device, (models.Devices, models.Bras))
        or not isinstance(operation, str)
    ):
        django_actions_logger.info(
            f"| NO DB | {str(user):<10} | {str(model_device):<15} | {str(operation)}\n"
        )
        return

    # В базу
    # Получение максимальной длины поля «действие» в модели UsersActions.
    operation_max_length = models.UsersActions._meta.get_field("action").max_length
    if len(operation) > operation_max_length:
        operation = operation[:operation_max_length]

    # Проверка того, является ли model_device экземпляром класса models.Devices.
    if isinstance(model_device, models.Devices):
        models.UsersActions.objects.create(
            user=user, device=model_device, action=operation
        )
        # В файл
        django_actions_logger.info(
            f"| {user.username:<10} | {model_device.name} ({model_device.ip}) | {operation}\n"
        )

    else:
        # В базу
        models.UsersActions.objects.create(
            user=user, action=f"{model_device} | " + operation
        )
        # В файл
        django_actions_logger.info(
            f"| {user.username:<10} |  | {model_device} | {operation}\n"
        )


def has_permission_to_device(device_to_check: models.Devices, user: models.User):
    """
    ## Определяет, имеет ли пользователь "user" право взаимодействовать с оборудованием "device_to_check"
    """

    if device_to_check.group_id in [
        g["id"] for g in user.profile.devices_groups.all().values("id")
    ]:
        return True
    return False


def permission(required_perm=models.Profile.READ):
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
                return HttpResponseForbidden()  # Недостаточно прав

            # Уровень привилегий пользователя
            user_permission_level = all_permissions.index(
                request.user.profile.permissions
            )

            # Если суперпользователь или его уровень привилегий равен или выше требуемых
            if (
                request.user.is_superuser
                or all_permissions.index(required_perm) <= user_permission_level
            ):
                return func(request, *args, **kwargs)  # Выполняем функцию

            return HttpResponseForbidden()  # Недостаточно прав

        return _wrapper

    return decorator


def by_zabbix_hostid(request, hostid: str):
    """
    ## Преобразование идентификатора узла сети "host_id" Zabbix в URL ecstasy

    :param hostid: Идентификатор узла сети в Zabbix
    """

    dev = Device.from_hostid(hostid)
    if not dev:
        raise Http404

    # Ищем по имени
    found_dev = models.Devices.objects.filter(name=dev.name)
    if not found_dev.exists():
        # Или по IP
        found_dev = models.Devices.objects.filter(ip=dev.ip)

    if not found_dev.exists():
        # Не нашли оборудование
        raise Http404

    model_dev = found_dev.first()
    return HttpResponseRedirect(resolve_url("device_info", name=model_dev.name))


@login_required
def home(request):
    """
    ## Домашняя страница
    """

    return render(request, "home.html")


@login_required
def show_devices(request):
    """
    ## Список всех имеющихся устройств
    """

    return render(request, "check/devices.html")


@login_required
def device_info(request, name: str):
    """
    ## Вывод главной информации об устройстве и его интерфейсов
    """

    return render(request, "check/device_info.html", {"device_name": name})


@login_required
@permission(models.Profile.REBOOT)
def reload_port(request):
    """
    ## Изменяем состояния порта
    """

    color_warning = "#ffc107"  # Оранжевый
    color_success = "#198754"  # Зеленый
    color_info = "#0d6efd"  # Голубой
    color_error = "#dc3545"  # Красный
    color = color_success  # Значение по умолчанию

    # Если не суперпользователь, то нельзя изменять состояние определенных портов
    port_guard_pattern = (
        r"svsl|power_monitoring|[as]sw\d|dsl|co[pr]m|msan|core|cr\d|nat|mx-\d|dns|bras"
    )

    if not request.user.is_superuser and re.findall(
        port_guard_pattern, request.POST.get("desc", "").lower()
    ):
        return JsonResponse(
            {
                "message": "Запрещено изменять состояние данного порта!",
                "status": "WARNING",
                "color": color_warning,
            }
        )

    # Если неправильный метод или не все обязательные данные были переданы
    if (
        request.method != "POST"
        or not request.POST.get("port")
        or not request.POST.get("device")
        or not request.POST.get("status")
    ):
        return JsonResponse(
            {
                "message": f"Ошибка отправки данных {request.POST}",
                "color": color_error,
                "status": "ERROR",
            }
        )

    # dev = Device(request.POST["device"])
    model_dev = get_object_or_404(models.Devices, name=request.POST["device"])

    port: str = request.POST["port"]
    status: str = request.POST["status"]
    save_config: bool = request.POST.get("save") != "false"  # По умолчанию сохранять

    # У пользователя нет доступа к группе данного оборудования
    if not has_permission_to_device(model_dev, request.user):
        return JsonResponse(
            {
                "message": "Вы не имеете права управлять этим устройством",
                "status": "ERROR",
                "color": color_error,
            }
        )

    # Уровень привилегий пользователя
    user_permission_level = models.Profile.permissions_level.index(
        request.user.profile.permissions
    )

    # Если недостаточно привилегий для изменения статуса порта
    if user_permission_level < 2 and status in ["up", "down"]:
        # Логи
        log(
            request.user,
            model_dev,
            f'Tried to set port {port} ({request.POST.get("desc")}) to the {status} state, but was refused \n',
        )
        return JsonResponse(
            {
                "message": "У вас недостаточно прав, для изменения состояния порта!",
                "status": "WARNING",
                "color": color_warning,
            }
        )

    # Если оборудование Недоступно
    if ping3.ping(model_dev.ip) <= 0:
        return JsonResponse(
            {
                "message": "Оборудование недоступно!",
                "status": "WARNING",
                "color": color_warning,
            }
        )

    port_change_status = "Не выполнили действие"
    try:
        # Теперь наконец можем подключиться к оборудованию :)
        with model_dev.connect() as session:
            try:
                # Перезагрузка порта
                if status == "reload":
                    port_change_status = session.reload_port(
                        port=port, save_config=save_config
                    )
                    message = f"Порт {port} был перезагружен!"

                # UP and DOWN
                else:
                    port_change_status = session.set_port(
                        port=port, status=status, save_config=save_config
                    )
                    message = f"Порт {port} был переключен в состояние {status}!"

            except pexpect.TIMEOUT:
                message = "Timeout"
                color = color_error

    except TelnetConnectionError:
        message = "Telnet недоступен "
        color = color_error
    except TelnetLoginError:
        message = "Неверный Логин/Пароль "
        color = color_error
    except UnknownDeviceError:
        message = "Неизвестный тип оборудования "
        color = color_error

    if "Saved Error" in port_change_status:
        config_status = " Конфигурация НЕ была сохранена"
        color = color_error

    elif "Saved OK" in port_change_status:
        config_status = " Конфигурация была сохранена"

    elif "Without saving" in port_change_status:
        config_status = " Конфигурация НЕ была сохранена"
        color = color_info

    else:
        config_status = port_change_status

    message += config_status

    # Логи
    log(
        request.user,
        model_dev,
        f'{status} port {port} ({request.POST.get("desc")}) \n{port_change_status}',
    )

    return JsonResponse(
        {
            "message": message,
            "status": f"Порт {status}",
            "color": color,
        }
    )
