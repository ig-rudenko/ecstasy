from re import findall
from typing import Any

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.gathering.models import Vlan, VlanPort

from ..models import (
    AuthGroup,
    BulkDeviceCommandExecution,
    BulkDeviceCommandExecutionResult,
    DeviceCommand,
    DeviceGroup,
    DeviceMedia,
    Devices,
    InterfacesComments,
    UsersActions,
)


class DevicesSerializer(serializers.ModelSerializer):
    """
    ## Класс сериализатора модели Devices
    """

    group = serializers.CharField(source="group.name")
    auth_group = serializers.PrimaryKeyRelatedField(queryset=AuthGroup.objects.all(), write_only=True)
    console_url = serializers.URLField(read_only=True)

    class Meta:
        model = Devices
        fields = [
            "id",
            "ip",
            "name",
            "vendor",
            "group",
            "auth_group",
            "model",
            "serial_number",
            "os_version",
            "port_scan_protocol",
            "cmd_protocol",
            "active",
            "collect_interfaces",
            "collect_mac_addresses",
            "collect_vlan_info",
            "collect_configurations",
            "connection_pool_size",
            "console_url",
        ]

    def create(self, validated_data: Any):
        group_name_dict: dict[str, str] = validated_data.pop("group", None)
        if group_name_dict is None:
            raise ValidationError("Group name is required")

        try:
            group = DeviceGroup.objects.get(name=group_name_dict["name"])
        except DeviceGroup.DoesNotExist as exc:
            raise ValidationError(f"Group {group_name_dict["name"]} does not exist") from exc
        validated_data["group"] = group
        return super().create(validated_data)


class DeviceGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceGroup
        fields = ["id", "name", "description"]


class DeviceAuthGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthGroup
        fields = ["id", "name", "description"]


class DevicesDetailUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Devices
        fields = [
            "id",
            "ip",
            "name",
            "model",
            "vendor",
            "serial_number",
            "os_version",
            "auth_group",
            "group",
            "snmp_community",
            "port_scan_protocol",
            "cmd_protocol",
            "interface_pattern",
            "active",
            "collect_interfaces",
            "collect_mac_addresses",
            "collect_vlan_info",
            "collect_configurations",
            "connection_pool_size",
        ]


class DevicesDetailSerializer(DevicesDetailUpdateSerializer):
    group = DeviceGroupSerializer()
    auth_group = DeviceAuthGroupSerializer()


class DeviceMediaSerializer(serializers.ModelSerializer):
    url = serializers.URLField(source="file.url", read_only=True)
    name = serializers.CharField(source="file_name", read_only=True)
    is_image = serializers.BooleanField(read_only=True)
    file = serializers.FileField(write_only=True)

    class Meta:
        model = DeviceMedia
        fields = [
            "id",
            "file",
            "name",
            "file_type",
            "is_image",
            "description",
            "mod_time",
            "url",
        ]
        read_only_fields = ["id", "mod_time", "file_type"]


class InterfacesCommentsSerializer(serializers.ModelSerializer):
    device = serializers.SlugRelatedField(
        slug_field="name",
        help_text="Название оборудования",
        queryset=Devices.objects.all(),
    )

    class Meta:
        model = InterfacesComments
        fields = ["id", "interface", "comment", "user", "device"]
        read_only_fields = ["id", "user"]


class MacSerializer(serializers.Serializer):
    mac = serializers.CharField(max_length=24, required=True)

    @staticmethod
    def validate_mac(value: str) -> str:
        """
        ## Удаляет все не шестнадцатеричные символы из строки MAC адреса

        Возвращает MAC в виде строки - `0011-2233-4455`.
        """
        mac_letters = findall(r"\w", value)
        if len(mac_letters) == 12:
            mac = "".join(mac_letters).lower()
            return "{}{}{}{}-{}{}{}{}-{}{}{}{}".format(*mac)
        raise ValidationError("Неверный MAC")


class BrassSessionSerializer(MacSerializer):
    """
    ## Проверка правильности ввода данных для работы с пользовательскими сессиями BRAS

    Требуемые поля:
     - str:`mac` - max:24
     - str:`device` - max:255
     - str:`port` - max:50
    """

    device = serializers.CharField(max_length=255, required=False, default="", allow_blank=True)
    port = serializers.CharField(max_length=50, required=False, default="", allow_blank=True)


class ADSLProfileSerializer(serializers.Serializer):
    """
    ## Проверка правильности ввода данных для смены xDSL профиля на оборудовании

    Требуемые поля:
     - int:`index` >= 0
     - str:`port` - max:50
    """

    index = serializers.IntegerField(min_value=0)
    port = serializers.CharField(max_length=50, required=True)


class RequiredBooleanField(serializers.BooleanField):
    default_empty_html = serializers.empty


class PortControlSerializer(serializers.Serializer):
    """
    ## Cериализатор для изменения статуса порта
    """

    port = serializers.CharField(max_length=50, required=True)
    status = serializers.ChoiceField(choices=["up", "down", "reload"], required=True)
    save = RequiredBooleanField(required=True)  # type: ignore


class PoEPortStatusSerializer(serializers.Serializer):
    port = serializers.CharField(max_length=50, required=True)
    status = serializers.ChoiceField(choices=["auto-on", "forced-on", "off"], required=True)


class ConfigFileSerializer(serializers.Serializer):
    name = serializers.CharField()
    size = serializers.IntegerField()
    modTime = serializers.CharField()


class UserDeviceActionSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user__username")

    class Meta:
        model = UsersActions
        fields = ["time", "user", "action"]


class DeviceVlanPortSerializer(serializers.ModelSerializer):
    class Meta:
        model = VlanPort
        fields = ["port", "desc"]


class DeviceVlanSerializer(serializers.ModelSerializer):
    ports = DeviceVlanPortSerializer(many=True)

    class Meta:
        model = Vlan
        fields = ["ports", "vlan", "desc", "datetime"]


class DeviceCommandsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceCommand
        fields = ["id", "name", "description", "command", "device_vendor"]


class DeviceViewingsSerializer(serializers.Serializer):
    username = serializers.CharField(read_only=True)
    started = serializers.DateTimeField(read_only=True)
    updated = serializers.DateTimeField(read_only=True)

    class Meta:
        fields = ["username", "started", "updated"]


class BulkDeviceCommandExecutionResultSerializer(serializers.ModelSerializer):
    """Serialize one persisted bulk command result row."""

    deviceId = serializers.IntegerField(source="device_id", allow_null=True)
    deviceName = serializers.CharField(source="device_name")
    commandText = serializers.CharField(source="command_text")

    class Meta:
        model = BulkDeviceCommandExecutionResult
        fields = [
            "id",
            "deviceId",
            "deviceName",
            "status",
            "commandText",
            "output",
            "detail",
            "error",
            "duration",
            "created_at",
            "updated_at",
        ]


class BulkDeviceCommandExecutionSerializer(serializers.ModelSerializer):
    """Serialize one persisted bulk command execution with nested results."""

    user = serializers.CharField(source="user.username")
    commandId = serializers.IntegerField(source="command_id", allow_null=True)
    commandName = serializers.CharField(source="command_name")
    commandBody = serializers.CharField(source="command_body")
    launchedAt = serializers.DateTimeField(source="launched_at")
    finishedAt = serializers.DateTimeField(source="finished_at", allow_null=True)
    successCount = serializers.SerializerMethodField()
    errorCount = serializers.SerializerMethodField()
    skippedCount = serializers.SerializerMethodField()

    class Meta:
        model = BulkDeviceCommandExecution
        fields = [
            "id",
            "task_id",
            "user",
            "commandId",
            "commandName",
            "commandBody",
            "context",
            "status",
            "progress",
            "processed",
            "total",
            "launchedAt",
            "finishedAt",
            "successCount",
            "errorCount",
            "skippedCount",
        ]

    @staticmethod
    def get_successCount(obj: BulkDeviceCommandExecution) -> int:
        """Return count of successful device runs."""
        return sum(1 for result in obj.results.all() if result.status == result.STATUS_SUCCESS)

    @staticmethod
    def get_errorCount(obj: BulkDeviceCommandExecution) -> int:
        """Return count of failed device runs."""
        return sum(1 for result in obj.results.all() if result.status == result.STATUS_ERROR)

    @staticmethod
    def get_skippedCount(obj: BulkDeviceCommandExecution) -> int:
        """Return count of skipped device runs."""
        return sum(1 for result in obj.results.all() if result.status == result.STATUS_SKIPPED)
