from typing import Literal

import orjson
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from check import models
from check.logging import log
from check.permissions import profile_permission
from devicemanager.device import Interfaces
from devicemanager.remote.exceptions import InvalidMethod
from net_tools.models import VlanName, DevicesInfo
from ..swagger import schemas
from ..decorators import except_connection_errors
from ..permissions import DevicePermission
from ..serializers import (
    InterfacesCommentsSerializer,
    ADSLProfileSerializer,
    PortControlSerializer,
    PoEPortStatusSerializer,
)


@method_decorator(schemas.port_control_api_doc, name="post")  # API DOC
@method_decorator(profile_permission(models.Profile.REBOOT), name="dispatch")
class PortControlAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, DevicePermission]
    serializer_class = PortControlSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.port_desc = ""

    @except_connection_errors
    def post(self, request, device_name: str):
        """
        ## Изменяем состояние порта оборудования
        """

        # Проверяем данные, полученные в запросе, с помощью сериализатора.
        serializer: PortControlSerializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        port_status: Literal["up", "down", "reload"] = serializer.validated_data["status"]
        port_name: str = serializer.validated_data["port"]
        save_config: bool = serializer.validated_data["save"]

        model_dev = get_object_or_404(models.Devices, name=device_name)

        # Есть ли у пользователя доступ к группе данного оборудования
        self.check_object_permissions(request, model_dev)

        # Если оборудование Недоступно
        if not model_dev.available:
            return Response({"error": "Оборудование недоступно!"}, status=500)

        # Теперь наконец можем подключиться к оборудованию :)
        session = model_dev.connect()
        # Перезагрузка порта
        if port_status == "reload":
            port_change_status = session.reload_port(
                port=port_name,
                save_config=save_config,
            )

        # UP and DOWN
        else:
            port_change_status = session.set_port(
                port=port_name,
                status=port_status,
                save_config=save_config,
            )

        if "Неверный порт" in port_change_status:
            return Response({"error": port_change_status}, status=400)

        # Логи
        log(
            request.user,
            model_dev,
            f"{port_status} port {port_name} ({self.port_desc}) \n{port_change_status}",
        )

        return Response(serializer.validated_data, status=200)

    def check_object_permissions(self, request, device) -> None:
        # Смотрим интерфейсы, которые сохранены в БД
        dev_info, _ = DevicesInfo.objects.get_or_create(dev=device)

        if dev_info.interfaces is None:
            # Собираем интерфейсы с оборудования.
            interfaces = Interfaces(device.connect().get_interfaces())
        else:
            # Преобразовываем JSON строку с интерфейсами в класс `Interfaces`
            interfaces = Interfaces(orjson.loads(dev_info.interfaces))

        # Далее смотрим описание на порту, так как от этого будет зависеть, может ли пользователь управлять им
        self.port_desc: str = interfaces[self.request.data["port"]].desc

        # Если не суперпользователь, то нельзя изменять состояние определенных портов
        if not request.user.is_superuser and settings.PORT_GUARD_PATTERN.search(self.port_desc):
            raise PermissionDenied(
                detail="Запрещено изменять состояние данного порта!",
            )

        # Если недостаточно привилегий для изменения статуса порта
        if request.user.profile.perm_level < 2 and request.data["status"] in ["up", "down"]:
            # Логи
            log(
                request.user,
                device,
                f"Tried to set port {request.data['port']} ({self.port_desc}) "
                f"to the {request.data['status']} state, but was refused \n",
            )

            raise PermissionDenied(
                detail="У вас недостаточно прав, для изменения состояния порта!",
            )


@method_decorator(profile_permission(models.Profile.BRAS), name="dispatch")
class ChangeDescriptionAPIView(APIView):
    """
    ## Изменяем описание на порту у оборудования
    """

    permission_classes = [IsAuthenticated, DevicePermission]

    @except_connection_errors
    def post(self, request, device_name: str):
        """
        ## Меняем описание на порту оборудования

        Требуется передать JSON:

            {
                "port": "порт оборудования",
                "description": "новое описание порта"
            }

        Если указанного порта не существует на оборудовании, то будет отправлен ответ со статусом `400`

            {
                "detail": "Неверный порт {port}"
            }

        Если описание слишком длинное, то будет отправлен ответ со статусом `400`

            {
                "detail": "Слишком длинное описание! Укажите не более {max_length} символов."
            }

        """

        if not self.request.data.get("port"):
            raise ValidationError({"detail": "Укажите порт!"})

        dev = get_object_or_404(models.Devices, name=device_name)

        # Проверяем права доступа пользователя к оборудованию
        self.check_object_permissions(request, dev)

        new_description = self.request.data.get("description", "")
        port = self.request.data.get("port")

        set_description_status = dev.connect().set_description(port=port, desc=new_description)

        if set_description_status.max_length:
            # Если есть данные, что описание слишком длинное.
            raise ValidationError(
                {
                    "detail": "Слишком длинное описание! "
                    f"Укажите не более {set_description_status.max_length} символов."
                }
            )

        log(request.user, dev, str(set_description_status))

        if set_description_status.error:
            return Response(
                {"detail": f"{set_description_status.error}, port={port}"},
                status=400 if set_description_status.error == "Неверный порт" else 500,
            )
        # Логи

        return Response(
            {
                "description": set_description_status.description,
                "port": set_description_status.port,
                "saved": set_description_status.saved,
            }
        )


class MacListAPIView(APIView):
    permission_classes = [IsAuthenticated, DevicePermission]

    @except_connection_errors
    def get(self, request, device_name):
        """
        ## Смотрим MAC-адреса на порту оборудования

        Для этого необходимо передать порт в параметре URL `?port=eth1`

        Если порт верный и там есть MAC-адреса, то будет вот такой ответ:

            {
                "count": 47,
                "result": [
                    {
                        "vlanID": "1051",
                        "mac": "00-04-96-51-AD-3D",
                        "vlanName": ""
                    },
                    {
                        "vlanID": "1051",
                        "mac": "00-04-96-52-A5-FB",
                        "vlanName": ""
                    },
                    ...
                ]
            }

        """

        port = self.request.GET.get("port")
        if not port:
            raise ValidationError({"detail": "Укажите порт!"})

        device = get_object_or_404(models.Devices, name=device_name)
        self.check_object_permissions(request, device)

        session = device.connect()
        macs = []  # Итоговый список
        vlan_passed = {}  # Словарь уникальных VLAN
        for vid, mac in session.get_mac(port):  # Смотрим VLAN и MAC
            # Если еще не искали такой VLAN
            if vid not in vlan_passed:
                # Ищем название VLAN'a
                try:
                    vlan_name = VlanName.objects.get(vid=int(vid)).name
                except (ValueError, VlanName.DoesNotExist):
                    vlan_name = ""
                # Добавляем в множество вланов, которые участвовали в поиске имени
                vlan_passed[vid] = vlan_name

            # Обновляем
            macs.append({"vlanID": vid, "mac": mac, "vlanName": vlan_passed[vid]})

        return Response({"count": len(macs), "result": macs})


class CableDiagAPIView(APIView):
    permission_classes = [IsAuthenticated, DevicePermission]

    @except_connection_errors
    def get(self, request, device_name):
        """
        ## Запускаем диагностику кабеля на порту

        Для этого необходимо передать порт в параметре URL `?port=eth1`

        Функция возвращает данные в виде словаря.
        В зависимости от результата диагностики некоторые ключи могут отсутствовать за ненадобностью.

            {
                "len": "-",         # Длина кабеля в метрах, либо "-", когда не определено
                "status": "",       # Состояние на порту (Up, Down, Empty)
                "pair1": {
                    "status": "",   # Статус первой пары (Open, Short)
                    "len": "",      # Длина первой пары в метрах
                },
                "pair2": {
                    "status": "",   # Статус второй пары (Open, Short)
                    "len": "",      # Длина второй пары в метрах
                }
            }

        """

        if not request.GET.get("port"):
            raise ValidationError({"detail": "Неверные данные"})

        # Находим оборудование
        device = get_object_or_404(models.Devices, name=device_name)
        self.check_object_permissions(request, device)

        # Если оборудование недоступно
        if not device.available:
            return Response({"detail": "Device unavailable"}, status=500)

        try:
            cable_test = device.connect().virtual_cable_test(request.GET["port"])
        except InvalidMethod:
            return Response({"detail": "Unsupported for this device"}, status=400)
        else:
            return Response(cable_test)


@method_decorator(profile_permission(models.Profile.BRAS), name="dispatch")
class SetPoEAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, DevicePermission]
    serializer_class = PoEPortStatusSerializer

    @except_connection_errors
    def post(self, request, device_name):
        """
        ## Устанавливает PoE статус на порту
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Находим оборудование
        device = get_object_or_404(models.Devices, name=device_name)
        self.check_object_permissions(request, device)

        # Если оборудование недоступно
        if not device.available:
            return Response({"detail": "Device unavailable"}, status=500)

        poe_status = serializer.validated_data["status"]
        port_name = serializer.validated_data["port"]

        try:
            _, err = device.connect().set_poe_out(port_name, poe_status)
        except InvalidMethod:
            return Response({"detail": "Unsupported for this device"}, status=400)
        else:
            if not err:
                return Response({"status": poe_status})
            return Response(
                {"detail": f"Invalid data ({poe_status})"},
                status=400,
            )


class InterfaceInfoAPIView(APIView):
    permission_classes = [IsAuthenticated, DevicePermission]

    @except_connection_errors
    def get(self, request, device_name):
        """
        ## Общая информация об определенном порте оборудования

        В зависимости от типа оборудования информация будет совершенно разной

        Поле `portDetailInfo.type` указывает тип данных, которые могут быть строкой, JSON, или HTML кодом.

            {
                "portDetailInfo": {
                    "type": "text",  - Тип данных для детальной информации о порте
                    "data": ""       - Сами данные
                },
                "portConfig":   "Конфигурация порта (из файла конфигурации)",
                "portType":     "COPPER"    - (SFP, COMBO),
                "portErrors":   "Ошибки на порту",
                "hasCableDiag": true        - Имеется ли на данном типе оборудования возможность диагностики порта
            }


        """

        port = self.request.GET.get("port")
        if not port:
            raise ValidationError({"detail": "Укажите порт!"})

        device = get_object_or_404(models.Devices, name=device_name)
        self.check_object_permissions(request, device)

        # Если оборудование недоступно
        if not device.available:
            return Response({"detail": "Device unavailable"}, status=500)

        result = {}
        session = device.connect()

        result["portDetailInfo"] = session.get_port_info(port)
        result["portConfig"] = session.get_port_config(port)
        result["portType"] = session.get_port_type(port)
        result["portErrors"] = session.get_port_errors(port)
        result["hasCableDiag"] = True

        return Response(result)


@method_decorator(profile_permission(models.Profile.BRAS), name="dispatch")
class ChangeDSLProfileAPIView(APIView):
    permission_classes = [IsAuthenticated, DevicePermission]

    @except_connection_errors
    def post(self, request, device_name: str):
        """
        ## Изменяем профиль xDSL порта на другой

        Возвращаем `{ "status": status }` или `{ "error": error }`

        """

        serializer = ADSLProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        device = get_object_or_404(models.Devices, name=device_name)
        self.check_object_permissions(request, device)

        # Если оборудование недоступно
        if not device.available:
            return Response({"detail": "Device unavailable"}, status=500)

        # Подключаемся к оборудованию
        session = device.connect()
        try:
            status = session.change_profile(
                serializer.validated_data["port"],
                serializer.validated_data["index"],
            )
        except InvalidMethod:
            # Нельзя менять профиль для данного устройства
            return Response({"error": "Device can't change profile"}, status=400)
        else:
            return Response({"status": status})


class CreateInterfaceCommentAPIView(generics.CreateAPIView):
    serializer_class = InterfacesCommentsSerializer

    def perform_create(self, serializer):
        dev = get_object_or_404(models.Devices, name=self.request.data.get("device"))
        serializer.save(user=self.request.user, device=dev)


class InterfaceCommentAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.InterfacesComments.objects.all()
    serializer_class = InterfacesCommentsSerializer
    lookup_field = "pk"
    lookup_url_kwarg = "pk"
