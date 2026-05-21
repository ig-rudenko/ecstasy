from rest_framework import serializers

from apps.gathering.models import Vlan, VlanPort


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
