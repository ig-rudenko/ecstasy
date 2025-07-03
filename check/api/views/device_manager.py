from django.utils.decorators import method_decorator
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from check import models
from check.logging import log
from check.permissions import profile_permission
from check.services.device.interfaces import (
    change_port_state,
    set_interface_description,
    get_mac_addresses_on_interface,
    get_interface_detail_info,
    check_user_interface_permission,
)
from devicemanager.remote.exceptions import InvalidMethod
from .base import DeviceAPIView
from ..decorators import except_connection_errors
from ..permissions import DevicePermission
from ..serializers import (
    InterfacesCommentsSerializer,
    ADSLProfileSerializer,
    PortControlSerializer,
    PoEPortStatusSerializer,
    DeviceCommandsSerializer,
)
from ..swagger import schemas
from ..swagger.schemas import (
    mac_list_api_doc,
    interface_info_api_doc,
    change_dsl_profile_api_doc,
    change_description_api_doc,
)
from ...models import DeviceCommand
from ...services.device.commands import execute_command, validate_command


@method_decorator(schemas.port_control_api_doc, name="post")  # API DOC
class InterfaceControlAPIView(DeviceAPIView):
    serializer_class = PortControlSerializer

    @except_connection_errors
    @method_decorator(profile_permission(models.Profile.REBOOT))
    def post(self, request: Request, *args, **kwargs):
        """
        ## Изменяем состояние порта оборудования
        """

        # Проверяем данные, полученные в запросе, с помощью сериализатора.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        port_status: str = serializer.validated_data["status"]
        port_name: str = serializer.validated_data["port"]
        save_config: bool = serializer.validated_data["save"]

        device: models.Devices = self.get_object()

        # Есть ли у пользователя доступ к группе данного оборудования.
        self.check_object_permissions(request, device)

        # Есть ли у пользователя доступ к порту данного оборудования.
        interface = check_user_interface_permission(self.current_user, device, port_name, action=port_status)

        change_status = change_port_state(
            device, port_name=port_name, port_status=port_status, save_config=save_config
        )

        # Логи
        log(self.current_user, device, f"{port_status} port {port_name} ({interface.desc}) \n{change_status}")

        return Response(serializer.validated_data, status=200)


@method_decorator(change_description_api_doc, name="post")
class ChangeDescriptionAPIView(DeviceAPIView):
    """
    ## Изменяем описание на порту у оборудования
    """

    @except_connection_errors
    @method_decorator(profile_permission(models.Profile.BRAS))
    def post(self, request: Request, *args, **kwargs):
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

        port = self.request.data.get("port", "")
        new_description = self.request.data.get("description", "")
        if not port:
            raise ValidationError({"detail": "Необходимо указать порт"})

        device: models.Devices = self.get_object()

        # Проверяем права доступа пользователя к оборудованию
        self.check_object_permissions(request, device)
        # Проверяем права доступа пользователя к порту.
        check_user_interface_permission(self.current_user, device, port)

        description_status = set_interface_description(
            device, interface_name=port, description=new_description
        )

        log(self.current_user, device, str(description_status))

        return Response(
            {
                "description": description_status.description,
                "port": description_status.port,
                "saved": description_status.saved,
            }
        )


@method_decorator(mac_list_api_doc, name="get")
class MacListAPIView(DeviceAPIView):
    permission_classes = [IsAuthenticated, DevicePermission]

    @except_connection_errors
    def get(self, request: Request, *args, **kwargs):
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
                        "vlanName": "Описание VLAN"
                    },
                    ...
                ]
            }

        """

        port: str = self.request.GET.get("port", "")
        if not port:
            raise ValidationError({"detail": "Укажите порт!"})

        device: models.Devices = self.get_object()

        macs = get_mac_addresses_on_interface(device, port)

        return Response({"count": len(macs), "result": macs})


class CableDiagAPIView(DeviceAPIView):
    @except_connection_errors
    def get(self, request: Request, *args, **kwargs):
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
        device: models.Devices = self.get_object()

        # Если оборудование недоступно
        if not device.available:
            return Response({"detail": "Device unavailable"}, status=500)

        try:
            cable_test = device.connect().virtual_cable_test(request.GET["port"])
        except InvalidMethod:
            return Response({"detail": "Unsupported for this device"}, status=400)
        else:
            return Response(cable_test)


class SetPoEAPIView(DeviceAPIView):
    serializer_class = PoEPortStatusSerializer

    @except_connection_errors
    @method_decorator(profile_permission(models.Profile.BRAS))
    def post(self, request: Request, *args, **kwargs):
        """Устанавливает PoE статус на порту"""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        poe_status = serializer.validated_data["status"]
        port_name = serializer.validated_data["port"]

        # Находим оборудование
        device = self.get_object()

        # Если оборудование недоступно
        if not device.available:
            return Response({"detail": "Device unavailable"}, status=500)

        try:
            _, err = device.connect().set_poe_out(port_name, poe_status)
        except InvalidMethod:
            return Response({"detail": "Unsupported for this device"}, status=400)
        else:
            if not err:
                return Response({"status": poe_status})
            return Response({"detail": f"Invalid data ({poe_status})"}, status=400)


@method_decorator(interface_info_api_doc, name="get")
class InterfaceInfoAPIView(DeviceAPIView):
    @except_connection_errors
    def get(self, request: Request, *args, **kwargs):
        """
        ## Общая информация об определенном порте оборудования

        В зависимости от типа оборудования информация будет совершенно разной

        Поле `portDetailInfo.type` указывает тип данных, которые могут быть Строкой или Объектом.
        Возможные значения: "text", "html", "error", "adsl", "gpon", "eltex-gpon", "mikrotik".

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

        device = self.get_object()

        result = get_interface_detail_info(device, port)  # Получаем информацию о порте

        return Response(result)


@method_decorator(change_dsl_profile_api_doc, name="post")
class ChangeDSLProfileAPIView(DeviceAPIView):
    permission_classes = [IsAuthenticated, DevicePermission]
    serializer_class = ADSLProfileSerializer

    @except_connection_errors
    @method_decorator(profile_permission(models.Profile.BRAS))
    def post(self, request, *args, **kwargs):
        """
        Изменяем профиль xDSL порта на другой

        Возвращаем `{ "status": status }` или `{ "error": error }`
        """

        serializer = ADSLProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        device = self.get_object()

        # Если оборудование недоступно
        if not device.available:
            return Response({"detail": "Device unavailable"}, status=500)

        # Подключаемся к оборудованию
        session = device.connect()
        try:
            status = session.change_profile(
                serializer.validated_data["port"], serializer.validated_data["index"]
            )
        except InvalidMethod:
            # Нельзя менять профиль для данного устройства
            return Response({"error": "Device can't change profile"}, status=400)
        else:
            return Response({"status": status})


class CreateInterfaceCommentAPIView(generics.CreateAPIView):
    serializer_class = InterfacesCommentsSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class InterfaceCommentAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.InterfacesComments.objects.all()
    serializer_class = InterfacesCommentsSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"
    lookup_url_kwarg = "pk"


class DeviceCommandsListAPIView(DeviceAPIView):
    serializer_class = DeviceCommandsSerializer
    permission_classes = [IsAuthenticated, DevicePermission]

    @method_decorator(profile_permission(models.Profile.CMD_RUN))
    def get(self, request, *args, **kwargs):
        device = self.get_object()
        commands = DeviceCommand.objects.filter(device_vendor=device.vendor)
        if not request.user.is_superuser:
            commands = commands.filter(perm_groups__user=request.user)

        serializer = self.get_serializer(commands, many=True)
        return Response(serializer.data)


class ExecuteDeviceCommandAPIView(DeviceAPIView):
    permission_classes = [IsAuthenticated, DevicePermission]

    @except_connection_errors
    @method_decorator(profile_permission(models.Profile.CMD_RUN))
    def post(self, request, *args, **kwargs) -> Response:
        device = self.get_object()
        commands = DeviceCommand.objects.filter(id=self.kwargs["command_id"])
        if not request.user.is_superuser:
            commands = commands.filter(perm_groups__user=request.user)

        if not commands.exists():
            return Response({"detail": "Command not found"}, status=404)

        command = commands.first()
        if command is None:
            return Response({"detail": "Command not found"}, status=404)

        try:
            output: str = execute_command(device, command, request.data)
        except InvalidMethod:
            return Response({"detail": "Unsupported for this device"}, status=400)
        except ValidationError as exc:
            return Response({"detail": exc.detail}, status=400)
        else:
            return Response({"output": output})


class ValidateDeviceCommandAPIView(DeviceAPIView):
    permission_classes = [IsAuthenticated, DevicePermission]

    @except_connection_errors
    @method_decorator(profile_permission(models.Profile.CMD_RUN))
    def post(self, request, *args, **kwargs) -> Response:
        device = self.get_object()
        commands = DeviceCommand.objects.filter(id=self.kwargs["command_id"])
        if not request.user.is_superuser:
            commands = commands.filter(perm_groups__user=request.user)

        if not commands.exists():
            return Response({"detail": "Command not found"}, status=404)

        command = commands.first()
        if command is None:
            return Response({"detail": "Command not found"}, status=404)

        try:
            valid_command: str = validate_command(device, command.command, request.data)
        except InvalidMethod:
            return Response({"detail": "Unsupported for this device"}, status=400)
        except ValidationError as exc:
            return Response({"detail": exc.detail}, status=400)
        else:
            return Response({"command": valid_command})
