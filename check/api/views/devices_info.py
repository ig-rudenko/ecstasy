from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app_settings.models import LogsElasticStackSettings
from check import models
from check.services.device.interfaces_workload import (
    DevicesInterfacesWorkloadCollector,
)
from devicemanager.device import DeviceManager
from devicemanager.device import zabbix_api
from ecstasy_project.types.api import UserAuthenticatedAPIView
from net_tools.models import DevicesInfo as ModelDeviceInfo
from ..decorators import except_connection_errors
from ..filters import DeviceFilter, DeviceInfoFilter
from ..permissions import DevicePermission
from ..serializers import DevicesSerializer
from ..swagger.schemas import (
    devices_interfaces_workload_list_api_doc,
    interfaces_workload_api_doc,
    interfaces_list_api_doc,
)
from ...services.device.interfaces_collector import get_device_interfaces, InterfacesBuilder
from ...services.remote_terminal import get_console_url
from ...services.zabbix import get_device_zabbix_maps_ids


class DevicesListAPIView(UserAuthenticatedAPIView):
    """
    ## Этот класс представляет собой ListAPIView, который возвращает список всех устройств в базе данных.
    """

    serializer_class = DevicesSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DeviceFilter

    def get_queryset(self):
        """
        ## Возвращаем queryset всех устройств из доступных для пользователя групп
        """
        return models.Devices.objects.filter(group__profile__user_id=self.current_user.id).select_related(
            "group"
        )

    @method_decorator(cache_page(60 * 10))
    @method_decorator(vary_on_cookie)
    def get(self, request, *args, **kwargs):
        """
        ## Возвращаем список всех устройств, без пагинации

        Пример ответа:

            [
                {
                    "ip": "172.30.0.58",
                    "name": "FTTB_Aktybinsk42_p1_TKD_116",
                    "vendor": "D-Link",
                    "group": "ASW",
                    "model": "DES-3200-28",
                    "port_scan_protocol": "telnet"
                },
                ...
            ]
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


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


class DeviceInterfacesAPIView(UserAuthenticatedAPIView):
    permission_classes = [IsAuthenticated, DevicePermission]

    @interfaces_list_api_doc
    @except_connection_errors
    def get(self, request, *args, **kwargs):
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
        device = get_object_or_404(models.Devices, name=kwargs["device_name"])
        self.check_object_permissions(request, device)

        status_on = ["1", "yes", "true"]

        interfaces_data = get_device_interfaces(
            device,
            DeviceManager.from_model(device),
            current_status=request.GET.get("current_status") in status_on,
            with_vlans=request.GET.get("vlans") in status_on,
        )

        interfaces_builder = InterfacesBuilder(device)
        interfaces_data["interfaces"] = interfaces_builder.build(interfaces_data["interfaces"])

        return Response(interfaces_data)


class DeviceInfoAPIView(UserAuthenticatedAPIView):
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
            ]
        }

    """

    permission_classes = [IsAuthenticated, DevicePermission]

    def get(self, request, device_name: str):
        device = get_object_or_404(models.Devices, name=device_name)
        self.check_object_permissions(self.request, device)
        zabbix_info = DeviceManager(name=device_name).zabbix_info

        with zabbix_api.connect() as zbx:
            devices_maps = get_device_zabbix_maps_ids(zbx, zabbix_info.hostid)

        return Response(
            {
                "deviceName": device_name,
                "deviceIP": device.ip,
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
            }
        )


class DeviceStatsInfoAPIView(APIView):
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

    permission_classes = [IsAuthenticated, DevicePermission]

    @except_connection_errors
    def get(self, request, device_name: str):
        device = get_object_or_404(models.Devices, name=device_name)
        self.check_object_permissions(request, device)

        # Если оборудование недоступно
        if not device.available:
            return Response({"detail": "Device unavailable"}, status=500)

        device_stats: dict = device.connect().get_device_info() or {}
        return Response(device_stats)
