"""
# Функции представления для взаимодействия с оборудованием
"""

import json
import random
import re
from functools import wraps
from datetime import datetime
import pexpect
import ping3

import django.db.utils
from django.urls import reverse
from django.http import (
    HttpResponseForbidden,
    JsonResponse,
    HttpResponseNotAllowed,
    HttpResponseRedirect,
    Http404,
)
from django.shortcuts import render, redirect, get_object_or_404, resolve_url
from django.db.models import Q
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required

from .paginator import ValidPaginator

from devicemanager.exceptions import (
    TelnetConnectionError,
    TelnetLoginError,
    UnknownDeviceError,
)
from net_tools.models import VlanName, DevicesInfo
from ecstasy_project import settings
from app_settings.models import LogsElasticStackSettings
from app_settings.models import ZabbixConfig
from devicemanager import *
from devicemanager.vendors.base import MACList
from . import models

try:
    # Устанавливаем конфигурацию для работы с devicemanager
    Config.set(ZabbixConfig.load())
except django.db.utils.OperationalError:
    pass


def log(
    user: models.User, model_device: (models.Devices, models.Bras), operation: str
) -> None:
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
        # Открытие файла журнала в режиме добавления и кодировка его в utf-8.
        with open(settings.LOG_FILE, "a", encoding="utf-8") as log_file:
            log_file.write(
                f"{datetime.now():%d.%m.%Y %H:%M:%S} "
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
        # Открытие файла логов в режиме добавления и с кодировкой utf-8.
        with open(settings.LOG_FILE, "a", encoding="utf-8") as log_file:
            log_file.write(
                f"{datetime.now():%d.%m.%Y %H:%M:%S} "
                f"| {user.username:<10} | {model_device.name} ({model_device.ip}) | {operation}\n"
            )
    else:
        # В базу
        models.UsersActions.objects.create(
            user=user, action=f"{model_device} | " + operation
        )
        # В файл
        with open(settings.LOG_FILE, "a", encoding="utf-8") as log_file:
            log_file.write(
                f"{datetime.now():%d.%m.%Y %H:%M:%S} "
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

    filter_by_group = request.GET.get("group", "")
    group_param = f"group={filter_by_group}" if filter_by_group else ""

    filter_by_vendor = request.GET.get("vendor", "")
    vendor_param = f"&vendor={filter_by_vendor}" if filter_by_vendor else ""

    # Группы оборудования, доступные текущему пользователю
    user_groups_ids = []
    user_groups_names = []
    for group in request.user.profile.devices_groups.all().values("id", "name"):
        user_groups_ids.append(group["id"])
        user_groups_names.append(group["name"])

    user_groups_names = {
        group: reverse("devices-list") + "?" + f"group={group}" + vendor_param
        for group in user_groups_names
    }

    # Вендоры оборудования, что доступны пользователю
    unique_vendors_list = sorted(
        list(
            set(
                d["vendor"]
                for d in models.Devices.objects.filter(
                    group__in=user_groups_ids
                ).values("vendor")
                if d["vendor"]
            )
        )
    )
    vendors = {
        g: reverse("devices-list") + "?" + group_param + f"&vendor={g}"
        for g in unique_vendors_list
    }

    full_url = reverse("devices-list") + "?" + group_param + vendor_param

    # Фильтруем запрос
    query = Q(group__in=user_groups_ids)
    if request.GET.get("s"):
        search_string = request.GET["s"].strip()
        query &= Q(ip__contains=search_string) | Q(name__icontains=search_string)

    # Фильтруем по группе
    if filter_by_group in user_groups_names:
        query &= Q(group__name=filter_by_group)

    # Фильтруем по вендору
    if filter_by_vendor:
        query &= Q(vendor=filter_by_vendor)

    devs = models.Devices.objects.filter(query)

    paginator = ValidPaginator(devs, per_page=50)
    page = paginator.validate_number(request.GET.get("page", 1))

    return render(
        request,
        "check/devices_list.html",
        {
            "devs": paginator.page(page),
            "search": request.GET.get("s", None),
            "total_count": paginator.count,
            "page": page,
            "num_pages": paginator.num_pages,
            "device_icon_number": random.randint(1, 5),
            "devices_groups": user_groups_names,
            "vendors": vendors,
            "full_url": full_url,
        },
    )


@login_required
def device_info(request, name: str):
    """
    ## Вывод главной информации об устройстве и его интерфейсов

    :param name: Название оборудования
    """

    model_dev = get_object_or_404(
        models.Devices, name=name
    )  # Получаем объект устройства из БД

    if not has_permission_to_device(model_dev, request.user):
        return HttpResponseForbidden()

    dev = Device(name)

    # Устанавливаем протокол для подключения
    dev.protocol = model_dev.port_scan_protocol
    # Устанавливаем community для подключения
    dev.snmp_community = model_dev.snmp_community
    dev.auth_obj = model_dev.auth_group  # Устанавливаем подключение
    dev.ip = model_dev.ip  # IP адрес
    ping = dev.ping()  # Оборудование доступно или нет

    # Сканируем интерфейсы в реальном времени?
    current_status = bool(request.GET.get("current_status", False)) and ping > 0

    # Вместе с VLAN?
    with_vlans = False if dev.protocol == "snmp" else request.GET.get("vlans") == "1"

    # Время последнего обновления интерфейсов
    last_interface_update = None
    if not current_status:
        try:
            if with_vlans:
                last_interface_update = DevicesInfo.objects.get(
                    ip=model_dev.ip
                ).vlans_date
            else:
                last_interface_update = DevicesInfo.objects.get(
                    ip=model_dev.ip
                ).interfaces_date
        except DevicesInfo.DoesNotExist:
            pass

    data = {
        "dev": dev,
        "ping": ping,
        # Создание URL-адреса для запроса журналов Kibana.
        "logs_url": LogsElasticStackSettings.load().query_kibana_url(device=model_dev),
        "zabbix_host_id": dev.zabbix_info.hostid,
        "current_status": current_status,
        "last_interface_update": last_interface_update,
        "perms": models.Profile.permissions_level.index(
            models.Profile.objects.get(user_id=request.user.id).permissions
        ),
    }

    if not request.GET.get("ajax", None):  # Если вызов НЕ AJAX
        return render(request, "check/device_info.html", data)

    # Собираем интерфейсы
    status = dev.collect_interfaces(vlans=with_vlans, current_status=current_status)

    model_update_fields = []  # Поля для обновлений, в случае изменения записи в БД

    # Если пароль неверный, то пробуем все по очереди, кроме уже введенного
    if "Неверный логин или пароль" in str(status):
        # Создаем список объектов авторизации
        all_auth = list(
            models.AuthGroup.objects.exclude(name=model_dev.auth_group.name)
            .order_by("id")
            .all()
        )

        # Собираем интерфейсы снова
        status = dev.collect_interfaces(
            vlans=with_vlans, current_status=current_status, auth_obj=all_auth
        )

        if status is None:  # Если статус сбора интерфейсов успешный
            # Необходимо перезаписать верный логин/пароль в БД, так как первая попытка была неудачной.
            # Смотрим объект у которого такие логин и пароль
            success_auth_obj = models.AuthGroup.objects.get(
                login=dev.success_auth["login"],
                password=dev.success_auth["password"],
            )

            # Указываем новый логин/пароль для этого устройства
            model_dev.auth_group = success_auth_obj
            # Добавляем это поле в список изменений
            model_update_fields.append("auth_group")

    # Обновляем модель устройства, взятую непосредственно во время подключения, либо с Zabbix
    # dev.zabbix_info.inventory.model обновляется на основе реальной модели при подключении
    if (
        dev.zabbix_info.inventory.model
        and dev.zabbix_info.inventory.model != model_dev.model
    ):
        model_dev.model = dev.zabbix_info.inventory.model
        model_update_fields.append("model")

    # Обновляем вендора оборудования, если он отличается от реального либо еще не существует
    if (
        dev.zabbix_info.inventory.vendor
        and dev.zabbix_info.inventory.vendor != model_dev.vendor
    ):
        model_dev.vendor = dev.zabbix_info.inventory.vendor
        model_update_fields.append("vendor")

    # Сохраняем изменения
    if model_update_fields:
        model_dev.save(update_fields=model_update_fields)

    # Обновляем данные в Zabbix
    dev.push_zabbix_inventory()

    # Сохраняем интерфейсы
    if current_status and dev.interfaces:
        try:
            current_device_info = DevicesInfo.objects.get(device_name=model_dev.name)
        except DevicesInfo.DoesNotExist:
            current_device_info = DevicesInfo.objects.create(
                ip=model_dev.ip, device_name=model_dev.name
            )

        if with_vlans:
            interfaces_to_save = [
                {
                    "Interface": line.name,
                    "Status": line.status,
                    "Description": line.desc,
                    "VLAN's": line.vlan,
                }
                for line in dev.interfaces
            ]
            current_device_info.vlans = json.dumps(interfaces_to_save)
            current_device_info.vlans_date = datetime.now()
            current_device_info.save(update_fields=["vlans", "vlans_date"])

        else:
            interfaces_to_save = [
                {
                    "Interface": line.name,
                    "Status": line.status,
                    "Description": line.desc,
                }
                for line in dev.interfaces
            ]
            current_device_info.interfaces = json.dumps(interfaces_to_save)
            current_device_info.interfaces_date = datetime.now()
            current_device_info.save(update_fields=["interfaces", "interfaces_date"])

    data = {
        "dev": dev,
        "interfaces": dev.interfaces,
        "ping": ping,
        "status": status,
        "current_status": current_status,
        "zabbix_host_id": dev.zabbix_info.hostid,
        "perms": models.Profile.permissions_level.index(
            models.Profile.objects.get(user_id=request.user.id).permissions
        ),
    }

    # Отправляем JSON, вызов AJAX
    return JsonResponse({"data": render_to_string("check/interfaces_table.html", data)})


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

    color_warning = "#d3ad23"  # Оранжевый
    color_success = "#08b736"  # Зеленый
    color_info = "#31d2f2"  # Голубой
    color_error = "#d53c3c"  # Красный
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
                "color": "#d3ad23",
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
    save_config: bool = request.POST.get("save") != "no"  # По умолчанию сохранять

    # У пользователя нет доступа к группе данного оборудования
    if not has_permission_to_device(model_dev, request.user):
        return JsonResponse(
            {
                "message": "Вы не имеете права управлять этим устройством",
                "status": "ERROR",
                "color": "#d53c3c",
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
        {"message": message, "status": f"Порт {status}", "color": color}
    )


# BRAS COMMAND
def send_command(session: pexpect, command: str) -> str:
    """
    ## Отправляем команду на BRAS

    :param session: Активная сессия с BRAS
    :param command: Команда
    :return: Результат команды
    """

    session.sendline(command)
    session.expect(command)
    result = ""
    while True:
        match = session.expect(
            [
                r"---- More ----|Are you sure to display some information",
                r"<BRAS\d>|\[BRAS\S+\]",
            ]
        )
        result += (
            session.before.decode("utf-8")
            .replace("\x1b[42D", "")
            .replace("?(Y/N)[Y]:", "")
        )
        if match:
            break  # Считали все данные, прерываем

        session.sendline(" ")  # Листаем дальше

    return result


@login_required
@permission(models.Profile.BRAS)
def show_session(request):
    """
    ## Смотрим сессию клиента
    """

    if (
        request.method == "GET"
        and request.GET.get("mac")
        and request.GET.get("device")
        and request.GET.get("port")
    ):
        mac_letters = re.findall(r"\w", request.GET["mac"])
        if len(mac_letters) == 12:

            mac = "{}{}{}{}-{}{}{}{}-{}{}{}{}".format(*mac_letters)

            brases = models.Bras.objects.all()
            user_info = {}
            errors = []

            if not request.GET.get("ajax"):
                # Если это асинхронный запрос, то отправляем html
                return render(
                    request,
                    "check/bras_info.html",
                    {
                        "mac": mac,
                        "result": user_info,
                        "port": request.GET["port"],
                        "device": request.GET["device"],
                        "desc": request.GET.get("desc"),
                        "errors": errors,
                    },
                )

            for bras in brases:
                try:
                    with pexpect.spawn(f"telnet {bras.ip}") as telnet:
                        telnet.expect(
                            ["Username", "Unable to connect", "Connection closed"],
                            timeout=10,
                        )
                        telnet.sendline(bras.login)

                        telnet.expect("[Pp]ass")
                        telnet.sendline(bras.password)

                        if telnet.expect(
                            [">", "password needs to be changed. Change now?"]
                        ):
                            telnet.sendline("N")

                        bras_output = send_command(
                            telnet, f"display access-user mac-address {mac}"
                        )
                        if "No online user!" not in bras_output:
                            user_index = re.findall(
                                r"User access index\s+:\s+(\d+)", bras_output
                            )
                            if user_index:
                                bras_output = send_command(
                                    telnet,
                                    f"display access-user user-id {user_index[0]} verbose",
                                )
                            user_info[bras.name] = bras_output
                except pexpect.TIMEOUT:
                    errors.append("Не удалось подключиться к " + bras.name)

                # Логи
                log(request.user, bras, f"display access-user mac-address {mac}")

            return render(
                request,
                "check/bras_table.html",
                {
                    "mac": mac,
                    "result": user_info,
                    "port": request.GET["port"],
                    "device": request.GET["device"],
                    "desc": request.GET.get("desc"),
                },
            )

    return redirect("/")


@login_required
@permission(models.Profile.BRAS)
def cut_user_session(request):
    """
    ## Сбрасываем сессию абонента по MAC адресу с помощью BRAS
    """

    status = "miss"

    # color_warning = '#d3ad23'
    color_success = "#08b736"
    color_error = "#d53c3c"
    status_color = color_error  # Значение по умолчанию

    if (
        request.method == "POST"
        and request.POST.get("mac")
        and request.POST.get("device")
        and request.POST.get("port")
    ):
        mac_letters = re.findall(r"\w", request.POST["mac"])

        dev = Device(request.POST["device"])
        model_dev = get_object_or_404(models.Devices, name=dev.name)

        if not has_permission_to_device(model_dev, request.user):
            return HttpResponseForbidden()

        # Если неверный MAC
        status = "invalid MAC"

        # Если мак верный и оборудование доступно
        if len(mac_letters) == 12 and dev.ping() > 0:

            mac = "{}{}{}{}-{}{}{}{}-{}{}{}{}".format(*mac_letters)

            brases = models.Bras.objects.all()

            status = ""  # Обновляем статус
            for bras in brases:
                try:
                    print(bras)
                    with pexpect.spawn(f"telnet {bras.ip}") as telnet:
                        telnet.expect(
                            ["Username", "Unable to connect", "Connection closed"],
                            timeout=20,
                        )
                        telnet.sendline(bras.login)

                        telnet.expect(r"[Pp]ass")
                        telnet.sendline(bras.password)

                        if telnet.expect(
                            [">", "password needs to be changed. Change now?"]
                        ):
                            telnet.sendline("N")

                        telnet.sendline("system-view")
                        telnet.sendline("aaa")
                        telnet.sendline(f"cut access-user mac-address {mac}")

                        # Логи
                        log(request.user, bras, f"cut access-user mac-address {mac}")

                except pexpect.TIMEOUT:
                    status += bras.name + " timeout\n"  # Кто был недоступен

            try:
                with model_dev.connect() as session:
                    # Перезагружаем порт без сохранения конфигурации
                    reload_port_status = session.reload_port(
                        request.POST["port"], save_config=False
                    )

                    status += reload_port_status
                    status_color = color_success  # Успех

                    # Логи
                    log(
                        request.user,
                        model_dev,
                        f'reload port {request.POST["port"]} \n{reload_port_status}',
                    )
            except (TelnetConnectionError, TelnetLoginError, UnknownDeviceError) as e:
                status = f"Сессия сброшена, но порт не был перезагружен! {e}"
                status_color = color_error

    return JsonResponse(
        {"message": status, "color": status_color, "status": "cut session"}
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
        status = "success"  # По умолчанию успешно

        try:
            with dev.connect() as session:
                if hasattr(session, "set_description"):
                    set_description_status = session.set_description(
                        port=port, desc=new_description
                    )
                    new_description = session.clear_description(new_description)

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
        request.method == "GET"
        and request.GET.get("device")
        and request.GET.get("port")
    ):
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
            except (TelnetConnectionError, TelnetLoginError, UnknownDeviceError):
                pass

        return JsonResponse(data)


@login_required
@permission(models.Profile.BRAS)
def change_adsl_profile(request) -> JsonResponse:
    """
    ## Изменяем профиль xDSL порта на другой

    Возвращаем {"status": status}

    :return: результат в формате JSON
    """

    port: str = request.POST.get("port")
    profile_index: str = request.POST.get("index")

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed!"}, status=403)

    if (
        not port
        or not profile_index
        or not profile_index.isdigit()
        or int(profile_index) <= 0
    ):
        return JsonResponse({"error": "Invalid data", "data": request.POST}, status=400)

    model_dev = get_object_or_404(models.Devices, name=request.POST.get("device_name"))

    if not ping3.ping(model_dev.ip, timeout=2):
        return JsonResponse({"error": "Device down"})

    try:
        # Подключаемся к оборудованию
        with model_dev.connect() as session:
            if hasattr(session, "change_profile"):
                # Если можно поменять профиль
                status = session.change_profile(port, int(profile_index))

                return JsonResponse({"status": status})

            else:  # Нельзя менять профиль для данного устройства
                return JsonResponse(
                    {"error": "Device can't change profile"}, status=400
                )

    except (TelnetLoginError, TelnetConnectionError, UnknownDeviceError) as e:
        return JsonResponse({"error": str(e)}, status=400)
