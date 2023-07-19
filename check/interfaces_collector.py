from datetime import datetime
from typing import Optional, Type

import orjson
from django.db.models import QuerySet
from django.utils import timezone
from django.core.cache import cache
from rest_framework.serializers import ModelSerializer

from .api.serializers import DevicesSerializer
from .models import Devices
from devicemanager.device import DeviceManager
from devicemanager.device.interfaces import Interfaces
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

    def collect_current_interfaces(self, make_session_global, **kwargs) -> None:
        """
        ## Собираем список всех интерфейсов на устройстве в данный момент.

        Если при подключении логин/пароль неверные, то пробуем другие группы авторизации
        """

        # Собираем интерфейсы
        self.device_collector.collect_interfaces(
            vlans=self.with_vlans,
            current_status=True,
            raise_exception=True,
            make_session_global=make_session_global,
            **kwargs
        )

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


class DevicesInterfacesWorkloadCollector:
    cache_key = "all_devices_interfaces_workload_api_view"
    cache_seconds = 60 * 10

    @staticmethod
    def get_interfaces_load(device: DevicesInfo):
        interfaces = Interfaces(orjson.loads(device.interfaces or "[]")).physical()

        non_system = interfaces.non_system()
        abons_up = non_system.up()
        abons_up_with_desc = abons_up.with_description()
        abons_down = non_system.down()
        abons_down_with_desc = abons_down.with_description()

        return {
            "count": interfaces.count,
            "abons": non_system.count,
            "abons_up": abons_up.count,
            "abons_up_with_desc": abons_up_with_desc.count,
            "abons_up_no_desc": abons_up.count - abons_up_with_desc.count,
            "abons_down": abons_down.count,
            "abons_down_with_desc": abons_down_with_desc.count,
            "abons_down_no_desc": abons_down.count - abons_down_with_desc.count,
        }

    def get_all_device_interfaces_workload(self, from_cache=True):
        cache_value = cache.get(self.cache_key)

        if not cache_value or not from_cache:
            queryset = self.get_queryset()
            DeviceSerializerClass = self.get_serializer_class()

            cache_value = {
                "devices_count": queryset.count(),
                "devices": [
                    {
                        "interfaces_count": self.get_interfaces_load(dev_info),
                        **DeviceSerializerClass(dev_info.dev).data,
                    }
                    for dev_info in queryset
                    if dev_info.dev and dev_info.interfaces
                ],
            }
            cache.set(self.cache_key, cache_value, timeout=self.cache_seconds)

        return cache_value

    def get_queryset(self) -> QuerySet:
        return DevicesInfo.objects.all().select_related("dev").order_by("dev__name")

    @staticmethod
    def get_serializer_class() -> Type[ModelSerializer]:
        return DevicesSerializer
