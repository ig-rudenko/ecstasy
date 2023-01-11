import json
from datetime import datetime

from django.views import View
from django.db.models import Q
from django.template.defaultfilters import date as _date
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from rest_framework import generics
from rest_framework.response import Response

from app_settings.models import LogsElasticStackSettings
from devicemanager.device import Device, Interfaces
from net_tools.models import DevicesInfo
from .serializers import DevicesSerializer
from .. import models
from ..views import has_permission_to_device


@method_decorator(login_required, name="dispatch")
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


@method_decorator(login_required, name="dispatch")
class DeviceInterfacesAPIView(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.device: models.Devices
        self.current_device_info: DevicesInfo
        self.device_collector: Device

        # Поля для обновлений, в случае изменения записи в БД
        self.model_update_fields = []

        # Собирать вместе с VLAN
        self.with_vlans = False

    def get(self, request, device_name: str):
        """
        ## Вывод интерфейсов оборудования

        :param device_name: Название оборудования
        """

        # Получаем объект устройства из БД
        self.device = get_object_or_404(models.Devices, name=device_name)

        if not has_permission_to_device(self.device, request.user):
            return HttpResponseForbidden()

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
            last_datetime = _date(last_datetime)
            json_str = (
                '{"interfaces": '
                + last_interfaces
                + ', "collected": "'
                + last_datetime
                + f"\", \"deviceAvailable\": {'true' if ping > 0 else 'false'}"
                + "}"
            )
            return HttpResponse(json_str, content_type="application/json")

        # Собираем состояние интерфейсов оборудования в данный момент
        self.get_current_interfaces()

        # Обновляем данные по оборудованию на основе предыдущего подключения
        self.update_device_info()

        # Если не собрали интерфейсы.
        if not self.device_collector.interfaces:
            # Возвращает пустой список интерфейсов.
            return JsonResponse(
                {
                    "interfaces": [],
                    "deviceAvailable": ping > 0,
                    "collected": datetime.now(),
                }
            )

        # Проверка наличия устройства в базе данных. Если это так, он получит устройство.
        # Если это не так, будет создано новое устройство.
        try:
            self.current_device_info = DevicesInfo.objects.get(
                device_name=self.device.name
            )
        except DevicesInfo.DoesNotExist:
            self.current_device_info = DevicesInfo.objects.create(
                ip=self.device.ip, device_name=self.device.name
            )

        # Сохраняем интерфейсы в базу.
        interfaces = self.save_interfaces()

        return JsonResponse(
            {
                "interfaces": interfaces,
                "deviceAvailable": ping > 0,
                "collected": datetime.now(),
            }
        )

    def update_device_info(self):
        """
        ## Обновляем информацию об устройстве.
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
        """

        device_info = DevicesInfo.objects.get(ip=self.device.ip)
        if self.with_vlans:
            return device_info.vlans, device_info.vlans_date
        return device_info.interfaces, device_info.interfaces_date

    def save_interfaces(self) -> list:
        """
        ## Сохраняем интерфейсы в БД
        :return: Список сохраненных интерфейсов
        """
        if self.with_vlans:
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

        else:
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

        return interfaces_to_save


@method_decorator(login_required, name="dispatch")
class DeviceInfoAPIView(View):

    def get(self, request, device_name: str):
        model_dev = get_object_or_404(models.Devices, name=device_name)

        if not has_permission_to_device(model_dev, request.user):
            return HttpResponseForbidden()

        dev = Device(name=device_name)

        data = {
            "deviceName": device_name,
            "deviceIP": model_dev.ip,
            # Создание URL-адреса для запроса журналов Kibana.
            "elasticStackLink": LogsElasticStackSettings.load().query_kibana_url(device=model_dev),
            "zabbixHostID": int(dev.zabbix_info.hostid),
            "permission": models.Profile.permissions_level.index(
                models.Profile.objects.get(user_id=request.user.id).permissions
            ),
            "coords": list(dev.zabbix_info.inventory.coordinates())
        }

        return JsonResponse(data)
