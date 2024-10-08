import re

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .address import AddressSerializer
from .common import CustomerSerializer, End3Serializer
from .types import ServicesType
from ...models import Customer, SubscriberConnection, HouseOLTState, Service, TechCapability


class SubscriberHouseOLTStateSerializer(serializers.ModelSerializer):
    houseAddress = AddressSerializer(source="house.address", read_only=True)
    deviceName = serializers.CharField(source="statement.device.name", read_only=True)
    devicePort = serializers.CharField(source="statement.olt_port", read_only=True)

    class Meta:
        model = HouseOLTState
        fields = ["id", "houseAddress", "deviceName", "devicePort"]


class SubscriberConnectionSerializer(serializers.ModelSerializer):
    houseOLTState = SubscriberHouseOLTStateSerializer(
        source="tech_capability.end3.house_olt_states", read_only=True, many=True
    )
    address = AddressSerializer()
    services: ServicesType = serializers.ListSerializer(child=serializers.CharField())
    status = serializers.CharField(source="tech_capability.status")
    tech_capability_id = serializers.PrimaryKeyRelatedField(
        source="tech_capability", queryset=TechCapability.objects.all()
    )
    end3Port = serializers.IntegerField(source="tech_capability.number")
    end3 = End3Serializer(source="tech_capability.end3")

    class Meta:
        model = SubscriberConnection
        fields = [
            "id",
            "address",
            "ip",
            "ont_id",
            "ont_serial",
            "ont_mac",
            "order",
            "transit",
            "description",
            "connected_at",
            "services",
            "status",
            "tech_capability_id",
            "houseOLTState",
            "end3",
            "end3Port",
        ]

    def validate_ont_mac(self, value: str) -> str:
        if not value:
            return value
        mac = re.findall("[a-f0-9]", value.lower())
        if len(mac) != 12:
            raise ValidationError("Неверный MAC адрес")
        return "".join(mac)

    def validate_services(self, values: list[str]) -> list[str]:
        if not values:
            return values
        if Service.objects.filter(name__in=values).count() != len(values):
            raise ValidationError("Некоторые сервисы не существуют")
        return values

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data["houseOLTState"]:
            data["houseOLTState"] = data["houseOLTState"][0]
        return data


class CustomerDetailSerializer(CustomerSerializer):
    connections = SubscriberConnectionSerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = [
            "id",
            "type",
            "firstName",
            "surname",
            "connections",
            "lastName",
            "companyName",
            "contract",
            "phone",
        ]
