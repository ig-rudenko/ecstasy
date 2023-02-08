from rest_framework import serializers
from ..models import Devices, InterfacesComments


class DevicesSerializer(serializers.ModelSerializer):
    """
    ## Класс сериализатора модели Devices
    """

    group = serializers.CharField(source="group.name")

    class Meta:
        model = Devices
        fields = ["ip", "name", "vendor", "group", "model", "port_scan_protocol"]


class InterfacesCommentsSerializer(serializers.ModelSerializer):
    device = serializers.CharField(source="device.name", read_only=True)

    class Meta:
        model = InterfacesComments
        fields = ["id", "interface", "comment", "user", "device"]
        read_only_fields = ["id", "user", "device"]


class InterfaceSerializer(serializers.Serializer):
    name = serializers.CharField()
    status = serializers.CharField()
    desc = serializers.CharField()
