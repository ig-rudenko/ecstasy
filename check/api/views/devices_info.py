import re
from typing import Type

from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django_filters.rest_framework import DjangoFilterBackend
from requests import RequestException
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView

from app_settings.models import LogsElasticStackSettings
from check import models
from check.interfaces_collector import (
    DeviceInterfacesCollectorMixin,
    DevicesInterfacesWorkloadCollector,
)
from check.logger import django_actions_logger
from devicemanager.device import DeviceManager
from devicemanager.device import ZabbixAPIConnection
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


class DevicesListAPIView(generics.ListAPIView):
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

        # Фильтруем запрос
        group_ids = self.request.user.profile.devices_groups.all().values_list("id", flat=True)
        return models.Devices.objects.filter(group_id__in=group_ids).select_related("group")

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
class AllDevicesInterfacesWorkLoadAPIView(generics.ListAPIView, DevicesInterfacesWorkloadCollector):
    filter_backends = [DjangoFilterBackend]
    filterset_class = DeviceInfoFilter

    def get_queryset(self):
        return ModelDeviceInfo.objects.all().select_related("dev").order_by("dev__name")

    def get_serializer_class(self) -> Type[BaseSerializer]:
        return DevicesSerializer

    def list(self, request, *args, **kwargs):
        data = self.get_all_device_interfaces_workload()
        groups_names = self.request.user.profile.devices_groups.all().values_list("name", flat=True)

        valid_data = {
            "devices_count": data["devices_count"],
            "devices": [],
        }

        for device_info in data["devices"]:
            if device_info["group"] not in groups_names:
                valid_data["devices_count"] -= 1
            else:
                valid_data["devices"].append(device_info)

        return Response(valid_data)


@method_decorator(interfaces_workload_api_doc, name="get")
class DeviceInterfacesWorkLoadAPIView(generics.RetrieveAPIView, AllDevicesInterfacesWorkLoadAPIView):
    lookup_url_kwarg = "device_name"
    lookup_field = "dev__name"

    def get_serializer_class(self) -> Type[BaseSerializer]:
        return DevicesSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        result = self.get_interfaces_load(instance)
        return Response(result)


class DeviceInterfacesAPIView(DeviceInterfacesCollectorMixin, APIView):
    permission_classes = [IsAuthenticated, DevicePermission]

    @property
    def device(self) -> models.Devices:
        """Получаем объект устройства из БД"""
        if self._device is None:
            self._device = get_object_or_404(models.Devices, name=self.kwargs["device_name"])
            self.check_object_permissions(self.request, self._device)
        return self._device

    @property
    def device_collector(self) -> DeviceManager:
        if self._device_collector is None:
            self._device_collector = DeviceManager.from_model(self.device)
        return self._device_collector

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
        available = self.device.available  # Оборудование доступно или нет

        # Сканируем интерфейсы в реальном времени?
        current_status = bool(request.GET.get("current_status", False)) and available > 0

        # Вместе с VLAN?
        self.with_vlans = (
            False if self.device_collector.protocol == "snmp" else request.GET.get("vlans") == "1"
        )

        # Если не нужен текущий статус интерфейсов, то отправляем прошлые данные
        if not current_status:
            last_interfaces, last_datetime = self.get_last_interfaces()

            self.add_comments(last_interfaces)
            self.add_devices_links(last_interfaces)
            self.add_zabbix_graph_links(last_interfaces)

            return Response(
                {
                    "interfaces": last_interfaces,
                    "deviceAvailable": available > 0,
                    "collected": last_datetime,
                }
            )

        # Собираем состояние интерфейсов оборудования в данный момент.
        self.collect_current_interfaces(make_session_global=True)

        # Синхронизируем реальные данные оборудования и поля в базе.
        self.sync_device_info_to_db()

        # Обновляем данные в Zabbix.
        self.device_collector.push_zabbix_inventory()

        # Если не собрали интерфейсы.
        if not self.device_collector.interfaces:
            # Возвращает пустой список интерфейсов.
            return Response(
                {
                    "interfaces": [],
                    "deviceAvailable": available > 0,
                    "collected": timezone.now(),
                }
            )

        self.save_interfaces_to_db()

        interfaces = self.device_collector.interfaces.json()
        self.add_devices_links(interfaces)
        self.add_comments(interfaces)
        self.add_zabbix_graph_links(interfaces)

        return Response(
            {
                "interfaces": interfaces,
                "deviceAvailable": available > 0,
                "collected": timezone.now(),
            }
        )

    @staticmethod
    def add_devices_links(interfaces: list) -> list:
        """
        ## Добавляет к интерфейсам ссылку на оборудование "Link", которое находится в описании

            {
                "Interface": "te1/0/2",
                "Status": "up",
                "Description": "To_DEVICE-1_pTe0/1|DF|",
                "Link": {
                    "device_name": "DEVICE-1",
                    "url": "/device/DEVICE-1"
                }
            },

        :param interfaces: Список интерфейсов
        :return: Список интерфейсов с добавлением ссылок
        """

        devices_names = models.Devices.objects.values("name").all()
        for intf in interfaces:
            for dev in devices_names:
                if dev["name"] in intf["Description"]:
                    intf["Link"] = {
                        "device_name": dev["name"],
                        "url": reverse("device_info", args=[dev["name"]]),
                    }

        return interfaces

    def add_comments(self, interfaces: list) -> list:
        """
        ## Берет список интерфейсов и добавляет к ним существующие комментарии

            {
                "Interface": "Eth0/0/6",
                "Status": "up",
                "Description": "Teplostroy",
                "Comments": [
                    {
                        "text": "Стоит медиаконвертор",
                        "user": "irudenko",
                        "id": 14
                    }
                ]
            },

        :param interfaces: список интерфейсов для добавления комментариев
        """

        interfaces_comments = self.device.interfacescomments_set.select_related("user")

        for intf in interfaces:
            intf["Comments"] = [
                {
                    "text": comment.comment,
                    "user": comment.user.username if comment.user else "Anonymous",
                    "id": comment.id,
                    "createdTime": comment.datetime.isoformat(),
                }
                for comment in interfaces_comments
                if comment.interface == intf["Interface"]
            ]

        return interfaces

    def add_zabbix_graph_links(self, interfaces: list) -> list:
        try:
            with ZabbixAPIConnection().connect() as zbx:
                host = zbx.host.get(output=["name"], filter={"name": self.device.name})
                if not host:
                    return interfaces

                # Получаем все графики для данного узла сети.
                host_id = host[0]["hostid"]
                graphs = zbx.graph.get(hostids=[host_id])

                for intf in interfaces:
                    intf_pattern = re.compile(rf"\s(Gi0/|1/)?\s?{intf['Interface']}[a-zA-Z\s(]")
                    intf_desc = intf["Description"]
                    valid_graph_ids = []

                    for g in graphs:
                        # Ищем все графики, в которых упоминается description или название интерфейса.
                        if (intf_desc and intf_desc in g["name"]) or intf_pattern.search(g["name"]):
                            valid_graph_ids.append(g["graphid"])

                    graphs_ids_params = ""
                    # Создаем параметры URL для фильтрации только требуемых графиков.
                    for graph_id in valid_graph_ids:
                        graphs_ids_params += f"filter_graphids%5B%5D={graph_id}&"

                    if graphs_ids_params:
                        # Создаем ссылку на графики zabbix, если получилось их найти.
                        intf["GraphsLink"] = (
                            f"{ZabbixAPIConnection.ZABBIX_URL}/zabbix.php?"
                            f"view_as=showgraph&action=charts.view&from=now-24h&to=now&"
                            f"filter_hostids%5B%5D={host_id}&filter_search_type=0&"
                            f"{graphs_ids_params}filter_set=1"
                        )

        except RequestException as exc:
            django_actions_logger.error("Ошибка `add_zabbix_graph_links`", exc_info=exc)
        finally:
            return interfaces


class DeviceInfoAPIView(APIView):
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
        model_dev = get_object_or_404(models.Devices, name=device_name)
        self.check_object_permissions(request, model_dev)

        dev = DeviceManager(name=device_name)
        return Response(
            {
                "deviceName": device_name,
                "deviceIP": model_dev.ip,
                # Создание URL-адреса для запроса журналов Kibana.
                "elasticStackLink": LogsElasticStackSettings.load().query_kibana_url(device=model_dev),
                "zabbixHostID": int(dev.zabbix_info.hostid or 0),
                "zabbixURL": ZabbixAPIConnection.ZABBIX_URL,
                "zabbixInfo": {
                    "description": dev.zabbix_info.description,
                    "inventory": dev.zabbix_info.inventory.to_dict,
                },
                "permission": request.user.profile.perm_level,
                "coords": dev.zabbix_info.inventory.coordinates(),
                "consoleURL": self.get_console_url(request.user.profile, model_dev),
            }
        )

    @staticmethod
    def get_console_url(profile: models.Profile, device: models.Devices) -> str:
        if not profile.console_access or not profile.console_url:
            return ""
        if device.cmd_protocol == "telnet":
            return (
                f"{profile.console_url}&command=./.tc.sh {device.ip}&title={device.ip} ({device.name}) telnet"
            )
        elif device.cmd_protocol == "ssh":
            return f"{profile.console_url}&command=./.sc.sh {device.ip}&title={device.ip} ({device.name}) ssh"
        else:
            return profile.console_url


class DeviceStatsInfoAPIView(APIView):
    """
    ## Возвращаем данные CPU, FLASH, RAM, TEMP

    Пример вывода:

        {
            "cpu": {
                "util": [
                    2
                ]
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
