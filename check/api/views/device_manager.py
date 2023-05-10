import orjson

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator

from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from check import models
from check.permissions import profile_permission
from devicemanager.device import Interfaces
from net_tools.models import VlanName, DevicesInfo

from ..serializers import (
    InterfacesCommentsSerializer,
    ADSLProfileSerializer,
    PortControlSerializer,
    PoEPortStatusSerializer,
)
from ..decorators import device_connection
from ..permissions import DevicePermission
from ..swagger import schemas
from ...logging import log


@method_decorator(schemas.port_control_api_doc, name="post")  # API DOC
@method_decorator(profile_permission(models.Profile.REBOOT), name="dispatch")
class PortControlAPIView(generics.GenericAPIView):
    permission_classes = [DevicePermission]
    serializer_class = PortControlSerializer

    @device_connection
    def post(self, request, device_name: str):
        """
        ## Изменяем состояние порта оборудования
        """

        # Проверяем данные, полученные в запросе, с помощью сериализатора.
        serializer: PortControlSerializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        port_status: str = serializer.validated_data["status"]
        port_name: str = serializer.validated_data["port"]
        save_config: bool = serializer.validated_data["save"]

        # Смотрим интерфейсы, которые сохранены в БД
        interfaces_storage = get_object_or_404(DevicesInfo, dev__name=device_name)
        # Преобразовываем JSON строку с интерфейсами в класс `Interfaces`
        interfaces = Interfaces(orjson.loads(interfaces_storage.interfaces))

        # Далее смотрим описание на порту, так как от этого будет зависеть, может ли пользователь управлять им
        port_desc: str = interfaces[port_name].desc

        # Если не суперпользователь, то нельзя изменять состояние определенных портов
        if not request.user.is_superuser and settings.PORT_GUARD_PATTERN.search(port_desc):
            return Response(
                {"error": "Запрещено изменять состояние данного порта!"},
                status=403,
            )

        model_dev = get_object_or_404(models.Devices, name=device_name)

        # Есть ли у пользователя доступ к группе данного оборудования
        self.check_object_permissions(request, model_dev)

        # Если недостаточно привилегий для изменения статуса порта
        if request.user.profile.perm_level < 2 and port_status in ["up", "down"]:
            # Логи
            log(
                request.user,
                model_dev,
                f'Tried to set port {port_name} ({serializer.validated_data["desc"]}) '
                f"to the {port_status} state, but was refused \n",
            )
            return Response(
                {"error": "У вас недостаточно прав, для изменения состояния порта!"},
                status=403,
            )

        # Если оборудование Недоступно
        if not model_dev.available:
            return Response({"error": "Оборудование недоступно!"}, status=500)

        # Теперь наконец можем подключиться к оборудованию :)
        with model_dev.connect() as session:
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

        # Логи
        log(
            request.user,
            model_dev,
            f"{port_status} port {port_name} ({port_desc}) \n{port_change_status}",
        )

        return Response(serializer.validated_data, status=200)


@method_decorator(profile_permission(models.Profile.BRAS), name="dispatch")
class ChangeDescription(APIView):
    """
    ## Изменяем описание на порту у оборудования
    """

    permission_classes = [DevicePermission]

    @device_connection
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

        new_description = self.request.data.get("description")
        port = self.request.data.get("port")

        with dev.connect() as session:
            set_description_status = session.set_description(port=port, desc=new_description)
            new_description = session.clear_description(new_description)

        if "Неверный порт" in set_description_status:
            return Response({"detail": f"Неверный порт {port}"}, status=400)

        # Проверяем результат изменения описания
        if "Max length" in set_description_status:
            # Описание слишком длинное.
            # Находим в строке "Max length:32" число "32"
            max_length = set_description_status.split(":")[1]
            if max_length.isdigit():
                max_length = int(max_length)
            else:
                max_length = 32
            raise ValidationError(
                {"detail": f"Слишком длинное описание! Укажите не более {max_length} символов."}
            )

        return Response({"description": new_description})


class MacListAPIView(APIView):
    permission_classes = [DevicePermission]

    @device_connection
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

        with device.connect() as session:
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
    permission_classes = [DevicePermission]

    @device_connection
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

        with device.connect() as session:
            if hasattr(session, "virtual_cable_test"):
                cable_test = session.virtual_cable_test(request.GET["port"])
                if cable_test:  # Если имеются данные
                    return Response(cable_test)
                return Response({})

            return Response({"detail": "Unsupported for this device"}, status=400)


@method_decorator(profile_permission(models.Profile.BRAS), name="dispatch")
class SetPoEAPIView(generics.GenericAPIView):
    permission_classes = [DevicePermission]
    serializer_class = PoEPortStatusSerializer

    @device_connection
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

        with device.connect() as session:
            if hasattr(session, "set_poe_out"):
                # Меняем PoE
                _, err = session.set_poe_out(port_name, poe_status)
                if not err:
                    return Response({"status": poe_status})
                return Response(
                    {"detail": f"Invalid data ({poe_status})"},
                    status=400,
                )

            return Response({"detail": "Unsupported for this device"}, status=400)


class InterfaceInfoAPIView(APIView):
    permission_classes = [DevicePermission]

    @device_connection
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
        with device.connect() as session:
            result["portDetailInfo"] = session.get_port_info(port)
            result["portConfig"] = session.get_port_config(port)
            result["portType"] = session.get_port_type(port)
            result["portErrors"] = session.get_port_errors(port)
            result["hasCableDiag"] = hasattr(session, "virtual_cable_test")

        return Response(result)


@method_decorator(profile_permission(models.Profile.BRAS), name="dispatch")
class ChangeDSLProfileAPIView(APIView):
    permission_classes = [DevicePermission]

    @device_connection
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
        with device.connect() as session:
            if hasattr(session, "change_profile"):
                # Если можно поменять профиль
                status = session.change_profile(
                    serializer.validated_data["port"],
                    serializer.validated_data["index"],
                )

                return Response({"status": status})

            # Нельзя менять профиль для данного устройства
            return Response({"error": "Device can't change profile"}, status=400)


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
