from datetime import datetime
import json

from concurrent.futures import ThreadPoolExecutor

from ecstasy_project.celery import app
from check.models import Devices as ModelDevices, AuthGroup
from devicemanager.device import Device, Config
from net_tools.models import DevicesInfo
from app_settings.models import ZabbixConfig


def save_interfaces(model_dev: ModelDevices):
    dev = Device(name=model_dev.name)
    ping = dev.ping()  # Оборудование доступно или нет

    if not ping:
        # Если оборудование недоступно, то пропускаем
        return

    # Устанавливаем протокол для подключения
    dev.protocol = model_dev.port_scan_protocol
    # Устанавливаем community для подключения
    dev.snmp_community = model_dev.snmp_community
    dev.auth_obj = model_dev.auth_group  # Устанавливаем подключение
    dev.ip = model_dev.ip  # IP адрес

    # Собираем интерфейсы
    status = dev.collect_interfaces(
        vlans=True, current_status=True, make_session_global=False
    )

    model_update_fields = []  # Поля для обновлений, в случае изменения записи в БД

    # Если пароль неверный, то пробуем все по очереди, кроме уже введенного
    if "Неверный логин или пароль" in str(status):

        # Создаем список объектов авторизации
        al = list(
            AuthGroup.objects.exclude(name=model_dev.auth_group.name)
            .order_by("id")
            .all()
        )

        # Собираем интерфейсы снова
        status = dev.collect_interfaces(
            vlans=True, current_status=True, auth_obj=al
        )

        if status is None:  # Если статус сбора интерфейсов успешный
            # Необходимо перезаписать верный логин/пароль в БД, так как первая попытка была неудачной
            try:
                # Смотрим объект у которого такие логин и пароль
                a = AuthGroup.objects.get(
                    login=dev.success_auth["login"],
                    password=dev.success_auth["password"],
                )

            except (TypeError, ValueError, AuthGroup.DoesNotExist):
                # Если нет такого объекта, значит нужно создать
                a = AuthGroup.objects.create(
                    name=dev.success_auth["login"],
                    login=dev.success_auth["login"],
                    password=dev.success_auth["password"],
                    secret=dev.success_auth["privilege_mode_password"],
                )

            # Указываем новый логин/пароль для этого устройства
            model_dev.auth_group = a
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
    if not dev.interfaces.count:
        return

    # Сохраняем интерфейсы
    try:
        current_device_info = DevicesInfo.objects.get(dev=model_dev)
    except DevicesInfo.DoesNotExist:
        current_device_info = DevicesInfo.objects.create(dev=model_dev)

    vlans_interfaces_to_save = [
        {
            "Interface": line.name,
            "Status": line.status,
            "Description": line.desc,
            "VLAN's": line.vlan,
        }
        for line in dev.interfaces
    ]
    current_device_info.vlans = json.dumps(vlans_interfaces_to_save)
    current_device_info.vlans_date = datetime.now()
    print("Saved VLANS      ---", model_dev)

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

    current_device_info.save()
    print("Saved Interfaces ---", model_dev)


@app.task(ignore_result=True)
def periodically_scan():
    Config.set(ZabbixConfig.load())

    with ThreadPoolExecutor() as execute:
        for device in ModelDevices.objects.all():
            execute.submit(save_interfaces, device)
