import orjson
from django.core.cache import cache
from django.db.models import QuerySet
from rest_framework.serializers import BaseSerializer

from check.api.serializers import DevicesSerializer
from check.models import Devices
from devicemanager.device.interfaces import Interfaces
from net_tools.models import DevicesInfo


class DevicesInterfacesWorkloadCollector:
    cache_key = "all_devices_interfaces_workload_api_view"
    cache_seconds = 60 * 10

    def __init__(self, devices_qs: QuerySet[Devices]):
        self.devices_qs = devices_qs

    @staticmethod
    def get_interfaces_load(device: DevicesInfo | dict) -> dict:
        """
        ## Возвращает список интерфейсов и их загрузку.
        :param device: Данные об устройстве.
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
    def get_serializer_class() -> type[BaseSerializer]:
        return DevicesSerializer

    def get_interfaces_workload(self) -> dict:
        queryset = self._create_queryset(self.devices_qs).values_list("dev__name", flat=True).distinct()
        devices_names: list[str] = list(queryset)
        all_devices_data = self.get_all_device_interfaces_workload(from_cache=True)

        return {
            "devices_count": len(devices_names),
            "devices": [
                dev_info for dev_info in all_devices_data["devices"] if dev_info["name"] in devices_names
            ],
        }

    def get_all_device_interfaces_workload(self, from_cache: bool = True):
        cache_value = cache.get(self.cache_key)

        if not cache_value or not from_cache:
            qs = self._create_queryset(Devices.objects.all())
            cache_value = {
                "devices_count": len(qs),
                "devices": [
                    {
                        "interfaces_count": self.get_interfaces_load(dev_info),
                        "ip": dev_info["dev__ip"],
                        "name": dev_info["dev__name"],
                        "vendor": dev_info["dev__vendor"],
                        "group": dev_info["dev__group__name"],
                        "model": dev_info["dev__model"],
                    }
                    for dev_info in qs
                ],
            }
            cache.set(self.cache_key, cache_value, timeout=self.cache_seconds)

        return cache_value

    @staticmethod
    def _create_queryset(qs: QuerySet[Devices]) -> QuerySet:
        return (
            DevicesInfo.objects.filter(interfaces__isnull=False, dev__in=qs)
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
