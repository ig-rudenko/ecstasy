
from django.core.cache import cache
from django.db.models import QuerySet
from rest_framework.serializers import BaseSerializer

from check.api.serializers import DevicesSerializer
from check.models import Profile
from gathering.models import Vlan, VlanPort
from net_tools.models import DevicesInfo


class DevicesVlanWorkloadCollector:
    cache_key = "all_devices_vlans_workload_api_view"
    cache_seconds = 60 * 10

    @staticmethod
    def get_vlans_load(device) -> dict:
        """
        ## Возвращает список VLAN и нагрузку на порты.
        :param device: Данные о устройстве.
        :return: Список VLAN и их загрузки по портам.
        """
        vlans = Vlan.objects.filter(device_id=device.dev.id)

        vlan_ports_data = []
        for vlan in vlans:
            vlan_ports = VlanPort.objects.filter(vlan=vlan)
            vlan_ports_data.append(
                {
                    "vlan": vlan.vlan,
                    "vlan_desc": vlan.desc,
                    "ports": [
                        {"port": port.port, "desc_port": port.port or "No description"} for port in vlan_ports
                    ],
                }
            )

        return {"vlan_count": len(vlans), "vlans": vlan_ports_data}

    @staticmethod
    def get_serializer_class() -> type[BaseSerializer]:
        return DevicesSerializer

    def get_vlans_load_for_user(self, user) -> dict:
        data = self.get_all_device_vlans_workload()
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

    def get_all_device_vlans_workload(self, from_cache=True):
        cache_value = cache.get(self.cache_key)

        if not cache_value or not from_cache:
            queryset = self.get_queryset()
            cache_value = {
                "devices_count": len(queryset),
                "devices": [
                    {
                        "vlans_count": self.get_vlans_load(dev_info)["vlan_count"],
                        "vlans": self.get_vlans_load(dev_info)["vlans"],
                        "ip": dev_info["dev__ip"],
                        "name": dev_info["dev__name"],
                        "vendor": dev_info["dev__vendor"],
                        "group": dev_info["dev__group__name"],
                        "model": dev_info["dev__model"],
                        "port_scan_protocol": dev_info["dev__port_scan_protocol"],
                    }
                    for dev_info in queryset
                ],
            }
            cache.set(self.cache_key, cache_value, timeout=self.cache_seconds)

        return cache_value

    @staticmethod
    def get_queryset() -> QuerySet:
        return (
            DevicesInfo.objects.filter(vlans__isnull=False, dev__active=True)
            .select_related("dev", "dev__group")
            .order_by("dev__name")
            .values(
                "vlans",
                "dev__ip",
                "dev__name",
                "dev__vendor",
                "dev__group__name",
                "dev__model",
                "dev__port_scan_protocol",
            )
        )
