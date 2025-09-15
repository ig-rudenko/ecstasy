from django.core.cache import cache
from django.db.models import Q
from django.http import Http404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response

from app_settings.models import LogsElasticStackSettings
from check import models
from check.models import Devices
from check.services.device.extra import get_device_stats
from check.services.device.interfaces_collector import get_device_interfaces, InterfacesBuilder
from check.services.device.interfaces_workload import DevicesInterfacesWorkloadCollector
from check.services.remote_terminal import get_console_url
from check.services.zabbix import get_zabbix_host_map_and_uptime
from devicemanager.device import DeviceManager
from devicemanager.device import zabbix_api
from ecstasy_project.types.api import UserAuthenticatedAPIView
from net_tools.models import DevicesInfo as ModelDeviceInfo
from .base import DeviceAPIView
from ..decorators import except_connection_errors
from ..filters import DeviceFilter, DeviceInfoFilter
from ..serializers import DevicesSerializer, DeviceVlanSerializer
from ..swagger.schemas import (
    devices_interfaces_workload_list_api_doc,
    interfaces_workload_api_doc,
    interfaces_list_api_doc,
    device_info_api_doc,
)


@method_decorator(cache_page(60 * 2), name="dispatch")
@method_decorator(vary_on_headers("Authorization"), name="dispatch")
class DevicesListAPIView(UserAuthenticatedAPIView):
    """
    ## Этот класс представляет собой ListAPIView, который возвращает список всех устройств в базе данных.
    """

    serializer_class = DevicesSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DeviceFilter

    def get_queryset(self):
        """
        ## Возвращает queryset всех устройств, к которым у пользователя есть доступ
        через Profile.devices_groups или AccessGroup (users / user_groups),
        при этом исключаются устройства, явно запрещённые в AccessGroup.
        """
        user = self.current_user

        return (
            Devices.objects.filter(
                Q(group__profile__user_id=user.id)  # доступ через профиль
                | Q(access_groups__users=user)
                | Q(access_groups__user_groups__in=user.groups.all())
            )
            .exclude(
                Q(forbidden_access_groups__users=user)
                | Q(forbidden_access_groups__user_groups__in=user.groups.all())
            )
            .distinct()
        )

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        all_fields = self.serializer_class.Meta.fields.copy()
        return_fields = self.request.GET.get("return-fields", "").split(",")
        return_fields = list(set(return_fields) & set(all_fields))

        if not return_fields:
            return_fields = all_fields

        if "group" in return_fields:
            queryset = queryset.select_related("group")
            return_fields.remove("group")
            return_fields.append("group__name")

        queryset = queryset.values(*return_fields)
        return queryset

    def get(self, request, *args, **kwargs):
        """
        ## Возвращаем список всех устройств, без пагинации
        """
        data = self.filter_queryset(self.get_queryset())

        for item in data:
            if item.get("group__name"):
                item["group"] = item["group__name"]
                del item["group__name"]

        return Response(data)


@method_decorator(devices_interfaces_workload_list_api_doc, name="get")
class AllDevicesInterfacesWorkLoadAPIView(UserAuthenticatedAPIView):
    filter_backends = [DjangoFilterBackend]
    filterset_class = DeviceInfoFilter

    def get(self, request, *args, **kwargs):
        collector = DevicesInterfacesWorkloadCollector()
        data = collector.get_interfaces_load_for_user(self.current_user)
        return Response(data)


@method_decorator(interfaces_workload_api_doc, name="get")
class DeviceInterfacesWorkLoadAPIView(UserAuthenticatedAPIView):
    lookup_url_kwarg = "device_name"
    lookup_field = "dev__name"

    def get_queryset(self):
        return ModelDeviceInfo.objects.all().select_related("dev").order_by("dev__name")

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        collector = DevicesInterfacesWorkloadCollector()
        result = collector.get_interfaces_load(instance)
        return Response(result)


@method_decorator(interfaces_list_api_doc, name="get")
class DeviceInterfacesAPIView(DeviceAPIView):
    @except_connection_errors
    def get(self, request, *args, **kwargs) -> Response:
        """
        ## Вывод интерфейсов оборудования

        Пример вывода:

            {
                "interfaces": [
                    {
                        "Interface": "gi1/0/1",
                        "Status": "up",
                        "Description": "To_DEVICE-1",
                        "Link": {
                            "device_name": "DEVICE-1",
                            "url": "/device/DEVICE-1"
                        },
                        "Comments": [
                            {
                                "text": "Какой-то комментарий",
                                "user": "irudenko",
                                "id": 14
                            }
                        ]
                    },

                    ...

                    {
                        "Interface": "te1/0/4",
                        "Status": "down",
                        "Description": ""
                    }
                ],
                "deviceAvailable": true,
                "collected": "2023-03-01T15:13:11.559175"
            }
        """
        device: models.Devices = self.get_object()

        status_on = ["1", "yes", "true"]

        current_status = request.GET.get("current_status") in status_on
        with_vlans = request.GET.get("vlans") in status_on
        check_status = request.GET.get("check_status", "true") in status_on

        interfaces_data = None
        cache_key = (
            f"interfaces:{device.name}:cs:{current_status}:vlans:{with_vlans}:check_status:{check_status}"
        )
        if current_status:
            interfaces_data = cache.get(cache_key)

        if not interfaces_data:
            interfaces_data = get_device_interfaces(
                device,
                DeviceManager.from_model(device),
                current_status=current_status,
                with_vlans=with_vlans,
                check_status=check_status,
            )
            cache.set(cache_key, interfaces_data, timeout=4)

        interfaces_builder = InterfacesBuilder(device)
        interfaces_data["interfaces"] = interfaces_builder.build(
            interfaces=interfaces_data["interfaces"],
            add_links=request.GET.get("add_links", "1") in status_on,
            add_comments=request.GET.get("add_comments", "1") in status_on,
            add_zabbix_graph=request.GET.get("add_zabbix_graph", "1") in status_on,
        )

        return Response(interfaces_data)


@method_decorator(device_info_api_doc, name="get")
class DeviceInfoAPIView(DeviceAPIView):
    """
    ## Возвращаем общую информацию оборудования

    Пример вывода:

        {
            "deviceName": "DEVICE-NAME",
            "deviceIP": "10.10.10.10",
            "elasticStackLink": "URL",
            "zabbixHostID": "45632",
            "zabbixInfo": {
                "description": "ОПИСАНИЕ ОБОРУДОВАНИЯ В ZABBIX",
                "inventory": {
                    "type": "Eltex",
                    "type_full": "MES3324F 28-port 1G/10G Managed Switch",
                    "serialno_a": "",
                    "macaddress_a": "",
                    "hardware": "MES3324F 28-port 1G/10G Managed Switch",

                    ...

                    "model": "MES3324F",
                    "vendor": "Eltex"
                }
            },
            "permission": 3,
            "coords": [
                "23.322332",
                "32.233223"
            ],
            "consoleURL": "",
            "uptime": 23434,
        }

    """

    def get(self, request, device_name: str, *args, **kwargs):
        device: models.Devices = self.get_object()
        zabbix_info = DeviceManager(name=device_name).zabbix_info

        devices_maps, uptime = get_zabbix_host_map_and_uptime(zabbix_info.hostid)

        return Response(
            {
                "deviceName": device.name,
                "deviceIP": device.ip,
                "vendor": device.vendor,
                "model": device.model,
                "serialNumber": device.serial_number,
                "osVersion": device.os_version,
                # Создание URL-адреса для запроса журналов Kibana.
                "elasticStackLink": LogsElasticStackSettings.load().query_kibana_url(device=device),
                "zabbixHostID": int(zabbix_info.hostid or 0),
                "zabbixURL": zabbix_api.zabbix_url,
                "zabbixInfo": {
                    "description": zabbix_info.description,
                    "monitoringAvailable": zabbix_info.status == 1,
                    "inventory": zabbix_info.inventory.to_dict,
                    "maps": devices_maps,
                },
                "permission": self.current_user.profile.perm_level,
                "coords": zabbix_info.inventory.coordinates(),
                "consoleURL": get_console_url(self.current_user.profile, device),
                "uptime": uptime,
            }
        )


class DeviceVlanInfoAPIView(DeviceAPIView):
    """
    ## Возвращаем информацию о VLAN-ах
    """

    serializer_class = DeviceVlanSerializer

    def get(self, request, *args, **kwargs) -> Response:
        device: Devices = self.get_object()
        queryset = device.vlan_set.all().prefetch_related("ports")
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class DeviceStatsInfoAPIView(DeviceAPIView):
    """
    ## Возвращаем данные CPU, FLASH, RAM, TEMP

    Пример вывода:

        {
            "cpu": {
                "util": [ 2 ]
            },
            "ram": {
                "util": 15
            },
            "flash": {
                "util": 50
            },
            "temp": {
                "value": 43.5,
                "status": "normal"
            }
        }
    """

    @except_connection_errors
    def get(self, request, *args, **kwargs) -> Response:
        device: models.Devices = self.get_object()

        # Если оборудование недоступно
        if not device.available:
            return Response({"detail": "Device unavailable"}, status=500)

        device_stats: dict = get_device_stats(device) or {}

        return Response(device_stats)


class GetDeviceByZabbixHostIDAPIView(DeviceAPIView):
    def get(self, request, host_id: str):
        """
        ## Преобразование идентификатора узла сети "host_id" Zabbix в URL ecstasy.

        :param request: Запрос.
        :param host_id: Идентификатор узла сети в Zabbix.
        """

        dev = DeviceManager.from_hostid(host_id)
        if dev is None:
            raise Http404

        # Ищем по имени
        found_dev = self.get_queryset().filter(name=dev.name)
        if not found_dev.exists():
            # Или по IP
            found_dev = self.get_queryset().filter(ip=dev.ip)

        model_dev = found_dev.first()
        if not model_dev:
            # Не нашли оборудование
            raise Http404

        return Response({"device": model_dev.name})
