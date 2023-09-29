from typing import Optional

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from check.models import Devices
from gpon.api.serializers.create_tech_data import OLTStateSerializer
from gpon.models import OLTState


class UpdateRetrieveOLTStateSerializer(OLTStateSerializer):
    deviceName = serializers.CharField(source="device.name")
    devicePort = serializers.CharField(source="olt_port")

    class Meta:
        model = OLTState
        fields = ["deviceName", "devicePort", "fiber", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._device: Optional[Devices] = None

    def validate(self, attrs):
        """
        Функция проверяет занят ли уже определенный порт на устройстве.
        """
        attrs = super().validate(attrs)

        try:
            OLTState.objects.get(device__name=attrs["device"]["name"], olt_port=attrs["olt_port"])
        except OLTState.DoesNotExist:
            return attrs
        else:
            raise ValidationError(f"Данный порт на оборудовании уже занят")

    def update(self, instance: OLTState, validated_data) -> OLTState:
        instance.device_id = self._device.id
        instance.olt_port = validated_data["olt_port"]
        instance.fiber = validated_data.get("fiber")
        instance.description = validated_data.get("description")
        instance.save()
        return instance
