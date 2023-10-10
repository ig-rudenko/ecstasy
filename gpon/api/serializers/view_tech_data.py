from rest_framework import serializers

from gpon.models import OLTState, HouseOLTState, TechCapability, SubscriberConnection, HouseB
from .address import BuildingAddressSerializer
from .common import End3Serializer
from .create_tech_data import OLTStateSerializer


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


class HouseOLTStateSerializer(serializers.ModelSerializer):
    statement = OLTStateSerializer()
    customerLines = End3Serializer(source="end3_set", many=True)

    class Meta:
        model = HouseOLTState
        fields = ["id", "entrances", "description", "customerLines", "statement"]


class ViewHouseBTechDataSerializer(BuildingAddressSerializer):
    oltStates = HouseOLTStateSerializer(source="house_olt_states", many=True)

    class Meta:
        model = HouseB
        fields = [
            "id",
            "region",
            "settlement",
            "planStructure",
            "street",
            "house",
            "block",
            "building_type",
            "floors",
            "total_entrances",
            "apartment_building",
            "floors",
            "total_entrances",
            "oltStates",
        ]


class SubscriberConnectionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="customer.full_name")

    class Meta:
        model = SubscriberConnection
        fields = ["id", "name", "transit"]


class TechCapabilitySerializer(serializers.ModelSerializer):
    subscribers = SubscriberConnectionSerializer(source="subscriber_connection", many=True, read_only=True)

    class Meta:
        model = TechCapability
        fields = ["id", "status", "number", "subscribers"]
        read_only_fields = ["id", "number", "subscribers"]

