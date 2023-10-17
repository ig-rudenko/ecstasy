import re
from typing import List

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from gpon.models import Customer, SubscriberConnection, HouseOLTState, Service
from .address import AddressSerializer
from .common import CustomerSerializer


class SubscriberHouseOLTStateSerializer(serializers.ModelSerializer):
    houseAddress = AddressSerializer(source="house.address", read_only=True)
    deviceName = serializers.CharField(source="statement.device.name", read_only=True)
    devicePort = serializers.CharField(source="statement.olt_port", read_only=True)

    class Meta:
        model = HouseOLTState
        fields = ["id", "houseAddress", "deviceName", "devicePort"]


class SubscriberConnectionSerializer(serializers.ModelSerializer):
    houseOLTState = SubscriberHouseOLTStateSerializer(
        source="tech_capability.end3.house_olt_states.first",
        read_only=True,
    )
    address = AddressSerializer()
    services = serializers.ListSerializer(child=serializers.CharField())
    status = serializers.CharField(source="tech_capability.status")
    end3ID = serializers.IntegerField(source="tech_capability.end3.id")
    end3Type = serializers.CharField(source="tech_capability.end3.type")

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
            "connected_at",
            "services",
            "status",
            "houseOLTState",
            "end3ID",
            "end3Type",
        ]

    def validate_ont_mac(self, value: str) -> str:
        if not value:
            return value
        mac = re.findall("[a-f0-9]", value.lower())
        if len(mac) != 12:
            raise ValidationError("Неверный MAC адрес")
        return "".join(mac)

    def validate_services(self, values: List[str]) -> List[str]:
        if not values:
            return values
        if Service.objects.filter(name__in=values).count() != len(values):
            raise ValidationError("Некоторые сервисы не существуют")
        return values


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
