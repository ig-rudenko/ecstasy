import json

import ping3
from datetime import datetime

from django.urls import reverse
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response

from app_settings.models import LogsElasticStackSettings
from devicemanager.device import Device
from devicemanager.exceptions import DeviceException

from devicemanager.device import Interfaces as InterfacesObject, Config as ZabbixConfig
from net_tools.models import DevicesInfo as ModelDeviceInfo
from ..permissions import DevicePermission
from ..serializers import DevicesSerializer
from check import models


class DevicesListAPIView(generics.ListAPIView):
    """
    ## Этот класс представляет собой ListAPIView, который возвращает список всех устройств в базе данных.
    """

    serializer_class = DevicesSerializer

    def get_queryset(self):
        """
        ## Возвращаем queryset всех устройств из доступных для пользователя групп
        """

        # Фильтруем запрос
        query = Q(
            group_id__in=[
                group["id"]
                for group in self.request.user.profile.devices_groups.all().values("id")
            ]
        )
        return models.Devices.objects.filter(query).select_related("group")

    def list(self, request, *args, **kwargs):
        """
        ## Возвращаем JSON список всех устройств, без пагинации
        """

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AllDevicesInterfacesWorkLoadAPIView(generics.ListAPIView):
    def get_queryset(self, *args, **kwargs):
        """
        ## Возвращаем queryset всех устройств из доступных для пользователя групп
        """

        # Фильтруем запрос
        query = Q(
            dev__group_id__in=[
                group["id"]
                for group in self.request.user.profile.devices_groups.all().values("id")
            ]
        )
        return (
            ModelDeviceInfo.objects.filter(query, **kwargs)
            .select_related("dev")
            .order_by("dev__name")
        )

    @staticmethod
    def get_interfaces_load(device: ModelDeviceInfo):
        interfaces = InterfacesObject(json.loads(device.interfaces)).physical()

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

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        result = {
            "devices_count": 0,
            "devices": [],
        }

        for dev_info in queryset:
            result["devices"].append(
                {
                    "interfaces_count": self.get_interfaces_load(dev_info),
                    **DevicesSerializer(dev_info.dev).data,
                }
            )
            result["devices_count"] += 1
        return Response(result)


class DeviceInterfacesWorkLoadAPIView(
    generics.RetrieveAPIView, AllDevicesInterfacesWorkLoadAPIView
):
    lookup_url_kwarg = "device_name"
    lookup_field = "dev__name"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        result = self.get_interfaces_load(instance)
        return Response(result)


class DeviceInterfacesAPIView(APIView):
    permission_classes = [DevicePermission]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.device = None
        self.current_device_info = None
        self.device_collector = None

        # Поля для обновлений, в случае изменения записи в БД
        self.model_update_fields = []

        # Собирать вместе с VLAN
        self.with_vlans = False

    def get(self, request, device_name: str):
        """
        ## Вывод интерфейсов оборудования

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

        :param device_name: Название оборудования
        """

        # Получаем объект устройства из БД
        self.device = get_object_or_404(models.Devices, name=device_name)

        self.check_object_permissions(request, self.device)

        self.device_collector = Device(device_name)

        # Устанавливаем протокол для подключения
        self.device_collector.protocol = self.device.port_scan_protocol
        # Устанавливаем community для подключения
        self.device_collector.snmp_community = self.device.snmp_community
        self.device_collector.auth_obj = self.device.auth_group
        self.device_collector.ip = self.device.ip  # IP адрес
        ping = self.device_collector.ping()  # Оборудование доступно или нет

        # Сканируем интерфейсы в реальном времени?
        current_status = bool(request.GET.get("current_status", False)) and ping > 0

        # Вместе с VLAN?
        self.with_vlans = (
            False
            if self.device_collector.protocol == "snmp"
            else request.GET.get("vlans") == "1"
        )

        # Если не нужен текущий статус интерфейсов, то отправляем прошлые данные
        if not current_status:
            last_interfaces, last_datetime = self.get_last_interfaces()
            last_interfaces = json.loads(last_interfaces)

            self.add_comments(last_interfaces)
            self.add_devices_links(last_interfaces)

            return Response(
                {
                    "interfaces": last_interfaces,
                    "deviceAvailable": ping > 0,
                    "collected": last_datetime,
                }
            )

        # Собираем состояние интерфейсов оборудования в данный момент
        self.get_current_interfaces()

        # Обновляем данные по оборудованию на основе предыдущего подключения
        self.update_device_info()

        # Если не собрали интерфейсы.
        if not self.device_collector.interfaces:
            # Возвращает пустой список интерфейсов.
            return Response(
                {
                    "interfaces": [],
                    "deviceAvailable": ping > 0,
                    "collected": datetime.now(),
                }
            )

        # Проверка наличия устройства в базе данных. Если это так, он получит устройство.
        # Если это не так, будет создано новое устройство.
        try:
            self.current_device_info = ModelDeviceInfo.objects.get(dev=self.device)
        except ModelDeviceInfo.DoesNotExist:
            self.current_device_info = ModelDeviceInfo.objects.create(dev=self.device)

        interfaces = self.save_interfaces()
        self.add_devices_links(interfaces)
        self.add_comments(interfaces)

        return Response(
            {
                "interfaces": interfaces,
                "deviceAvailable": ping > 0,
                "collected": datetime.now(),
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
            for comment in interfaces_comments:
                if comment.interface == intf["Interface"]:
                    intf.setdefault("Comments", [])
                    intf["Comments"].append(
                        {
                            "text": comment.comment,
                            "user": comment.user.username,
                            "id": comment.id,
                        }
                    )

        return interfaces

    def update_device_info(self):
        """
        ## Обновляем информацию об устройстве (вендор, модель) в БД и Zabbix.

        Также отправляем данные, взятые при подключении к оборудованию на Zabbix сервер
        """

        # Обновляем модель устройства, взятую непосредственно во время подключения, либо с Zabbix
        # dev.zabbix_info.inventory.model обновляется на основе реальной модели при подключении
        if (
            self.device_collector.zabbix_info.inventory.model
            and self.device_collector.zabbix_info.inventory.model != self.device.model
        ):
            self.device.model = self.device_collector.zabbix_info.inventory.model
            self.model_update_fields.append("model")

        # Обновляем вендора оборудования, если он отличается от реального либо еще не существует
        if (
            self.device_collector.zabbix_info.inventory.vendor
            and self.device_collector.zabbix_info.inventory.vendor != self.device.vendor
        ):
            self.device.vendor = self.device_collector.zabbix_info.inventory.vendor
            self.model_update_fields.append("vendor")

        # Сохраняем изменения
        if self.model_update_fields:
            self.device.save(update_fields=self.model_update_fields)

        # Обновляем данные в Zabbix
        self.device_collector.push_zabbix_inventory()

    def get_current_interfaces(self) -> None:
        """
        ## Собираем список всех интерфейсов на устройстве в данный момент.

        Если при подключении логин/пароль неверные, то пробуем другие группы авторизации
        """

        # Собираем интерфейсы
        status = self.device_collector.collect_interfaces(
            vlans=self.with_vlans, current_status=True
        )

        # Если пароль неверный, то пробуем все по очереди, кроме уже введенного
        if "Неверный логин или пароль" in str(status):
            # Создаем список объектов авторизации
            all_auth = list(
                models.AuthGroup.objects.exclude(name=self.device.auth_group.name)
                .order_by("id")
                .all()
            )
            # Собираем интерфейсы снова
            status = self.device_collector.collect_interfaces(
                vlans=self.with_vlans, current_status=True, auth_obj=all_auth
            )

            if status is None:  # Если статус сбора интерфейсов успешный
                # Необходимо перезаписать верный логин/пароль в БД, так как первая попытка была неудачной.
                # Смотрим объект у которого такие логин и пароль
                success_auth_obj = models.AuthGroup.objects.get(
                    login=self.device_collector.success_auth["login"],
                    password=self.device_collector.success_auth["password"],
                )

                # Указываем новый логин/пароль для этого устройства
                self.device.auth_group = success_auth_obj
                # Добавляем это поле в список изменений
                self.model_update_fields.append("auth_group")

    def get_last_interfaces(self) -> (str, datetime):
        """
        ## Возвращает кортеж из последних собранных интерфейсов (JSON) и времени их последнего изменения.

            (
                "[ { "Interface": "GE0/0/2", "Status": "down", "Description": "desc" }, ... ]" ,
                datetime
            )
        """

        try:
            device_info = ModelDeviceInfo.objects.get(dev=self.device)
        except ModelDeviceInfo.DoesNotExist:
            return "{}", ""

        # Если необходимы интерфейсы с VLAN и они имеются в БД, то отправляем их
        if self.with_vlans and device_info.vlans:
            return device_info.vlans, device_info.vlans_date

        # Отправляем интерфейсы без VLAN
        return device_info.interfaces or "{}", device_info.interfaces_date or ""

    def save_interfaces(self) -> list:
        """
        ## Сохраняем интерфейсы в БД
        :return: Список сохраненных интерфейсов
        """
        if self.device_collector.interfaces and self.with_vlans:
            interfaces_to_save = [
                {
                    "Interface": line.name,
                    "Status": line.status,
                    "Description": line.desc,
                    "VLAN's": line.vlan,
                }
                for line in self.device_collector.interfaces
            ]
            self.current_device_info.vlans = json.dumps(interfaces_to_save)
            self.current_device_info.vlans_date = datetime.now()
            self.current_device_info.save(update_fields=["vlans", "vlans_date"])

        elif self.device_collector.interfaces:
            interfaces_to_save = [
                {
                    "Interface": line.name,
                    "Status": line.status,
                    "Description": line.desc,
                }
                for line in self.device_collector.interfaces
            ]
            self.current_device_info.interfaces = json.dumps(interfaces_to_save)
            self.current_device_info.interfaces_date = datetime.now()
            self.current_device_info.save(
                update_fields=["interfaces", "interfaces_date"]
            )

        else:
            return []

        return interfaces_to_save


class DeviceInfoAPIView(APIView):
    """
    ## Возвращаем общую информацию оборудования

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

    permission_classes = [DevicePermission]

    def get(self, request, device_name: str):
        model_dev = get_object_or_404(models.Devices, name=device_name)
        self.check_object_permissions(request, model_dev)

        dev = Device(name=device_name)

        data = {
            "deviceName": device_name,
            "deviceIP": model_dev.ip,
            # Создание URL-адреса для запроса журналов Kibana.
            "elasticStackLink": LogsElasticStackSettings.load().query_kibana_url(
                device=model_dev
            ),
            "zabbixHostID": int(dev.zabbix_info.hostid or 0),
            "zabbixURL": ZabbixConfig.ZABBIX_URL,
            "zabbixInfo": {
                "description": dev.zabbix_info.description,
                "inventory": dev.zabbix_info.inventory.to_dict,
            },
            "permission": models.Profile.permissions_level.index(
                models.Profile.objects.get(user_id=request.user.id).permissions
            ),
            "coords": list(dev.zabbix_info.inventory.coordinates()),
        }

        return Response(data)


class DeviceStatsInfoAPIView(APIView):
    """
    ## Возвращаем данные CPU, FLASH, RAM, TEMP

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

    permission_classes = [DevicePermission]

    def get(self, request, device_name: str):
        device = get_object_or_404(models.Devices, name=device_name)
        self.check_object_permissions(request, device)

        if not ping3.ping(device.ip, timeout=2):
            return Response()

        try:
            # Подключаемся к оборудованию
            with device.connect() as session:
                device_stats: dict = session.get_device_info() or {}
                return Response(device_stats)

        except DeviceException:
            return Response(status=400)

