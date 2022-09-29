import json

import requests
from django.shortcuts import render, redirect, get_object_or_404, resolve_url
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseNotAllowed, HttpResponseRedirect, Http404
from django.db.models import Q
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from ecstasy_project import settings
from . import models
from devicemanager import *

from datetime import datetime
import pexpect
import re
from django.contrib.auth.decorators import login_required
from configparser import ConfigParser

Config.set(settings.ZABBIX_CONFIG_FILE)


def log(user: models.User, model_device: (models.Devices, models.Bras), operation: str):

    if not isinstance(user, models.User) or not isinstance(model_device, (models.Devices, models.Bras)) \
            or not isinstance(operation, str):
        with open(settings.LOG_FILE, 'a') as log_file:
            log_file.write(
                f'{datetime.now():%d.%m.%Y %H:%M:%S} '
                f'| NO DB | {str(user):<10} | {str(model_device):<15} | {str(operation)}\n'
            )
        return

    # В базу
    operation_max_length = models.UsersActions._meta.get_field('action').max_length
    if len(operation) > operation_max_length:
        operation = operation[:operation_max_length]

    if isinstance(model_device, models.Devices):
        models.UsersActions.objects.create(
            user=user,
            device=model_device,
            action=operation
        )
        # В файл
        with open(settings.LOG_FILE, 'a') as log_file:
            log_file.write(
                f'{datetime.now():%d.%m.%Y %H:%M:%S} '
                f'| {user.username:<10} | {model_device.name} ({model_device.ip}) | {operation}\n'
            )
    else:
        models.UsersActions.objects.create(
            user=user,
            action=f"{model_device} | " + operation
        )
        # В файл
        with open(settings.LOG_FILE, 'a') as log_file:
            log_file.write(
                f'{datetime.now():%d.%m.%Y %H:%M:%S} '
                f'| {user.username:<10} |  | {model_device} | {operation}\n'
            )


def has_permission_to_device(device_to_check: models.Devices, user):
    if device_to_check.group_id in [g['id'] for g in user.profile.devices_groups.all().values('id')]:
        return True
    return False


def permission(perm=None):
    p = models.Profile.permissions_level

    def decorator(func):
        def _wrapper(request, *args, **kwargs):
            # Проверяем уровень привилегий
            if request.user.is_superuser or \
                    p.index(perm) <= p.index(models.Profile.objects.get(user_id=request.user.id).permissions):
                return func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden()
        return _wrapper

    return decorator


def by_zabbix_hostid(request, hostid):
    dev = Device.from_hostid(hostid)
    try:
        if dev and models.Devices.objects.get(name=dev.name):
            return HttpResponseRedirect(
                resolve_url('device_info', name=dev.name) + '?current_status=1'
            )
        else:
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    except (ValueError, TypeError, models.Devices.DoesNotExist):
        if request.META.get('HTTP_REFERER'):
            return HttpResponseRedirect(request.META.get('HTTP_REFERER') + '/zabbix')
        else:
            raise Http404


@login_required
def show_devices(request):
    p = request.GET.get('page', 1)
    try:
        p = int(p)
    except (ValueError, TypeError):
        p = 1

    # Группы оборудования, доступные текущему пользователю
    user_groups = [g['id'] for g in request.user.profile.devices_groups.all().values('id')]

    if request.GET.get('s'):
        s = request.GET['s'].strip()
        query = (Q(ip__contains=s) | Q(name__icontains=s))
    else:
        query = Q()

    devs = models.Devices.objects.filter(Q(group__in=user_groups) & query)

    paginator = Paginator(devs, per_page=50)

    if p < 1:
        p = 1
    elif p > paginator.num_pages:
        p = paginator.num_pages

    return render(
        request, 'check/devices_list.html',
        {'devs': paginator.page(p), 'search': request.GET.get('s'), 'page': p, 'num_pages': paginator.num_pages}
    )


@login_required
def device_info(request, name):
    print('device info')
    model_dev = get_object_or_404(models.Devices, name=name)  # Получаем объект устройства из БД

    if not has_permission_to_device(model_dev, request.user):
        return HttpResponseForbidden()

    dev = Device(name)
    dev.protocol = model_dev.port_scan_protocol  # Устанавливаем протокол для подключения
    dev.snmp_community = model_dev.snmp_community  # Устанавливаем community для подключения
    dev.auth_obj = model_dev.auth_group  # Устанавливаем подключение
    ping = dev.ping()  # Оборудование доступно или нет

    # Сканируем интерфейсы в реальном времени?
    current_status = bool(request.GET.get('current_status', False)) and ping

    data = {
        'dev': dev,
        'ping': ping,
        'zabbix_host_id': dev.zabbix_info.hostid,
        'current_status': current_status,
        'perms': models.Profile.permissions_level.index(models.Profile.objects.get(user_id=request.user.id).permissions)
    }

    if not request.GET.get('ajax', None):  # Eсли вызов НЕ AJAX
        return render(request, 'check/device_info.html', data)

    # Вместе с VLAN?
    with_vlans = False if dev.protocol == 'snmp' else request.GET.get('vlans') == '1'

    # Собираем интерфейсы
    status = dev.collect_interfaces(vlans=with_vlans, current_status=current_status)

    model_update_fields = []  # Поля для обновлений, в случае изменения записи в БД

    # Если пароль неверный, то пробуем все по очереди, кроме уже введенного
    if 'Неверный логин или пароль' in str(status):

        # Создаем список объектов авторизации
        al = list(models.AuthGroup.objects.exclude(name=model_dev.auth_group.name).order_by('id').all())

        # Собираем интерфейсы снова
        status = dev.collect_interfaces(vlans=with_vlans, current_status=current_status, auth_obj=al)

        if status is None:  # Если статус сбора интерфейсов успешный
            # Необходимо перезаписать верный логин/пароль в БД, так как первая попытка была неудачной
            try:
                # Смотрим объект у которого такие логин и пароль
                a = models.AuthGroup.objects.get(login=dev.success_auth['login'], password=dev.success_auth['password'])

            except (TypeError, ValueError, models.AuthGroup.DoesNotExist):
                # Если нет такого объекта, значит нужно создать
                a = models.AuthGroup.objects.create(
                    name=dev.success_auth['login'], login=dev.success_auth['login'], password=dev.success_auth['password'],
                    secret=dev.success_auth['privilege_mode_password']
                )

            model_dev.auth_group = a  # Указываем новый логин/пароль для этого устройства
            model_update_fields.append('auth_group')  # Добавляем это поле в список изменений

    # Обновляем модель устройства, взятую непосредственно во время подключения, либо с Zabbix
    # dev.zabbix_info.inventory.model обновляется на основе реальной модели при подключении
    if dev.zabbix_info.inventory.model and dev.zabbix_info.inventory.model != model_dev.model:
        model_dev.model = dev.zabbix_info.inventory.model
        model_update_fields.append('model')

    # Обновляем вендора оборудования, если он отличается от реального либо еще не существует
    if dev.zabbix_info.inventory.vendor and dev.zabbix_info.inventory.vendor != model_dev.vendor:
        model_dev.vendor = dev.zabbix_info.inventory.vendor
        model_update_fields.append('vendor')

    # Сохраняем изменения
    if model_update_fields:
        model_dev.save(update_fields=model_update_fields)

    # Отправляем собранные интерфейсы через REST API
    if current_status:
        if with_vlans:
            interfaces_to_save = [
                {
                    "Interface": line.name,
                    "Status": line.status,
                    "Description": line.desc,
                    "VLAN's": line.vlan
                } for line in dev.interfaces
            ]

        else:
            interfaces_to_save = [
                {
                    "Interface": line.name,
                    "Status": line.status,
                    "Description": line.desc
                } for line in dev.interfaces
            ]
        with open('logs', 'a') as f:
            f.write(f'{interfaces_to_save}\n')

        # Отправляем
        url = Config.INTERFACE_API_URL
        url += "vlans/" if with_vlans else 'interfaces/'
        resp = requests.post(
            url,
            headers={"api-key": Config.INTERFACE_API_KEY},
            data={
                'interfaces': json.dumps(interfaces_to_save),
                'dev': dev.name
            }
        )
        with open('logs', 'a') as f:
            f.write(f'{resp.status_code} {resp.text}\n')
            print(resp.status_code, resp.text)

    data = {
        'dev': dev,
        'interfaces': dev.interfaces,
        'ping': ping,
        'status': status,
        'current_status': current_status,
        'zabbix_host_id': dev.zabbix_info.hostid,
        'perms': models.Profile.permissions_level.index(models.Profile.objects.get(user_id=request.user.id).permissions)
    }

    # Отправляем JSON, вызов AJAX
    return JsonResponse({
        'data': render_to_string('check/interfaces_table.html', data)
    })


@login_required
@permission(models.Profile.READ)
def get_logs(request, dev_name):
    model_dev = models.Devices.objects.get(name=dev_name)

    if request.GET.get('ajax', None):
        dev = Device(dev_name)
        dev.protocol = model_dev.port_scan_protocol
        dev.snmp_community = model_dev.snmp_community
        dev.auth_obj = model_dev.auth_group

        with dev.connect() as conn:
            if hasattr(conn, 'get_logs'):
                logs = conn.get_logs()
            else:
                logs = 'Не поддерживается просмотр логов для данного устройства'
        return JsonResponse({
            'logs': logs
        })

    else:
        return render(request, 'check/logs.html', {"dev": model_dev})


@login_required
@permission(models.Profile.READ)
def get_port_mac(request):
    """Смотрим MAC на порту"""

    # Стороннее приложение для поиска по маку
    parser = ConfigParser()
    parser.read(f"{settings.BASE_DIR}/zabbix_conf")
    mac_finder_app_url = parser.get('MAC', 'finder_url')

    if request.method == 'GET' and request.GET.get('device') and request.GET.get('port'):
        model_dev = get_object_or_404(models.Devices, name=request.GET.get('device'))

        if not has_permission_to_device(model_dev, request.user):
            return HttpResponseForbidden()

        dev = Device(request.GET['device'])

        data = {
            'dev': dev,
            'port': request.GET.get('port'),
            'desc': request.GET.get('desc'),
            'perms': models.Profile.permissions_level.index(request.user.profile.permissions),
            'mac_finder_url': mac_finder_app_url or None
        }

        if dev.ping():
            if not request.GET.get('ajax'):
                # ЛОГИ
                log(request.user, model_dev, f'show mac\'s port {data["port"]}')
                return render(request, 'check/mac_list.html', data)

            with dev.connect(protocol=model_dev.cmd_protocol, auth_obj=model_dev.auth_group) as session:
                data['macs'] = session.get_mac(data['port'])

                # Отправляем JSON, если вызов AJAX = mac
                if request.GET.get('ajax') == 'mac':
                    macs_tbody = render_to_string('check/macs_table.html', data)
                    return JsonResponse({
                        'macs': macs_tbody
                    })

                if hasattr(session, 'get_port_info'):
                    data['port_info'] = session.get_port_info(data['port'])

                if hasattr(session, 'port_type'):
                    data['port_type'] = session.port_type(data['port'])

                if hasattr(session, 'port_config'):
                    data['port_config'] = session.port_config(data['port'])

                if hasattr(session, 'get_port_errors'):
                    data['port_errors'] = session.get_port_errors(data['port'])

                if request.GET.get('ajax') == 'all':
                    data['macs'] = render_to_string('check/macs_table.html', data)
                    del data['dev']
                    del data['perms']
                    return JsonResponse(data)

        return redirect('device_info', request.GET['device'])

    return HttpResponseNotAllowed(['GET'])


@login_required
@permission(models.Profile.REBOOT)
def reload_port(request):
    """Изменяем состояния порта"""

    color_warning = '#d3ad23'
    color_success = '#08b736'
    color_error = '#d53c3c'
    color = color_success  # Значение по умолчанию

    if re.findall(r'svsl|power_monitoring|[as]sw\d|dsl|co[pr]m|msan|core|cr\d|nat|mx-\d|dns|bras',
                  request.POST.get('desc', '').lower()) and not request.user.is_superuser:
        return JsonResponse({
            'message': f'Запрещено изменять состояние данного порта!',
            'status': 'WARNING',
            'color': '#d3ad23'
        })
    print(request.POST, request.user)

    if request.method == 'POST' and request.POST.get('port') and request.POST.get('device') and request.POST.get(
            'status'):

        dev = Device(request.POST['device'])
        model_dev = get_object_or_404(models.Devices, name=dev.name)
        dev.protocol = model_dev.cmd_protocol

        port = request.POST['port']
        status = request.POST['status']

        # У пользователя нет доступа к группе данного оборудования
        if not has_permission_to_device(model_dev, request.user):
            return JsonResponse({
                'message': f'Вы не имеете права управляет этим устройством',
                'status': 'ERROR',
                'color': '#d53c3c'
            })

        user_permission_level = models.Profile.permissions_level.index(request.user.profile.permissions)

        if dev.ping():
            with dev.connect(protocol=model_dev.cmd_protocol, auth_obj=model_dev.auth_group) as session:
                # Перезагрузка
                if status == 'reload':
                    try:
                        s = session.reload_port(port)
                        message = f'Порт {port} был перезагружен!'
                    except pexpect.TIMEOUT:
                        message = 'Timeout'
                        color = color_error
                # UP and DOWN
                elif user_permission_level >= 2 and status in ['up', 'down']:
                    try:
                        s = session.set_port(port, status=status)
                        message = f'Порт {port} был переключен в состояние {status}!'
                    except pexpect.TIMEOUT:
                        message = 'Timeout'
                        color = color_error
                # Нет прав
                else:
                    # Логи
                    log(request.user, model_dev, f'Tried to set port {port} ({request.POST.get("desc")})'
                                                 f' to the {status} state, but was refused \n'
                        )
                    return JsonResponse({
                        'message': f'У вас недостаточно прав, для изменения состояния порта!',
                        'status': 'WARNING',
                        'color': color_warning
                    })

            if 'Saved Error' in s:
                config_status = ' Конфигурация НЕ была сохранена'
                color = color_error

            elif 'Saved OK' in s:
                config_status = ' Конфигурация была сохранена'

            else:
                config_status = s

            message += config_status

            # Логи
            log(request.user, model_dev, f'{status} port {port} ({request.POST.get("desc")}) \n{s}')

            return JsonResponse({
                'message': message,
                'status': '',
                'color': color
            })

        return JsonResponse({
            'message': f'Оборудование недоступно!',
            'status': 'WARNING',
            'color': color_warning
        })

    return JsonResponse({
        'message': f'Ошибка отправки данных {request.POST}',
        'color': color_error,
        'status': 'ERROR'
    })


# BRAS COMMAND
def send_command(session: pexpect, command):
    session.sendline(command)
    session.expect(command)
    result = ''
    while True:
        match = session.expect(
            [r'---- More ----|Are you sure to display some information', r'<BRAS\d>|\[BRAS\S+\]']
        )
        result += session.before.decode('utf-8').replace('\x1b[42D', '').replace('?(Y/N)[Y]:', '')
        if match:
            break
        else:
            session.sendline(' ')
    return result


@login_required
@permission(models.Profile.BRAS)
def parse_mac(request):
    """Смотрим сессию клиента"""
    if request.method == 'GET' and request.GET.get('mac') and request.GET.get('device') and request.GET.get('port'):
        mac_letters = re.findall(r'[\w\d]', request.GET['mac'])
        if len(mac_letters) == 12:

            mac = '{}{}{}{}-{}{}{}{}-{}{}{}{}'.format(*mac_letters)

            brases = models.Bras.objects.all()
            user_info = {}

            for b in brases:

                with pexpect.spawn(f"telnet {b.ip}") as telnet:
                    telnet.expect(["Username", 'Unable to connect', 'Connection closed'], timeout=20)
                    telnet.sendline(b.login)

                    telnet.expect("[Pp]ass")
                    telnet.sendline(b.password)

                    if telnet.expect(['>', 'password needs to be changed. Change now?']):
                        telnet.sendline('N')

                    bras_output = send_command(telnet, f'display access-user mac-address {mac}')
                    if 'No online user!' not in bras_output:
                        user_index = re.findall(r'User access index\s+:\s+(\d+)', bras_output)
                        if user_index:
                            bras_output = send_command(telnet, f'display access-user user-id {user_index[0]} verbose')
                        user_info[b.name] = bras_output

                # Логи
                log(request.user, b, f'display access-user mac-address {mac}')

            return render(
                request, 'check/bras_info.html',
                {
                    'mac': mac, 'result': user_info, 'port': request.GET['port'],
                    'device': request.GET['device'], 'desc': request.GET.get('desc')
                }
            )

    return redirect('/')


@login_required
@permission(models.Profile.BRAS)
def cut_user_session(request):
    if request.method == 'POST' and request.POST.get('mac') and request.POST.get('device') and request.POST.get('port'):
        mac_letters = re.findall(r'[\w\d]', request.POST['mac'])

        dev = Device(request.POST['device'])
        model_dev = get_object_or_404(models.Devices, name=dev.name)

        if not has_permission_to_device(model_dev, request.user):
            return HttpResponseForbidden()

        # Если мак верный и оборудование доступно
        if len(mac_letters) == 12 and dev.ping():

            mac = '{}{}{}{}-{}{}{}{}-{}{}{}{}'.format(*mac_letters)

            brases = models.Bras.objects.all()

            for b in brases:
                print(b)
                with pexpect.spawn(f"telnet {b.ip}") as telnet:
                    telnet.expect(["Username", 'Unable to connect', 'Connection closed'], timeout=20)
                    telnet.sendline(b.login)

                    telnet.expect(r"[Pp]ass")
                    telnet.sendline(b.password)

                    if telnet.expect(['>', 'password needs to be changed. Change now?']):
                        telnet.sendline('N')

                    telnet.sendline('system-view')
                    telnet.sendline('aaa')
                    telnet.sendline(f'cut access-user mac-address {mac}')

                    # Логи
                    log(request.user, b, f'cut access-user mac-address {mac}')

            with dev.connect(protocol=model_dev.port_scan_protocol, auth_obj=model_dev.auth_group) as session:
                s = session.reload_port(request.POST['port'])

                # Логи
                log(request.user, model_dev, f'reload port {request.POST["port"]} \n{s}')

    return HttpResponseRedirect(
        f'/device/parse_mac?device={request.POST.get("device")}&mac={request.POST.get("mac")}&port={request.POST.get("port")}')
