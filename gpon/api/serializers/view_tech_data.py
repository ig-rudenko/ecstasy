from rest_framework import serializers

from gpon.models import OLTState, HouseOLTState, TechCapability, SubscriberConnection
from .address import BuildingAddressSerializer
from .common import End3Serializer


class StructuresHouseOLTStateSerializer(serializers.ModelSerializer):
    address = BuildingAddressSerializer(source="house")
    customerLines = End3Serializer(source="end3_set", many=True)

    class Meta:
        model = HouseOLTState
        fields = ["id", "address", "entrances", "description", "customerLines"]


class ViewOLTStatesTechDataSerializer(serializers.ModelSerializer):
    deviceName = serializers.CharField(source="device.name")
    devicePort = serializers.CharField(source="olt_port")
    structures = StructuresHouseOLTStateSerializer(source="house_olt_states", many=True)

    class Meta:
        model = OLTState
        fields = ["id", "deviceName", "devicePort", "fiber", "description", "structures"]


class SubscriberConnectionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="customer.full_name")

    class Meta:
        model = SubscriberConnection
        fields = ["id", "name", "transit"]


class TechCapabilitySerializer(serializers.ModelSerializer):
    subscribers = SubscriberConnectionSerializer(source="subscriber_connection", many=True)

    class Meta:
        model = TechCapability
        fields = ["id", "status", "ending", "subscribers"]
