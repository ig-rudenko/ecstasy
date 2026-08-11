from rest_framework import serializers

from apps.gathering.models import DeviceGatheringResult, GatheringTask, MacAddress, Vlan, VlanPort


class GatheringTaskSummarySerializer(serializers.ModelSerializer):
    """Сериализовать запуск периодической задачи для строки результата."""

    class Meta:
        model = GatheringTask
        fields = [
            "id",
            "task_id",
            "name",
            "status",
            "total_devices",
            "error_type",
            "error_message",
            "started_at",
            "finished_at",
        ]


class GatheringResultDeviceSerializer(serializers.Serializer):
    """Сериализовать безопасную сводку оборудования без учетных данных."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    ip = serializers.CharField(read_only=True)
    vendor = serializers.CharField(read_only=True, allow_null=True)
    model = serializers.CharField(read_only=True, allow_null=True)
    group = serializers.SerializerMethodField()

    @staticmethod
    def get_group(obj) -> dict[str, int | str]:
        """Вернуть идентификатор и название группы оборудования."""

        return {"id": obj.group_id, "name": obj.group.name}


class DeviceGatheringResultSerializer(serializers.ModelSerializer):
    """Сериализовать результат опроса одного устройства."""

    task = GatheringTaskSummarySerializer(read_only=True)
    device = GatheringResultDeviceSerializer(read_only=True)

    class Meta:
        model = DeviceGatheringResult
        fields = [
            "id",
            "task",
            "device",
            "status",
            "error_type",
            "error_message",
            "started_at",
            "finished_at",
        ]


class MacAddressSerializer(serializers.ModelSerializer):
    """Serialize one collected MAC address row."""

    device_id = serializers.IntegerField(source="device.id", read_only=True)
    device_name = serializers.CharField(source="device.name", read_only=True)
    device_ip = serializers.CharField(source="device.ip", read_only=True)

    class Meta:
        model = MacAddress
        fields = [
            "id",
            "address",
            "vlan",
            "type",
            "device_id",
            "device_name",
            "device_ip",
            "port",
            "desc",
            "datetime",
        ]


class VlanPortSerializer(serializers.ModelSerializer):
    """Serialize one collected VLAN port row."""

    vlan = serializers.IntegerField(source="vlan.vlan", read_only=True)
    vlan_id = serializers.IntegerField(read_only=True)
    vlan_desc = serializers.CharField(source="vlan.desc", read_only=True)
    device_id = serializers.IntegerField(source="vlan.device_id", read_only=True)
    device_name = serializers.CharField(source="vlan.device.name", read_only=True)
    device_ip = serializers.CharField(source="vlan.device.ip", read_only=True)

    class Meta:
        model = VlanPort
        fields = [
            "id",
            "vlan_id",
            "vlan_desc",
            "vlan",
            "device_id",
            "device_name",
            "device_ip",
            "port",
            "desc",
        ]


class ShortVlanPortSerializer(serializers.ModelSerializer):
    """Serialize one collected VLAN port row."""

    class Meta:
        model = VlanPort
        fields = ["id", "port", "desc"]


class VlanSerializer(serializers.ModelSerializer):
    """Serialize collected VLAN data with ports."""

    device_id = serializers.IntegerField(source="device.id", read_only=True)
    device_name = serializers.CharField(source="device.name", read_only=True)
    device_ip = serializers.CharField(source="device.ip", read_only=True)
    ports = ShortVlanPortSerializer(many=True, read_only=True)

    class Meta:
        model = Vlan
        fields = [
            "id",
            "vlan",
            "desc",
            "device_id",
            "device_name",
            "device_ip",
            "datetime",
            "ports",
        ]


class MacGatherStatusSerializer(serializers.Serializer):
    status = serializers.CharField(allow_null=True, read_only=True)
    progress = serializers.FloatField(allow_null=True, read_only=True)


class MacGatherScanTaskSerializer(serializers.Serializer):
    task_id = serializers.UUIDField(allow_null=True, read_only=True)


class VlanGatherStatusSerializer(serializers.Serializer):
    status = serializers.CharField(allow_null=True, read_only=True)
    progress = serializers.FloatField(allow_null=True, read_only=True)


class VlanGatherScanTaskSerializer(serializers.Serializer):
    task_id = serializers.UUIDField(allow_null=True, read_only=True)
