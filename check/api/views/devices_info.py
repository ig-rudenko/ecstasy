from django.core.cache import cache
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
from check.services.device.interfaces_collector import (
    DeviceInterfacesResult,
    InterfacesBuilder,
    get_device_interfaces,
)
from check.services.device.interfaces_workload import DevicesInterfacesWorkloadCollector
from check.services.remote_terminal import get_console_url
from check.services.zabbix import get_zabbix_host_map_and_uptime
from devicemanager.device import DeviceManager, zabbix_api
from ecstasy_project.types.api import UserAuthenticatedAPIView

from ...services.filters import filter_devices_qs_by_user
from ..decorators import except_connection_errors
from ..filters import DeviceFilter
from ..serializers import DevicesSerializer, DeviceVlanSerializer
from ..swagger.schemas import (
    device_info_api_doc,
    devices_interfaces_workload_list_api_doc,
    devices_list_api_doc,
    interfaces_list_api_doc,
    interfaces_workload_api_doc,
)
from .base import DeviceAPIView


@method_decorator(devices_list_api_doc, name="get")
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
        return filter_devices_qs_by_user(Devices.objects.all(), self.current_user)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        return_fields = self.return_fields

        # Если запрашивается поле group, то нужно добавить связь с моделью Group
        if "group" in return_fields:
            queryset = queryset.select_related("group")
            return_fields.remove("group")
            return_fields.append("group__name")

        # Если запрашивается поле console_url, то нужно добавить дополнительные поля.
        if "console_url" in return_fields:
            return_fields += ["cmd_protocol", "ip", "name"]

        # Получаем список полей модели
        model_fields = [f.name for f in queryset.model._meta.fields] + ["group__name"]
        # Оставляем поля, которые есть в модели
        return queryset.values(*[f for f in return_fields if f in model_fields])

    @property
    def return_fields(self) -> list[str]:
        # Формируем список полей, которые могут быть возвращены в ответе.
        all_fields = self.serializer_class.Meta.fields.copy()
        return_fields = (
            self.request.GET.get("return_fields", "") or self.request.GET.get("return-fields", "")
        ).split(",")

        # Оставляем только поля, которые есть в списке all_fields.
        return_fields = list(set(return_fields) & set(all_fields))

        # Если не указано ни одного поля, то возвращаем все поля.
        if not return_fields:
            return_fields = all_fields

        return return_fields

    def get(self, request, *args, **kwargs):
        """
        ## Возвращаем список всех устройств, без пагинации
        """
        data = self.filter_queryset(self.get_queryset())
        return_fields = self.return_fields

        for item in data:
            # Форматируем поле group
            if item.get("group__name"):
                item["group"] = item["group__name"]
                del item["group__name"]

            # Добавляем поле console_url
            if "console_url" in return_fields:
                item["console_url"] = get_console_url(
                    self.current_user.profile,
                    ip=item["ip"],
                    name=item["name"],
                    cmd_protocol=item["cmd_protocol"],
                )

            # Оставляем только нужные поля
            for key in list(item.keys()):
                if key not in return_fields:
                    item.pop(key)

        return Response(data)


@method_decorator(devices_interfaces_workload_list_api_doc, name="get")
class AllDevicesInterfacesWorkLoadAPIView(UserAuthenticatedAPIView):
    filter_backends = [DjangoFilterBackend]
    filterset_class = DeviceFilter

    def get_queryset(self):
        """
        ## Возвращает queryset всех устройств, к которым у пользователя есть доступ
        через Profile.devices_groups или AccessGroup (users / user_groups),
        при этом исключаются устройства, явно запрещённые в AccessGroup.
        """
        return filter_devices_qs_by_user(Devices.objects.all(), self.current_user)

    def get(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        collector = DevicesInterfacesWorkloadCollector(qs)
        data = collector.get_interfaces_workload()
        return Response(data)


@method_decorator(interfaces_workload_api_doc, name="get")
class DeviceInterfacesWorkLoadAPIView(DeviceAPIView):
    def get(self, request, *args, **kwargs):
        device = self.get_object()
        result = DevicesInterfacesWorkloadCollector.get_interfaces_load(device=device.devicesinfo or {})
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
                        "name": "gi1/0/1",
                        "status": "up",
                        "description": "To_DEVICE-1",
                        "link": {
                            "deviceName": "DEVICE-1",
                            "url": "/device/DEVICE-1"
                        },
                        "comments": [
                            {
                                "text": "Какой-то комментарий",
                                "user": "irudenko",
                                "id": 14
                            }
                        ],
                        "vlans": [],
                    },

                    ...

                    {
                        "name": "te1/0/4",
                        "status": "down",
                        "description": ""
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

        interfaces_data: DeviceInterfacesResult | None = None
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
        interfaces = interfaces_builder.build(
            interfaces=interfaces_data.interfaces.json(),
            add_links=request.GET.get("add_links", "1") in status_on,
            add_comments=request.GET.get("add_comments", "1") in status_on,
            add_zabbix_graph=request.GET.get("add_zabbix_graph", "1") in status_on,
        )

        return Response(
            {
                "interfaces": interfaces,
                "deviceAvailable": interfaces_data.device_available,
                "collected": interfaces_data.collected,
            }
        )


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

    def get(self, request, device_name_or_ip: str, *args, **kwargs):
        device: models.Devices = self.get_object()
        zabbix_info = DeviceManager(name=device_name_or_ip).zabbix_info

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
                "consoleURL": get_console_url(
                    self.current_user.profile,
                    ip=device.ip,
                    name=device.name,
                    cmd_protocol=device.cmd_protocol,
                ),
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
