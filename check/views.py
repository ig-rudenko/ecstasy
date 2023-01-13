"""
# Функции представления для взаимодействия с оборудованием
"""

import re
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
import pexpect
import ping3

import django.db.utils
from django.http import (
    HttpResponseForbidden,
    JsonResponse,
    HttpResponseNotAllowed,
    HttpResponseRedirect,
    Http404,
)
from django.shortcuts import render, redirect, get_object_or_404, resolve_url
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required

from devicemanager.exceptions import (
    TelnetConnectionError,
    TelnetLoginError,
    UnknownDeviceError,
)
from net_tools.models import VlanName
from app_settings.models import ZabbixConfig
from devicemanager import *
from devicemanager.vendors.base import MACList
from ecstasy_project.settings import django_actions_logger
from . import models
from .forms import BrassSessionForm, ADSLProfileForm

try:
    # Устанавливаем конфигурацию для работы с devicemanager
    Config.set(ZabbixConfig.load())
except django.db.utils.OperationalError:
    pass


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
            # Проверяем уровень привилегий
            user_permission = models.Profile.objects.get(
                user_id=request.user.id
            ).permissions

            # Если суперпользователь или его уровень привилегий равен или выше требуемых
            if request.user.is_superuser or all_permissions.index(
                required_perm
            ) <= all_permissions.index(user_permission):
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
    try:
        if dev and models.Devices.objects.get(name=dev.name):
            return HttpResponseRedirect(
                resolve_url("device_info", name=dev.name) + "?current_status=1"
            )

        raise Http404

    except (ValueError, TypeError, models.Devices.DoesNotExist) as exception:
        raise Http404 from exception


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

    :param name: Название оборудования
    """

    return render(request, "check/device_info.html", {"device_name": name})

def add_names_to_vlan(vlan_mac_list: MACList) -> list:
    """
    ## Добавляет к списку VLAN, MAC еще и название VLAN из таблицы соответствий
    """

    result = []
    vlan_passed = {}  # Словарь с VLAN, имена для которых уже найдены
    for vid, mac in vlan_mac_list:  # Смотрим VLAN и MAC

        # Если еще не искали такой VLAN
        if not vlan_passed.get(vid):
            # Ищем название VLAN'a
            try:
                vlan_name = VlanName.objects.get(vid=int(vid)).name
            except VlanName.DoesNotExist:
                vlan_name = ""
            # Добавляем в множество вланов, которые участвовали в поиске имени
            vlan_passed[vid] = vlan_name

        # Обновляем
        result.append([vid, mac, vlan_passed.get(vid)])

    return result


@login_required
@permission(models.Profile.READ)
def get_port_detail(request):
    """
    ## Смотрим информацию о порте
    """

    if (
        request.method == "GET"
        and request.GET.get("device")
        and request.GET.get("port")
    ):
        model_dev = get_object_or_404(models.Devices, name=request.GET.get("device"))

        if not has_permission_to_device(model_dev, request.user):
            return HttpResponseForbidden()

        dev = Device(request.GET["device"])
        dev.ip = model_dev.ip  # IP адрес

        data = {
            "dev": dev,
            "port": request.GET["port"],
            "desc": request.GET.get("desc", ""),
            "perms": models.Profile.permissions_level.index(
                request.user.profile.permissions
            ),
        }

        # Если оборудование недоступно
        if dev.ping() <= 0:
            return redirect("device_info", request.GET["device"])

        if not request.GET.get("ajax"):
            # ЛОГИ
            log(request.user, model_dev, f'show mac\'s port {data["port"]}')
            return render(request, "check/port_page.html", data)

        try:
            # Подключаемся к оборудованию
            with model_dev.connect() as session:

                data["macs"] = []  # Итоговый список
                vlan_passed = {}  # Словарь уникальных VLAN
                for vid, mac in session.get_mac(data["port"]):  # Смотрим VLAN и MAC

                    # Если еще не искали такой VLAN
                    if vid not in vlan_passed:
                        # Ищем название VLAN'a
                        try:
                            vlan_name = VlanName.objects.get(vid=int(vid)).name
                        except (ValueError, VlanName.DoesNotExist):
                            vlan_name = ""
                        # Добавляем в множество вланов, которые участвовали в поиске имени
                        vlan_passed[vid] = vlan_name

                    # Обновляем
                    data["macs"].append([vid, mac, vlan_passed[vid]])

                # Отправляем JSON, если вызов AJAX = mac
                if request.GET.get("ajax") == "mac":
                    macs_tbody = render_to_string("check/macs_table.html", data)
                    return JsonResponse({"macs": macs_tbody})

                data["port_info"] = session.get_port_info(data["port"])

                data["port_type"] = session.get_port_type(data["port"])

                data["port_config"] = session.get_port_config(data["port"])

                data["port_errors"] = session.get_port_errors(data["port"])

                if hasattr(session, "virtual_cable_test"):
                    data["cable_test"] = "has"

        except (TelnetConnectionError, TelnetLoginError, UnknownDeviceError):
            pass

        if request.GET.get("ajax") == "all":
            # Отправляем все собранные данные
            data["macs"] = render_to_string("check/macs_table.html", data)
            del data["dev"]
            del data["perms"]
            return JsonResponse(data)

    return HttpResponseNotAllowed(["GET"])


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

    dev = Device(request.POST["device"])
    model_dev = get_object_or_404(models.Devices, name=dev.name)

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
    if dev.ping() <= 0:
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


def get_user_session(bras: models.Bras, mac: str, user_info: dict, errors: list):
    """
    ## Получает сеанс пользователя для заданного MAC-адреса.

    :param bras: объект Bras, к которому подключается пользователь
    :param mac: мак адрес пользователя
    :param user_info: dict, содержащий информацию о сессии
    :param errors: список ошибок, которые произошли во время сеанса
    """

    try:
        with bras.connect() as session:
            bras_output = session.send_command(f"display access-user mac-address {mac}")
            if "No online user!" not in bras_output:
                user_index = re.findall(r"User access index\s+:\s+(\d+)", bras_output)

                if user_index:
                    bras_output = session.send_command(
                        f"display access-user user-id {user_index[0]} verbose",
                    )

            user_info[bras.name] = bras_output

    except TelnetConnectionError:
        errors.append("Не удалось подключиться к " + bras.name)
    except TelnetLoginError:
        errors.append("Неверный Логин/Пароль " + bras.name)
    except UnknownDeviceError:
        errors.append("Неизвестные тип оборудования " + bras.name)


@login_required
@permission(models.Profile.BRAS)
def show_session(request):
    """
    ## Смотрим сессию клиента
    """

    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    form = BrassSessionForm(request.GET)
    # Проверка правильности формы.
    if not form.is_valid():
        raise Http404

    # Берем mac-адрес из формы и форматируем его в строку вида `aaaa-bbbb-cccc`.
    mac = models.Bras.format_mac(form.cleaned_data["mac"])

    brases = models.Bras.objects.all()
    user_info = {}
    errors = []

    response_dict = {
        "mac": mac,
        "result": user_info,
        "port": form.cleaned_data["port"],
        "device": form.cleaned_data["device"],
        "desc": form.cleaned_data.get("desc"),
        "errors": errors,
    }

    if not form.cleaned_data["ajax"]:
        # Если это не ajax запрос, то отправляем html
        return render(request, "check/bras_info.html", response_dict)

    with ThreadPoolExecutor() as executor:
        for bras in brases:
            # Приведенный выше код создает пул потоков,
            # а затем отправляет функцию get_user_session в пул потоков.
            executor.submit(get_user_session, bras, mac, user_info, errors)
            # Логи
            log(request.user, bras, f"display access-user mac-address {mac}")

    return render(request, "check/bras_table.html", response_dict)


@login_required
@permission(models.Profile.BRAS)
def cut_user_session(request):
    """
    ## Сбрасываем сессию абонента по MAC адресу с помощью BRAS
    """

    color_warning = "#d3ad23"
    color_success = "#08b736"
    color_error = "#d53c3c"

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    form = BrassSessionForm(request.POST)

    # Проверка правильности формы.
    if not form.is_valid():
        return JsonResponse(
            {
                "message": "Invalid data",
                "color": color_error,
                "status": "Ошибка",
            },
            status=400,
        )

    # Получение объекта устройства из базы данных.
    model_dev = get_object_or_404(models.Devices, name=form.cleaned_data["device"])

    # Проверка наличия у пользователя прав доступа к устройству.
    if not has_permission_to_device(model_dev, request.user):
        return HttpResponseForbidden()

    # Берем mac-адрес из формы и форматируем его в строку вида `aaaa-bbbb-cccc`.
    mac = models.Bras.format_mac(form.cleaned_data["mac"])
    brases = models.Bras.objects.all()

    status = ""
    for bras in brases:
        try:
            with bras.connect() as session:
                session.send_command("system-view")
                session.send_command("aaa")
                session.send_command(f"cut access-user mac-address {mac}")

                # Логи
                log(request.user, bras, f"cut access-user mac-address {mac}")

        except pexpect.TIMEOUT:
            status += bras.name + " timeout\n"  # Кто был недоступен

    try:
        with model_dev.connect() as session:
            # Перезагружаем порт без сохранения конфигурации
            reload_port_status = session.reload_port(
                form.cleaned_data["port"], save_config=False
            )

            status += reload_port_status
            status_color = color_success  # Успех

            # Логи
            log(
                request.user,
                model_dev,
                f"reload port {form.cleaned_data['port']} \n" f"{reload_port_status}",
            )

    except (TelnetConnectionError, TelnetLoginError, UnknownDeviceError) as e:
        status = f"Сессия сброшена, но порт не был перезагружен! {e}"
        status_color = color_warning

    return JsonResponse(
        {
            "message": status,
            "color": status_color,
            "status": "Сессия сброшена",
        }
    )


@login_required
@permission(models.Profile.REBOOT)
def set_description(request):
    """
    ## Изменяем описание на порту у оборудования
    """

    if request.method != "POST":
        return HttpResponseNotAllowed(permitted_methods=["POST"])

    if request.POST.get("device_name") and request.POST.get("port"):
        dev = get_object_or_404(models.Devices, name=request.POST.get("device_name"))

        new_description = request.POST.get("description")
        port = request.POST.get("port")

        max_length = 64  # По умолчанию максимальная длина описания 64 символа

        try:
            with dev.connect() as session:
                if hasattr(session, "set_description"):
                    set_description_status = session.set_description(
                        port=port, desc=new_description
                    )
                    new_description = session.clear_description(new_description)
                    status = "success"

                else:
                    set_description_status = "Недоступно для данного оборудования"
                    status = "warning"  # Описание цветовой палитры для bootstrap

        except (TelnetConnectionError, TelnetLoginError, UnknownDeviceError) as e:
            return JsonResponse(
                {
                    "status": "danger",
                    "info": str(e),
                }
            )

        if "Неверный порт" in set_description_status:
            status = "warning"

        # Проверяем результат изменения описания
        if "Max length" in set_description_status:
            # Описание слишком длинное.
            # Находим в строке "Max length:32" число "32"
            max_length = set_description_status.split(":")[1]
            if max_length.isdigit():
                max_length = int(max_length)
            else:
                max_length = 32
            set_description_status = (
                f"Слишком длинное описание! Укажите не более {max_length} символов."
            )
            status = "warning"

        return JsonResponse(
            {
                "status": status,
                "description": new_description,
                "info": set_description_status,
                "max_length": max_length,
            }
        )

    return JsonResponse(
        {
            "status": "danger",
            "info": "Invalid data",
        }
    )


@login_required
@permission(models.Profile.READ)
def start_cable_diag(request) -> (JsonResponse, HttpResponseForbidden):
    """
    ## Запускаем диагностику кабеля на порту
    """

    if (
        request.method != "GET"
        or not request.GET.get("device")
        or not request.GET.get("port")
    ):
        return JsonResponse({}, status=400)

    model_dev = get_object_or_404(models.Devices, name=request.GET["device"])
    dev = Device(request.GET["device"], zabbix_info=False)

    if not has_permission_to_device(model_dev, request.user):
        return HttpResponseForbidden()

    data = {}
    # Если оборудование доступно
    if dev.ping() > 0:
        try:
            with model_dev.connect() as session:
                if hasattr(session, "virtual_cable_test"):
                    cable_test = session.virtual_cable_test(request.GET["port"])
                    if cable_test:  # Если имеются данные
                        data["cable_test"] = cable_test
        except (TelnetConnectionError, TelnetLoginError, UnknownDeviceError) as e:
            return JsonResponse({}, status=400)

    return JsonResponse(data)


@login_required
@permission(models.Profile.BRAS)
def change_adsl_profile(request) -> JsonResponse:
    """
    ## Изменяем профиль xDSL порта на другой

    Возвращаем {"status": status} или {"error": error}

    :return: результат в формате JSON
    """

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed!"}, status=405)

    form = ADSLProfileForm(request.POST)

    if not form.is_valid():
        return JsonResponse({"error": "Invalid data", "data": request.POST}, status=400)

    model_dev = get_object_or_404(models.Devices, name=form.cleaned_data["device_name"])

    if not ping3.ping(model_dev.ip, timeout=2):
        return JsonResponse({"error": "Device down"})

    try:
        # Подключаемся к оборудованию
        with model_dev.connect() as session:
            if hasattr(session, "change_profile"):
                # Если можно поменять профиль
                status = session.change_profile(
                    form.cleaned_data["port"], form.cleaned_data["index"]
                )

                return JsonResponse({"status": status})

            else:  # Нельзя менять профиль для данного устройства
                return JsonResponse(
                    {"error": "Device can't change profile"}, status=400
                )

    except (TelnetLoginError, TelnetConnectionError, UnknownDeviceError) as e:
        return JsonResponse({"error": str(e)}, status=400)
