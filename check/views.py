"""
Функции представления для взаимодействия с оборудованием
"""

import json
import random
import re
from datetime import datetime
import pexpect
import ping3

from django.urls import reverse
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseNotAllowed, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect, get_object_or_404, resolve_url
from django.db.models import Q
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required

from net_tools.models import VlanName, DevicesInfo
from ecstasy_project import settings
from app_settings.models import LogsElasticStackSettings
from app_settings.models import ZabbixConfig
from devicemanager import *
from . import models

# Устанавливаем конфигурацию для работы с devicemanager
Config.set(ZabbixConfig.load())


def log(user: models.User, model_device: (models.Devices, models.Bras), operation: str) -> None:
    """
    Записываем логи о действиях пользователя "user"

    :param user: Пользователь, который совершил действие
    :param model_device: Оборудование, по отношению к которому было совершено действие
    :param operation: Описание действия
    :return: None
    """

    if not isinstance(user, models.User) or not isinstance(model_device, (models.Devices, models.Bras)) \
            or not isinstance(operation, str):
        with open(settings.LOG_FILE, 'a', encoding="utf-8") as log_file:
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
        with open(settings.LOG_FILE, 'a', encoding="utf-8") as log_file:
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
        with open(settings.LOG_FILE, 'a', encoding="utf-8") as log_file:
            log_file.write(
                f'{datetime.now():%d.%m.%Y %H:%M:%S} '
                f'| {user.username:<10} |  | {model_device} | {operation}\n'
            )


def has_permission_to_device(device_to_check: models.Devices, user):
    """ Определяет, имеет ли пользователь "user" право взаимодействовать с оборудованием "device_to_check" """

    if device_to_check.group_id in [g['id'] for g in user.profile.devices_groups.all().values('id')]:
        return True
    return False


def permission(required_perm=None):
    """ Декоратор для определения прав пользователя """

    all_permissions = models.Profile.permissions_level

    def decorator(func):
        def _wrapper(request, *args, **kwargs):
            # Проверяем уровень привилегий
            user_permission = models.Profile.objects.get(user_id=request.user.id).permissions

            # Если суперпользователь или его уровень привилегий равен или выше требуемых
            if request.user.is_superuser or \
                    all_permissions.index(required_perm) <= all_permissions.index(user_permission):
                return func(request, *args, **kwargs)  # Выполняем функцию

            return HttpResponseForbidden()  # Недостаточно прав

        return _wrapper
    return decorator


def by_zabbix_hostid(request, hostid):
    """ Преобразование идентификатора узла сети "host_id" Zabbix в URL ecstasy """

    dev = Device.from_hostid(hostid)
    try:
        if dev and models.Devices.objects.get(name=dev.name):
            return HttpResponseRedirect(
                resolve_url('device_info', name=dev.name) + '?current_status=1'
            )

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    except (ValueError, TypeError, models.Devices.DoesNotExist) as exception:
        if request.META.get('HTTP_REFERER'):
            return HttpResponseRedirect(request.META.get('HTTP_REFERER') + '/zabbix')

        raise Http404 from exception


@login_required
def home(request):
    """ Домашняя страница """

    return render(request, 'home.html')


@login_required
def show_devices(request):
    """ Список всех имеющихся устройств """

    filter_by_group = request.GET.get('group', '')
    group_param = f'group={filter_by_group}' if filter_by_group else ''

    filter_by_vendor = request.GET.get('vendor', '')
    vendor_param = f'&vendor={filter_by_vendor}' if filter_by_vendor else ''

    page = request.GET.get('page', 1)
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1

    # Группы оборудования, доступные текущему пользователю
    user_groups_ids = []
    user_groups_names = []
    for group in request.user.profile.devices_groups.all().values('id', 'name'):
        user_groups_ids.append(group['id'])
        user_groups_names.append(group['name'])

    user_groups_names = {
        group: reverse('devices-list') + '?' + f'group={group}' + vendor_param
        for group in user_groups_names
    }

    # Вендоры оборудования, что доступны пользователю
    unique_vendors_list = sorted(
        list(
            set(
                d['vendor'] for d in models.Devices.objects.filter(group__in=user_groups_ids).values('vendor')
                if d['vendor']
            )
        )
    )
    vendors = {
        g: reverse('devices-list') + '?' + group_param + f'&vendor={g}'
        for g in unique_vendors_list
    }

    full_url = reverse('devices-list') + '?' + group_param + vendor_param

    # Фильтруем запрос
    query = Q(group__in=user_groups_ids)
    if request.GET.get('s'):
        search_string = request.GET['s'].strip()
        query &= (Q(ip__contains=search_string) | Q(name__icontains=search_string))

    # Фильтруем по группе
    if filter_by_group in user_groups_names:
        query &= Q(group__name=filter_by_group)

    # Фильтруем по вендору
    if filter_by_vendor:
        query &= Q(vendor=filter_by_vendor)

    devs = models.Devices.objects.filter(query)

    paginator = Paginator(devs, per_page=50)

    if page < 1:
        page = 1
    elif page > paginator.num_pages:
        page = paginator.num_pages

    return render(
        request, 'check/devices_list.html',
        {
            'devs': paginator.page(page),
            'search': request.GET.get('s', ''),
            'total_count': paginator.count,
            'page': page,
            'num_pages': paginator.num_pages,
            'device_icon_number': random.randint(1, 5),
            'devices_groups': user_groups_names,
            'vendors': vendors,
            'full_url': full_url
        }
    )


@login_required
def device_info(request, name):
    """ Вывод главной информации об устройстве и его интерфейсов """

    model_dev = get_object_or_404(models.Devices, name=name)  # Получаем объект устройства из БД

    if not has_permission_to_device(model_dev, request.user):
        return HttpResponseForbidden()

    dev = Device(name)
    dev.protocol = model_dev.port_scan_protocol  # Устанавливаем протокол для подключения
    dev.snmp_community = model_dev.snmp_community  # Устанавливаем community для подключения
    dev.auth_obj = model_dev.auth_group  # Устанавливаем подключение
    dev.ip = model_dev.ip  # IP адрес
    ping = dev.ping()  # Оборудование доступно или нет

    # Сканируем интерфейсы в реальном времени?
    current_status = bool(request.GET.get('current_status', False)) and ping > 0

    # Вместе с VLAN?
    with_vlans = False if dev.protocol == 'snmp' else request.GET.get('vlans') == '1'

    # Elastic Stack settings
    elastic_settings = LogsElasticStackSettings.load()
    if elastic_settings.is_set():
        try:
            # Форматируем строку поиска логов
            query_str = elastic_settings.query_str.format(device=model_dev)
        except AttributeError:
            query_str = ''

        # Формируем ссылку для kibana
        logs_url = f"{elastic_settings.kibana_url}?_g=(filters:!(),refreshInterval:(pause:!t,value:0)," \
                   f"time:(from:now-{elastic_settings.time_range},to:now))" \
                   f"&_a=(columns:!({elastic_settings.output_columns}),interval:auto," \
                   f"query:(language:{elastic_settings.query_lang}," \
                   f"query:'{query_str}')," \
                   f"sort:!(!('{elastic_settings.time_field}',desc)))"
    else:
        logs_url = ''

    # Время последнего обновления интерфейсов
    last_interface_update = None
    if not current_status:
        try:
            if with_vlans:
                last_interface_update = DevicesInfo.objects.get(ip=model_dev.ip).vlans_date
            else:
                last_interface_update = DevicesInfo.objects.get(ip=model_dev.ip).interfaces_date
        except DevicesInfo.DoesNotExist:
            pass

    data = {
        'dev': dev,
        'ping': ping,
        'logs_url': logs_url,
        'zabbix_host_id': dev.zabbix_info.hostid,
        'current_status': current_status,
        'last_interface_update': last_interface_update,
        'perms': models.Profile.permissions_level.index(models.Profile.objects.get(user_id=request.user.id).permissions)
    }

    if not request.GET.get('ajax', None):  # Если вызов НЕ AJAX
        return render(request, 'check/device_info.html', data)

    # Собираем интерфейсы
    status = dev.collect_interfaces(vlans=with_vlans, current_status=current_status)

    model_update_fields = []  # Поля для обновлений, в случае изменения записи в БД

    # Если пароль неверный, то пробуем все по очереди, кроме уже введенного
    if 'Неверный логин или пароль' in str(status):
        # Создаем список объектов авторизации
        all_auth = list(models.AuthGroup.objects.exclude(name=model_dev.auth_group.name).order_by('id').all())

        # Собираем интерфейсы снова
        status = dev.collect_interfaces(vlans=with_vlans, current_status=current_status, auth_obj=all_auth)

        if status is None:  # Если статус сбора интерфейсов успешный
            # Необходимо перезаписать верный логин/пароль в БД, так как первая попытка была неудачной
            try:
                # Смотрим объект у которого такие логин и пароль
                success_auth_obj = models.AuthGroup.objects.get(
                    login=dev.success_auth['login'], password=dev.success_auth['password']
                )

            except (TypeError, ValueError, models.AuthGroup.DoesNotExist):
                # Если нет такого объекта, значит нужно создать
                success_auth_obj = models.AuthGroup.objects.create(
                    name=dev.success_auth['login'],
                    login=dev.success_auth['login'], password=dev.success_auth['password'],
                    secret=dev.success_auth['privilege_mode_password']
                )

            model_dev.auth_group = success_auth_obj  # Указываем новый логин/пароль для этого устройства
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

    # Сохраняем интерфейсы
    if current_status and dev.interfaces:
        try:
            current_device_info = DevicesInfo.objects.get(device_name=model_dev.name)
        except DevicesInfo.DoesNotExist:
            current_device_info = DevicesInfo.objects.create(ip=model_dev.ip, device_name=model_dev.name)

        if with_vlans:
            interfaces_to_save = [
                {
                    "Interface": line.name,
                    "Status": line.status,
                    "Description": line.desc,
                    "VLAN's": line.vlan
                } for line in dev.interfaces
            ]
            current_device_info.vlans = json.dumps(interfaces_to_save)
            current_device_info.vlans_date = datetime.now()
            current_device_info.save(update_fields=['vlans', 'vlans_date'])

        else:
            interfaces_to_save = [
                {
                    "Interface": line.name,
                    "Status": line.status,
                    "Description": line.desc
                } for line in dev.interfaces
            ]
            current_device_info.interfaces = json.dumps(interfaces_to_save)
            current_device_info.interfaces_date = datetime.now()
            current_device_info.save(update_fields=['interfaces', 'interfaces_date'])

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


def add_names_to_vlan(vlan_mac_list: list) -> list:
    """ Добавляет к списку VLAN, MAC еще и название VLAN из таблицы соответствий """
    result = []
    vlan_passed = {}  # Словарь с VLAN, имена для которых уже найдены
    for vid, mac in vlan_mac_list:  # Смотрим VLAN и MAC

        # Если еще не искали такой VLAN
        if not vlan_passed.get(vid):
            # Ищем название VLAN'a
            try:
                vlan_name = VlanName.objects.get(vid=int(vid)).name
            except VlanName.DoesNotExist:
                vlan_name = ''
            # Добавляем в множество вланов, которые участвовали в поиске имени
            vlan_passed[vid] = vlan_name

        # Обновляем
        result.append([vid, mac, vlan_passed.get(vid)])

    return result


@login_required
@permission(models.Profile.READ)
def get_port_detail(request):
    """Смотрим информацию о порте"""

    if request.method == 'GET' and request.GET.get('device') and request.GET.get('port'):
        model_dev = get_object_or_404(models.Devices, name=request.GET.get('device'))

        if not has_permission_to_device(model_dev, request.user):
            return HttpResponseForbidden()

        dev = Device(request.GET['device'])

        data = {
            'dev': dev,
            'port': request.GET['port'],
            'desc': request.GET.get('desc', ''),
            'perms': models.Profile.permissions_level.index(request.user.profile.permissions),
        }

        # Если оборудование недоступно
        if dev.ping() <= 0:
            return redirect('device_info', request.GET['device'])

        if not request.GET.get('ajax'):
            # ЛОГИ
            log(request.user, model_dev, f'show mac\'s port {data["port"]}')
            return render(request, 'check/port_page.html', data)

        # Подключаемся к оборудованию
        with model_dev.connect() as session:

            data['macs'] = []  # Итоговый список
            vlan_passed = set()  # Множество уникальных VLAN
            for vid, mac in session.get_mac(data['port']):  # Смотрим VLAN и MAC

                # Если еще не искали такой VLAN
                if vid not in vlan_passed:
                    # Добавляем в множество вланов, которые участвовали в поиске имени
                    vlan_passed.add(vid)
                    # Ищем название VLAN'a
                    try:
                        vlan_name = VlanName.objects.get(vid=int(vid)).name
                    except VlanName.DoesNotExist:
                        vlan_name = ''

                # Обновляем
                data['macs'].append([vid, mac, vlan_name])

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

            if hasattr(session, 'virtual_cable_test'):
                data['cable_test'] = 'has'

            if request.GET.get('ajax') == 'all':
                # Отправляем все собранные данные
                data['macs'] = render_to_string('check/macs_table.html', data)
                del data['dev']
                del data['perms']
                return JsonResponse(data)

    return HttpResponseNotAllowed(['GET'])


@login_required
@permission(models.Profile.REBOOT)
def reload_port(request):
    """Изменяем состояния порта"""

    color_warning = '#d3ad23'  # Оранжевый
    color_success = '#08b736'  # Зеленый
    color_info = '#31d2f2'  # Голубой
    color_error = '#d53c3c'  # Красный
    color = color_success  # Значение по умолчанию

    # Если не суперпользователь, то нельзя изменять состояние определенных портов
    port_guard_pattern = r'svsl|power_monitoring|[as]sw\d|dsl|co[pr]m|msan|core|cr\d|nat|mx-\d|dns|bras'

    if not request.user.is_superuser and \
            re.findall(port_guard_pattern, request.POST.get('desc', '').lower()):
        return JsonResponse({
            'message': 'Запрещено изменять состояние данного порта!',
            'status': 'WARNING',
            'color': '#d3ad23'
        })

    # Если неправильный метод или не все обязательные данные были переданы
    if request.method != 'POST' or not request.POST.get('port') or not request.POST.get('device') or not \
            request.POST.get('status'):
        return JsonResponse({
            'message': f'Ошибка отправки данных {request.POST}',
            'color': color_error,
            'status': 'ERROR'
        })

    dev = Device(request.POST['device'])
    model_dev = get_object_or_404(models.Devices, name=dev.name)

    port: str = request.POST['port']
    status: str = request.POST['status']
    save_config: bool = request.POST.get('save') != 'no'  # По умолчанию сохранять

    # У пользователя нет доступа к группе данного оборудования
    if not has_permission_to_device(model_dev, request.user):
        return JsonResponse({
            'message': 'Вы не имеете права управлять этим устройством',
            'status': 'ERROR',
            'color': '#d53c3c'
        })

    # Уровень привилегий пользователя
    user_permission_level = models.Profile.permissions_level.index(request.user.profile.permissions)

    # Если недостаточно привилегий для изменения статуса порта
    if user_permission_level < 2 and status in ['up', 'down']:
        # Логи
        log(
            request.user, model_dev,
            f'Tried to set port {port} ({request.POST.get("desc")}) to the {status} state, but was refused \n'
        )
        return JsonResponse({
            'message': 'У вас недостаточно прав, для изменения состояния порта!',
            'status': 'WARNING',
            'color': color_warning
        })

    # Если оборудование Недоступно
    if dev.ping() <= 0:
        return JsonResponse({
            'message': 'Оборудование недоступно!',
            'status': 'WARNING',
            'color': color_warning
        })

    # Теперь наконец можем подключиться к оборудованию :)
    with model_dev.connect() as session:
        try:
            # Перезагрузка порта
            if status == 'reload':
                port_change_status = session.reload_port(port=port, save_config=save_config)
                message = f'Порт {port} был перезагружен!'

            # UP and DOWN
            else:
                port_change_status = session.set_port(port=port, status=status, save_config=save_config)
                message = f'Порт {port} был переключен в состояние {status}!'

        except pexpect.TIMEOUT:
            message = 'Timeout'
            color = color_error

    if 'Saved Error' in port_change_status:
        config_status = ' Конфигурация НЕ была сохранена'
        color = color_error

    elif 'Saved OK' in port_change_status:
        config_status = ' Конфигурация была сохранена'

    elif 'Without saving' in port_change_status:
        config_status = ' Конфигурация НЕ была сохранена'
        color = color_info

    else:
        config_status = port_change_status

    message += config_status

    # Логи
    log(request.user, model_dev, f'{status} port {port} ({request.POST.get("desc")}) \n{port_change_status}')

    return JsonResponse({
        'message': message,
        'status': f'Порт {status}',
        'color': color
    })


# BRAS COMMAND
def send_command(session: pexpect, command):
    """ Отправляем команду на BRAS """

    session.sendline(command)
    session.expect(command)
    result = ''
    while True:
        match = session.expect(
            [r'---- More ----|Are you sure to display some information', r'<BRAS\d>|\[BRAS\S+\]']
        )
        result += session.before.decode('utf-8').replace('\x1b[42D', '').replace('?(Y/N)[Y]:', '')
        if match:
            break  # Считали все данные, прерываем

        session.sendline(' ')  # Листаем дальше

    return result


@login_required
@permission(models.Profile.BRAS)
def show_session(request):
    """ Смотрим сессию клиента """

    if request.method == 'GET' and request.GET.get('mac') and request.GET.get('device') and request.GET.get('port'):
        mac_letters = re.findall(r'[\w\d]', request.GET['mac'])
        if len(mac_letters) == 12:

            mac = '{}{}{}{}-{}{}{}{}-{}{}{}{}'.format(*mac_letters)

            brases = models.Bras.objects.all()
            user_info = {}
            errors = []

            if not request.GET.get('ajax'):
                # Если это асинхронный запрос, то отправляем html
                return render(
                    request, 'check/bras_info.html',
                    {
                        'mac': mac, 'result': user_info, 'port': request.GET['port'],
                        'device': request.GET['device'], 'desc': request.GET.get('desc'),
                        'errors': errors
                    }
                )

            for bras in brases:
                try:
                    with pexpect.spawn(f"telnet {bras.ip}") as telnet:
                        telnet.expect(["Username", 'Unable to connect', 'Connection closed'], timeout=10)
                        telnet.sendline(bras.login)

                        telnet.expect("[Pp]ass")
                        telnet.sendline(bras.password)

                        if telnet.expect(['>', 'password needs to be changed. Change now?']):
                            telnet.sendline('N')

                        bras_output = send_command(telnet, f'display access-user mac-address {mac}')
                        if 'No online user!' not in bras_output:
                            user_index = re.findall(r'User access index\s+:\s+(\d+)', bras_output)
                            if user_index:
                                bras_output = send_command(
                                    telnet, f'display access-user user-id {user_index[0]} verbose'
                                )
                            user_info[bras.name] = bras_output
                except pexpect.TIMEOUT:
                    errors.append(
                        'Не удалось подключиться к ' + bras.name
                    )

                # Логи
                log(request.user, bras, f'display access-user mac-address {mac}')

            return render(request, 'check/bras_table.html', {
                'mac': mac, 'result': user_info, 'port': request.GET['port'],
                'device': request.GET['device'], 'desc': request.GET.get('desc'),
            })

    return redirect('/')


@login_required
@permission(models.Profile.BRAS)
def cut_user_session(request):
    """ Сбрасываем сессию по MAC адресу """

    status = 'miss'

    # color_warning = '#d3ad23'
    color_success = '#08b736'
    color_error = '#d53c3c'
    status_color = color_error  # Значение по умолчанию

    if request.method == 'POST' and request.POST.get('mac') and request.POST.get('device') and request.POST.get('port'):
        mac_letters = re.findall(r'[\w\d]', request.POST['mac'])

        dev = Device(request.POST['device'])
        model_dev = get_object_or_404(models.Devices, name=dev.name)

        if not has_permission_to_device(model_dev, request.user):
            return HttpResponseForbidden()

        # Если неверный MAC
        status = 'invalid MAC'

        # Если мак верный и оборудование доступно
        if len(mac_letters) == 12 and dev.ping() > 0:

            mac = '{}{}{}{}-{}{}{}{}-{}{}{}{}'.format(*mac_letters)

            brases = models.Bras.objects.all()

            status = ''  # Обновляем статус
            for bras in brases:
                try:
                    print(bras)
                    with pexpect.spawn(f"telnet {bras.ip}") as telnet:
                        telnet.expect(["Username", 'Unable to connect', 'Connection closed'], timeout=20)
                        telnet.sendline(bras.login)

                        telnet.expect(r"[Pp]ass")
                        telnet.sendline(bras.password)

                        if telnet.expect(['>', 'password needs to be changed. Change now?']):
                            telnet.sendline('N')

                        telnet.sendline('system-view')
                        telnet.sendline('aaa')
                        telnet.sendline(f'cut access-user mac-address {mac}')

                        # Логи
                        log(request.user, bras, f'cut access-user mac-address {mac}')

                except pexpect.TIMEOUT:
                    status += bras.name + ' timeout\n'  # Кто был недоступен

            with model_dev.connect() as session:
                # Перезагружаем порт без сохранения конфигурации
                reload_port_status = session.reload_port(request.POST['port'], save_config=False)

                status += reload_port_status
                status_color = color_success  # Успех

                # Логи
                log(request.user, model_dev, f'reload port {request.POST["port"]} \n{reload_port_status}')

    return JsonResponse(
        {
            'message': status,
            'color': status_color,
            'status': 'cut session'
        }
    )


@login_required
@permission(models.Profile.REBOOT)
def set_description(request):
    """ Изменяем описание на порту у оборудования """

    if request.method != 'POST':
        return HttpResponseNotAllowed(permitted_methods=['POST'])

    if request.POST.get('device_name') and request.POST.get('port'):
        dev = get_object_or_404(models.Devices, name=request.POST.get('device_name'))

        new_description = request.POST.get('description')
        port = request.POST.get('port')

        max_length = 64  # По умолчанию максимальная длина описания 64 символа
        status = 'success'  # По умолчанию успешно

        with dev.connect() as session:
            if hasattr(session, 'set_description'):
                set_description_status = session.set_description(port=port, desc=new_description)
                new_description = session.clear_description(new_description)

            else:
                set_description_status = 'Недоступно для данного оборудования'
                status = 'warning'  # Описание цветовой палитры для bootstrap

        if 'Неверный порт' in set_description_status:
            status = 'warning'

        # Проверяем результат изменения описания
        if 'Max length' in set_description_status:
            # Описание слишком длинное
            max_length = set_description_status.split(':')[1]  # Находим в строке "Max length:32" число "32"
            if max_length.isdigit():
                max_length = int(max_length)
            else:
                max_length = 32
            set_description_status = f'Слишком длинное описание! Укажите не более {max_length} символов.'
            status = 'warning'

        return JsonResponse(
            {
                'status': status,
                'description': new_description,
                'info': set_description_status,
                'max_length': max_length
            }
        )

    return JsonResponse(
        {
            'status': 'danger',
            'info': 'Invalid data',
        }
    )


@login_required
@permission(models.Profile.READ)
def start_cable_diag(request):
    """ Запускаем диагностику кабеля на порту """

    if request.method == 'GET' and request.GET.get('device') and request.GET.get('port'):
        model_dev = get_object_or_404(models.Devices, name=request.GET['device'])
        dev = Device(request.GET['device'], zabbix_info=False)

        if not has_permission_to_device(model_dev, request.user):
            return HttpResponseForbidden()

        data = {}
        # Если оборудование доступно
        if dev.ping() > 0:
            with model_dev.connect() as session:
                if hasattr(session, 'virtual_cable_test'):
                    cable_test = session.virtual_cable_test(request.GET['port'])
                    if cable_test:  # Если имеются данные
                        data['cable_test'] = cable_test

        return JsonResponse(data)


@login_required
@permission(models.Bras)
def change_adsl_profile(request):
    port: str = request.POST.get('port')
    profile_index: str = request.POST.get('index')

    if request.method != 'POST':
        return JsonResponse({
            'error': 'Method not allowed!'
        }, status=403)

    if not port or not profile_index or not profile_index.isdigit() or int(profile_index) <= 0:
        return JsonResponse({
            'error': 'Invalid data',
            'data': request.POST
        }, status=400)

    model_dev = get_object_or_404(models.Devices, name=request.POST.get('device_name'))

    if not ping3.ping(model_dev.ip, timeout=2):
        return JsonResponse({
            'error': 'Device down'
        })

    with model_dev.connect() as session:
        if hasattr(session, 'change_profile'):
            status = session.change_profile(port, int(profile_index))

            return JsonResponse({
                'status': status
            })

        else:
            return JsonResponse({
                'error': 'Device can\'t change profile'
            }, status=400)
