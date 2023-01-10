from rest_framework import serializers
from ..models import Devices


class DevicesSerializer(serializers.ModelSerializer):
    """
    ## Класс сериализатора модели Devices
    """

    group = serializers.CharField(source="group.name")

    class Meta:
        model = Devices
        fields = ["ip", "name", "vendor", "group", "model", "port_scan_protocol"]
