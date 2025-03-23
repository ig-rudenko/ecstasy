from typing import Type

import orjson
from django.core.cache import cache
from django.db.models import QuerySet
from rest_framework.serializers import BaseSerializer

from check.api.serializers import DevicesSerializer
from check.models import Profile
from devicemanager.device.interfaces import Interfaces
from net_tools.models import DevicesInfo


class DevicesInterfacesWorkloadCollector:
    cache_key = "all_devices_interfaces_workload_api_view"
    cache_seconds = 60 * 10

    @staticmethod
    def get_interfaces_load(device: DevicesInfo | dict) -> dict:
        """
        ## Возвращает список интерфейсов и их загрузку.
        :param device: Данные о устройстве.
        :return: Список интерфейсов и их загрузки.
        """
        if isinstance(device, DevicesInfo):
            raw_interfaces = device.interfaces or "[]"
        else:
            raw_interfaces = device.get("interfaces", "[]")

        interfaces = Interfaces(orjson.loads(raw_interfaces))

        physical_interfaces = interfaces.physical()
        non_system = physical_interfaces.non_system()
        abons_up = non_system.up()
        abons_up_with_desc = abons_up.with_description()
        abons_down = non_system.down()
        abons_down_with_desc = abons_down.with_description()

        return {
            "count": physical_interfaces.count,
            "abons": non_system.count,
            "abons_up": abons_up.count,
            "abons_up_with_desc": abons_up_with_desc.count,
            "abons_up_no_desc": abons_up.count - abons_up_with_desc.count,
            "abons_down": abons_down.count,
            "abons_down_with_desc": abons_down_with_desc.count,
            "abons_down_no_desc": abons_down.count - abons_down_with_desc.count,
        }

    @staticmethod
    def get_serializer_class() -> Type[BaseSerializer]:
        return DevicesSerializer

    def get_interfaces_load_for_user(self, user) -> dict:
        data = self.get_all_device_interfaces_workload()
        try:
            groups_names = list(
                Profile.objects.get(user=user).devices_groups.all().values_list("name", flat=True)
            )
        except Profile.DoesNotExist:
            groups_names = []

        user_data = {
            "devices_count": data["devices_count"],
            "devices": [],
        }

        for device_info in data["devices"]:
            if device_info["group"] not in groups_names:
                user_data["devices_count"] -= 1
            else:
                user_data["devices"].append(device_info)
        return user_data

    def get_all_device_interfaces_workload(self, from_cache=True):
        cache_value = cache.get(self.cache_key)

        if not cache_value or not from_cache:
            queryset = self.get_queryset()
            cache_value = {
                "devices_count": len(queryset),
                "devices": [
                    {
                        "interfaces_count": self.get_interfaces_load(dev_info),
                        "ip": dev_info["dev__ip"],
                        "name": dev_info["dev__name"],
                        "vendor": dev_info["dev__vendor"],
                        "group": dev_info["dev__group__name"],
                        "model": dev_info["dev__model"],
                    }
                    for dev_info in queryset
                ],
            }
            cache.set(self.cache_key, cache_value, timeout=self.cache_seconds)

        return cache_value

    @staticmethod
    def get_queryset() -> QuerySet:
        return (
            DevicesInfo.objects.filter(interfaces__isnull=False, dev__active=True)
            .select_related("dev", "dev__group")
            .order_by("dev__name")
            .values(
                "interfaces",
                "dev__ip",
                "dev__name",
                "dev__vendor",
                "dev__group__name",
                "dev__model",
            )
        )
