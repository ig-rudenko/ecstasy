import re
from functools import lru_cache
from typing import Literal, Dict, Optional

import orjson
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from check import models
from check.logging import log
from check.permissions import profile_permission
from devicemanager.device import Interfaces
from devicemanager.remote.exceptions import InvalidMethod
from net_tools.models import VlanName, DevicesInfo
from ..decorators import except_connection_errors
from ..permissions import DevicePermission
from ..serializers import (
    InterfacesCommentsSerializer,
    ADSLProfileSerializer,
    PortControlSerializer,
    PoEPortStatusSerializer,
)
from ..swagger import schemas
from ...models import Profile


class PortGuardCheckMixin:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.port_desc = ""
        self.profile: Optional[Profile] = None

    def check_object_permissions(self, request, obj):
        # Смотрим интерфейсы, которые сохранены в БД
        dev_info, _ = DevicesInfo.objects.get_or_create(dev=obj)

        if dev_info.interfaces is None:
            # Собираем интерфейсы с оборудования.
            interfaces = Interfaces(obj.connect().get_interfaces())
        else:
            # Преобразовываем JSON строку с интерфейсами в класс `Interfaces`
            interfaces = Interfaces(orjson.loads(dev_info.interfaces))

        # Далее смотрим описание на порту, так как от этого будет зависеть, может ли пользователь управлять им
        self.port_desc: str = interfaces[self.request.data["port"]].desc

        # Если не суперпользователь, то нельзя изменять состояние определенных портов
        try:
            self.profile: Profile = Profile.objects.get(user=self.request.user)
        except Profile.DoesNotExist:
            raise PermissionDenied(
                detail="У вас нет профиля для выполнения данного действия!",
            )

        # Если в профиле пользователя стоит ограничение на определенные порты
        if self.profile.port_guard_pattern and re.search(
            self.profile.port_guard_pattern, self.port_desc, flags=re.IGNORECASE
        ):
            raise PermissionDenied(
                detail="Запрещено изменять состояние данного порта!",
            )


@method_decorator(schemas.port_control_api_doc, name="post")  # API DOC
@method_decorator(profile_permission(models.Profile.REBOOT), name="dispatch")
class PortControlAPIView(PortGuardCheckMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated, DevicePermission]
    serializer_class = PortControlSerializer

    @except_connection_errors
    def post(self, request, device_name: str):
        """
        ## Изменяем состояние порта оборудования
        """

        # Проверяем данные, полученные в запросе, с помощью сериализатора.
        serializer: PortControlSerializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        port_status: Literal["up", "down", "reload"] = serializer.validated_data[
            "status"
        ]
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
        super().check_object_permissions(request, device)

        # Если недостаточно привилегий для изменения статуса порта
        if (
            self.profile
            and self.profile.perm_level < 2
            and request.data["status"] in ["up", "down"]
        ):
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
class ChangeDescriptionAPIView(PortGuardCheckMixin, APIView):
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

        set_description_status = dev.connect().set_description(
            port=port, desc=new_description
        )

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

        macs = []  # Итоговый список
        for vid, mac in device.connect().get_mac(port):  # Смотрим VLAN и MAC
            macs.append(
                {
                    "vlanID": vid,
                    "mac": mac,
                    "vlanName": self.get_vlan_name(vid),
                }
            )

        return Response({"count": len(macs), "result": macs})

    @staticmethod
    @lru_cache(maxsize=35)
    def get_vlan_name(vlan_id: int) -> str:
        try:
            return VlanName.objects.get(vid=int(vlan_id)).name
        except (ValueError, VlanName.DoesNotExist):
            return ""


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

        if result["portDetailInfo"].get("type") == "gpon":
            # Ищем возможные комментарии только для GPON типа
            result["portDetailInfo"]["data"][
                "onts_lines"
            ] = self.create_onts_lines_with_comments(
                result["portDetailInfo"]["data"].get("onts_lines", []),
                gpon_port=port,
                device=device,
            )

        return Response(result)

    @staticmethod
    def create_onts_lines_with_comments(
        onts_lines: list, gpon_port: str, device: models.Devices
    ) -> list:
        """
        Находит комментарии созданные на ONT для порта `gpon_port` оборудования `device`.

        :param onts_lines: Текущий список данных ONT.
        :param gpon_port: Основной GPON порт.
        :param device: Оборудование, на котором надо искать комментарии.
        :return: Список данных ONT с добавлением в конец списка возможных комментариев.
        """
        if not onts_lines:
            return []

        interfaces_comments = device.interfacescomments_set.select_related("user")

        ont_interfaces_dict: Dict[str, list] = {}

        for comment in interfaces_comments:
            comment_data = {
                "text": comment.comment,
                "user": comment.user.username,
                "id": comment.id,
            }
            if ont_interfaces_dict.get(comment.interface):
                ont_interfaces_dict[comment.interface].append(comment_data)
            else:
                ont_interfaces_dict[comment.interface] = [comment_data]

        new_onts_lines = []

        for line in onts_lines:
            # Соединяем порт GPON и ONTid
            ont_full_port = f"{gpon_port}/{line[0]}"
            # Добавляем комментарии либо пустой список в конец
            new_onts_lines.append(
                line
                + [
                    ont_interfaces_dict.get(ont_full_port, []),
                ]
            )
        return new_onts_lines


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
