import copy
from typing import Optional

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from check.models import Devices
from gpon.api.serializers.address import AddressSerializer
from gpon.api.serializers.create_tech_data import (
    OLTStateSerializer,
    WriteOnlyHouseBAddressSerializer,
)
from gpon.models import OLTState, HouseOLTState


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


class UpdateHouseOLTStateSerializer(serializers.ModelSerializer):
    address = WriteOnlyHouseBAddressSerializer(source="house.address")

    class Meta:
        model = HouseOLTState
        fields = ["entrances", "description", "address"]

    def update(self, instance: HouseOLTState, validated_data) -> HouseOLTState:
        data = copy.deepcopy(validated_data)
        building_type = data["house"]["address"].pop("building_type")
        floors = data["house"]["address"].pop("floors")
        total_entrances = data["house"]["address"].pop("total_entrances")

        address = AddressSerializer.create(data["house"]["address"])

        instance.house.address = address
        instance.house.apartment_building = building_type == "building"
        instance.house.total_entrances = total_entrances
        instance.house.floors = floors
        instance.house.save()

        instance.description = validated_data["description"]
        instance.entrances = validated_data["entrances"]
        instance.save()

        return instance
