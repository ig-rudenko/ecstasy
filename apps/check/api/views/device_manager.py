import re

from django.utils.decorators import method_decorator
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.notifications.services.notifications_render import run_device_trigger
from apps.notifications.services.triggers import TriggerNames
from devicemanager.remote.connector import pool_controller
from devicemanager.remote.exceptions import InvalidMethod
from ecstasy_project.types.api import UserAuthenticatedAPIView

from ... import models
from ...logging import log
from ...models import DeviceCommand
from ...permissions import profile_permission
from ...services.device.commands import (
    dispatch_bulk_execute_command_task,
    execute_command,
    get_available_command_for_device,
    get_available_commands_for_device,
    get_device_command_task_results,
    validate_command,
)
from ...services.device.interfaces import (
    change_port_state,
    check_user_interface_permission,
    get_interface_detail_info,
    get_mac_addresses_on_interface,
    set_interface_description,
)
from ...services.filters import filter_devices_qs_by_user
from ..decorators import except_connection_errors
from ..permissions import has_user_access_to_device
from ..serializers import (
    ADSLProfileSerializer,
    BulkDeviceCommandExecutionSerializer,
    BulkDeviceCommandExecutionResultSerializer,
    DeviceCommandsSerializer,
    InterfacesCommentsSerializer,
    PoEPortStatusSerializer,
    PortControlSerializer,
)
from ..swagger import schemas
from ..swagger.schemas import (
    change_description_api_doc,
    change_dsl_profile_api_doc,
    get_device_pool_status_api_doc,
    interface_info_api_doc,
    mac_list_api_doc,
)
from .base import DeviceAPIView
from .paginators import BulkDeviceCommandExecutionPagination, BulkDeviceCommandExecutionResultPagination


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

        # Запускаем триггер на изменение статуса порта.
        run_device_trigger(
            TriggerNames.get_name_for_device_port_status(port_status),
            request,
            device,
            action_result={**serializer.validated_data, "status": change_status},
        )

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

        # Логи
        log(self.current_user, device, str(description_status))

        # Запускаем триггер на изменение описания порта.
        run_device_trigger(
            TriggerNames.device_port_change_description,
            request,
            device,
            action_result=description_status,
        )

        return Response(
            {
                "description": description_status.description,
                "port": description_status.port,
                "saved": description_status.saved,
            }
        )


@method_decorator(mac_list_api_doc, name="get")
class MacListAPIView(DeviceAPIView):
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

        return Response(cable_test)


class SetPoEAPIView(DeviceAPIView):
    serializer_class = PoEPortStatusSerializer

    @except_connection_errors
    @method_decorator(profile_permission(models.Profile.BRAS))
    def post(self, request: Request, *args, **kwargs):
        """Устанавливает PoE статус на порту"""
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        poe_status = serializer.validated_data["status"]
        port_name = serializer.validated_data["port"]

        # Находим оборудование
        device = self.get_object()
        result = self.change_poe_status(device, port=port_name, poe_status=poe_status)

        # Запускаем триггер на изменение PoE порта.
        run_device_trigger(
            TriggerNames.device_port_set_poe_status,
            request,
            device,
            action_result=result,
        )

        return Response(result)

    @staticmethod
    def change_poe_status(device, port: str, poe_status: str) -> tuple[dict, int]:
        error_status = 0
        result: dict = {"status": poe_status, "port_name": port}

        # Если оборудование недоступно
        if not device.available:
            error_status = 500
            result["detail"] = "Device unavailable"

        if not error_status:
            try:
                _, got_error = device.connect().set_poe_out(port, poe_status)
            except InvalidMethod:
                error_status = 400
                result["detail"] = "Unsupported for this device"
            else:
                if got_error:
                    error_status = 400
                    result["detail"] = f"Invalid data ({poe_status})"

        result["has_error"] = bool(error_status)

        return result, error_status


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
            change_profile_status = session.change_profile(
                serializer.validated_data["port"], serializer.validated_data["index"]
            )
        except InvalidMethod:
            # Нельзя менять профиль для данного устройства
            return Response({"error": "Device can't change profile"}, status=400)

        # Запускаем триггер на изменение ADSL профиля.
        run_device_trigger(
            TriggerNames.device_port_change_adsl_profile,
            request,
            device,
            action_result={**serializer.validated_data, "status": change_profile_status},
        )

        return Response({"status": change_profile_status})


class CreateInterfaceCommentAPIView(generics.CreateAPIView):
    serializer_class = InterfacesCommentsSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if not has_user_access_to_device(self.request.user, serializer.validated_data["device"]):
            self.permission_denied(self.request, message="У вас нет доступа к данному устройству")
        serializer.save(user=self.request.user)


class InterfaceCommentAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.InterfacesComments.objects.all().select_related("device")
    serializer_class = InterfacesCommentsSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"
    lookup_url_kwarg = "pk"


class DeviceCommandsListAPIView(DeviceAPIView):
    serializer_class = DeviceCommandsSerializer

    @method_decorator(profile_permission(models.Profile.CMD_RUN))
    def get(self, request, *args, **kwargs):
        """Return available commands for the selected device."""
        device = self.get_object()
        serializer = self.get_serializer(
            get_available_commands_for_device(self.current_user, device), many=True
        )
        return Response(serializer.data)


class ExecuteDeviceCommandAPIView(DeviceAPIView):
    @except_connection_errors
    @method_decorator(profile_permission(models.Profile.CMD_RUN))
    def post(self, request, *args, **kwargs) -> Response:
        """Execute a command on a single device."""
        device = self.get_object()
        command = get_available_command_for_device(self.current_user, device, int(self.kwargs["command_id"]))
        if command is None:
            return Response({"detail": "Command not found"}, status=404)

        try:
            output: str = execute_command(device, command, request.data)
        except InvalidMethod:
            return Response({"detail": "Unsupported for this device"}, status=400)
        except ValidationError as exc:
            return Response({"detail": exc.detail}, status=400)

        # Если есть проверка выполнения команды.
        if not command.valid_regexp or re.compile(command.valid_regexp).search(output):
            return Response({"output": output})

        # Неверное выполнение команды
        return Response({"detail": output}, status=500)


class ValidateDeviceCommandAPIView(DeviceAPIView):
    @except_connection_errors
    @method_decorator(profile_permission(models.Profile.CMD_RUN))
    def post(self, request, *args, **kwargs) -> Response:
        """Validate a command for a single device."""
        device = self.get_object()
        command = get_available_command_for_device(self.current_user, device, int(self.kwargs["command_id"]))
        if command is None:
            return Response({"detail": "Command not found"}, status=404)

        try:
            valid_command = validate_command(device, command.command, request.data)
        except InvalidMethod:
            return Response({"detail": "Unsupported for this device"}, status=400)
        except ValidationError as exc:
            return Response({"detail": exc.detail}, status=400)

        return Response({"command": valid_command})


class ExecuteBulkDeviceCommandAPIView(UserAuthenticatedAPIView):
    """Start background execution of a command on multiple devices."""

    @schemas.execute_bulk_device_command_api_doc
    @method_decorator(profile_permission(models.Profile.CMD_RUN))
    def post(self, request, *args, **kwargs) -> Response:
        """Validate request and dispatch celery task."""
        command = self.get_command()
        if command is None:
            return Response({"detail": "Command not found"}, status=404)

        device_ids = self.get_device_ids(request.data.get("device_ids"))
        context = dict(request.data)
        context.pop("device_ids", None)

        requested_devices = {
            device.id: device
            for device in filter_devices_qs_by_user(
                models.Devices.objects.filter(id__in=device_ids).select_related("auth_group"),
                self.current_user,
            )
        }

        devices = []
        skipped = []
        for device_id in device_ids:
            device = requested_devices.get(device_id)
            if device is None:
                skipped.append(
                    {
                        "deviceId": device_id,
                        "detail": "Device not found or access denied",
                    }
                )
                continue
            devices.append(device)

        try:
            result = dispatch_bulk_execute_command_task(command, devices, context, self.current_user.id)
        except ValidationError as exc:
            return Response(exc.detail, status=400)

        result["skipped"] = [*result["skipped"], *skipped]
        return Response(result, status=status.HTTP_202_ACCEPTED)

    def get_command(self) -> DeviceCommand | None:
        """Return command available for the current user."""
        commands = DeviceCommand.objects.filter(id=self.kwargs["command_id"])
        if not self.current_user.is_superuser:
            commands = commands.filter(perm_groups__user=self.current_user)
        return commands.distinct().first()

    @staticmethod
    def get_device_ids(device_ids: object) -> list[int]:
        """Validate requested device identifiers."""
        if not isinstance(device_ids, list) or not device_ids:
            raise ValidationError({"device_ids": "Необходимо передать непустой список ID оборудования"})

        validated_ids = []
        for device_id in device_ids:
            try:
                validated_ids.append(int(device_id))
            except (TypeError, ValueError) as exc:
                raise ValidationError({"device_ids": "ID оборудования должны быть целыми числами"}) from exc

        return validated_ids


class BulkDeviceCommandTaskAPIView(UserAuthenticatedAPIView):
    """Return celery status for bulk device command task."""

    @schemas.bulk_device_command_task_status_api_doc
    @method_decorator(profile_permission(models.Profile.CMD_RUN))
    def get(self, request, *args, **kwargs) -> Response:
        """Return current task state, progress and cached results."""
        task_id = str(self.kwargs["task_id"])
        results_map = get_device_command_task_results(task_id)
        sorted_results = self.get_sorted_results(results_map)
        execution = self.get_execution(task_id)
        task_status = self.get_task_status(execution)

        response = {
            "taskId": task_id,
            "status": task_status,
            "resultsCount": len(results_map),
            "resultDeviceIds": [result["deviceId"] for result in sorted_results],
            "results": sorted_results,
        }
        if execution is not None:
            response.update(
                {
                    "progress": execution.progress,
                    "processed": execution.processed,
                    "total": execution.total,
                }
            )
        return Response(response)

    @staticmethod
    def get_sorted_results(results_map: dict[str, dict]) -> list[dict]:
        """Return sorted cached results."""
        sorted_items = sorted(
            results_map.items(),
            key=lambda item: int(item[0]),
        )

        return [
            {
                "deviceId": result.get("device_id", int(device_id)),
                "deviceName": result.get("device_name", ""),
                "status": result.get("status", "SUCCESS"),
                "commandId": result.get("command_id"),
                "commandText": result.get("command_text", ""),
                "output": result.get("output", ""),
                "detail": result.get("detail", ""),
                "error": result.get("error", ""),
                "duration": result.get("duration", 0),
            }
            for device_id, result in sorted_items
        ]

    def get_execution(self, task_id: str) -> models.BulkDeviceCommandExecution | None:
        """Return persisted execution record for the task."""
        queryset = models.BulkDeviceCommandExecution.objects.filter(task_id=task_id)
        if not self.current_user.is_superuser:
            queryset = queryset.filter(user=self.current_user)
        return queryset.first()

    @staticmethod
    def get_task_status(
        execution: models.BulkDeviceCommandExecution | None,
    ) -> str:
        """Return bulk task status from persisted execution state."""
        if execution is None:
            return "PENDING"
        return execution.status


class BulkDeviceCommandExecutionListAPIView(UserAuthenticatedAPIView, generics.ListAPIView):
    """Return persisted bulk command executions for audit history."""

    serializer_class = BulkDeviceCommandExecutionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = BulkDeviceCommandExecutionPagination

    @method_decorator(profile_permission(models.Profile.CMD_RUN))
    def get(self, request, *args, **kwargs):
        """List bulk command executions with nested device results."""
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """Return filtered execution history for the current user."""
        queryset = (
            models.BulkDeviceCommandExecution.objects.select_related("user", "command")
            .prefetch_related("results")
            .order_by("-launched_at")
        )

        if not self.current_user.is_superuser:
            queryset = queryset.filter(user=self.current_user)

        return queryset


class BulkDeviceCommandExecutionResultListAPIView(UserAuthenticatedAPIView, generics.ListAPIView):
    """Return persisted device results for one bulk command execution."""

    serializer_class = BulkDeviceCommandExecutionResultSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = BulkDeviceCommandExecutionResultPagination

    @method_decorator(profile_permission(models.Profile.CMD_RUN))
    def get(self, request, *args, **kwargs):
        """List paginated device results for one execution."""
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """Return filtered result rows for one execution."""
        execution_queryset = models.BulkDeviceCommandExecution.objects.all()
        if not self.current_user.is_superuser:
            execution_queryset = execution_queryset.filter(user=self.current_user)

        execution = generics.get_object_or_404(execution_queryset, pk=self.kwargs["execution_id"])
        queryset = execution.results.select_related("device", "execution").order_by("device_name", "id")

        search_query = str(self.request.query_params.get("search", "")).strip()
        if search_query:
            queryset = queryset.filter(device_name__icontains=search_query)

        return queryset


# @method_decorator(get_device_pool_status_api_doc, name="get")
class DevicePoolManager(DeviceAPIView):
    @get_device_pool_status_api_doc
    def get(self, request, *args, **kwargs):
        """
        Возвращает максимальное кол-во сессий в пуле подключений и список статусов работоспособности текущих пулов.
        """
        device = self.get_object()
        return Response(
            {
                "connectionPoolSize": device.connection_pool_size,
                "statuses": pool_controller.get_pool_status(device.ip),
            }
        )

    def delete(self, request, *args, **kwargs):
        """
        Очищает пул всех текущих подключений
        """
        device = self.get_object()
        if pool_controller.clear_pool(device.ip):
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
