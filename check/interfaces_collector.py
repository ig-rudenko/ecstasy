from datetime import datetime
from typing import Optional

import orjson
from django.utils import timezone

from .models import Devices, AuthGroup
from devicemanager import DeviceManager
from devicemanager.zabbix_info_dataclasses import ZabbixInventory
from net_tools.models import DevicesInfo


class DeviceInterfacesCollectorMixin:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.device: Devices = Optional[None]
        self.device_collector: DeviceManager = Optional[None]

        # Поля для обновлений, в случае изменения записи в БД
        self.model_update_fields = []

        # Собирать вместе с VLAN
        self.with_vlans = False

    def get_device(self) -> Devices:
        pass

    def sync_device_info_to_db(self):
        """
        ## Обновляем информацию об устройстве (вендор, модель) в БД.
        """
        actual_inventory: ZabbixInventory = self.device_collector.zabbix_info.inventory

        for field_name in ["vendor", "model"]:
            inventory_field_value = getattr(actual_inventory, field_name)
            dev_field_value = getattr(self.device, field_name)

            if inventory_field_value and inventory_field_value != dev_field_value:
                setattr(self.device, field_name, inventory_field_value)
                self.model_update_fields.append(field_name)

        # Сохраняем изменения
        if self.model_update_fields:
            self.device.save(update_fields=self.model_update_fields)

    def collect_current_interfaces(self, make_session_global=True, **kwargs) -> None:
        """
        ## Собираем список всех интерфейсов на устройстве в данный момент.

        Если при подключении логин/пароль неверные, то пробуем другие группы авторизации
        """

        # Собираем интерфейсы
        status = self.device_collector.collect_interfaces(
            vlans=self.with_vlans,
            current_status=True,
            make_session_global=make_session_global,
            **kwargs
        )

        # Если пароль неверный, то пробуем все по очереди, кроме уже введенного
        if "Неверный логин или пароль" in str(status):
            # Создаем список объектов авторизации
            auth_list = list(
                AuthGroup.objects.exclude(name=self.device.auth_group.name).order_by("id").all()
            )
            # Собираем интерфейсы снова
            status = self.device_collector.collect_interfaces(
                vlans=self.with_vlans,
                current_status=True,
                auth_obj=auth_list,
                make_session_global=make_session_global,
                **kwargs
            )

            if status is None:  # Если статус сбора интерфейсов успешный
                # Необходимо перезаписать верный логин/пароль в БД, так как первая попытка была неудачной.
                # Смотрим объект у которого такие логин и пароль
                success_auth_obj = AuthGroup.objects.get(
                    login=self.device_collector.success_auth["login"],
                    password=self.device_collector.success_auth["password"],
                )

                # Указываем новый логин/пароль для этого устройства
                self.device.auth_group = success_auth_obj
                # Добавляем это поле в список изменений
                self.model_update_fields.append("auth_group")

    def get_last_interfaces(self) -> (list, datetime):
        """
        ## Возвращает кортеж из последних собранных интерфейсов и времени их последнего изменения.

            (
                [ { "Interface": "GE0/0/2", "Status": "down", "Description": "desc" }, ... ] ,
                datetime
            )
        """

        interfaces = []
        collected_time: datetime = timezone.now()

        try:
            device_info = DevicesInfo.objects.get(dev=self.device)
        except DevicesInfo.DoesNotExist:
            return interfaces, collected_time

        # Если необходимы интерфейсы с VLAN и они имеются в БД, то отправляем их
        if self.with_vlans and device_info.vlans:
            interfaces = orjson.loads(device_info.vlans or "[]")
            collected_time = device_info.vlans_date or timezone.now()
        else:
            interfaces = orjson.loads(device_info.interfaces or "[]")
            collected_time = device_info.interfaces_date or timezone.now()

        return interfaces, collected_time

    def save_interfaces_to_db(self):
        """
        ## Сохраняем интерфейсы в БД
        :return: Список сохраненных интерфейсов
        """
        device_info, _ = DevicesInfo.objects.get_or_create(dev=self.device)
        if self.device_collector.interfaces and self.with_vlans:
            device_info.update_interfaces_with_vlans_state(self.device_collector.interfaces)
            device_info.save(update_fields=["vlans", "vlans_date"])

        elif self.device_collector.interfaces:
            device_info.update_interfaces_state(self.device_collector.interfaces)
            device_info.save(update_fields=["interfaces", "interfaces_date"])
