import re
from typing import List

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from gpon.api.serializers.address import AddressSerializer
from gpon.models import SubscriberConnection, Customer, Service


class CustomerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(allow_null=True)
    firstName = serializers.CharField(source="first_name", required=False, allow_blank=True)
    lastName = serializers.CharField(source="last_name", required=False, allow_blank=True)
    companyName = serializers.CharField(source="company_name", required=False, allow_blank=True)

    class Meta:
        model = Customer
        fields = [
            "id",
            "type",
            "firstName",
            "surname",
            "lastName",
            "companyName",
            "contract",
            "phone",
        ]


class CreateSubscriberDataSerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    customer = CustomerSerializer()
    services = serializers.ListSerializer(child=serializers.CharField())
    ont_mac = serializers.CharField(max_length=20)

    class Meta:
        model = SubscriberConnection
        fields = [
            "address",
            "tech_capability",
            "customer",
            "ip",
            "ont_id",
            "ont_serial",
            "ont_mac",
            "order",
            "transit",
            "connected_at",
            "services",
        ]

    def validate_ont_mac(self, value: str) -> str:
        mac = re.findall("[a-f0-9]", value.lower())
        if len(mac) != 12:
            raise ValidationError("Неверный MAC адрес")
        return "".join(mac)

    def validate_services(self, values: List[str]) -> List[str]:
        if Service.objects.filter(name__in=values).count() != len(values):
            raise ValidationError("Некоторые сервисы не существуют")
        return values

    def create(self, validated_data) -> SubscriberConnection:
        try:
            customer = Customer.objects.get(id=validated_data["customer"].get("id", 0))
        except Customer.DoesNotExist:
            customer = Customer.objects.create(
                type=validated_data["customer"]["type"],
                first_name=validated_data["customer"].get("first_name"),
                surname=validated_data["customer"].get("surname"),
                last_name=validated_data["customer"].get("last_name"),
                company_name=validated_data["customer"].get("company_name"),
                contract=validated_data["customer"]["contract"],
                phone=validated_data["customer"].get("phone"),
            )

        address = AddressSerializer.create(validated_data["address"])
        services = Service.objects.filter(name__in=validated_data["services"])
        connection: SubscriberConnection = SubscriberConnection.objects.create(
            address=address,
            customer=customer,
            tech_capability=validated_data["tech_capability"],
            ont_id=validated_data.get("ont_id", None),
            ont_serial=validated_data.get("ont_serial", None),
            ont_mac=validated_data.get("ont_mac", None),
            order=validated_data.get("order", None),
            transit=validated_data.get("transit", None),
            connected_at=validated_data.get("connected_at", None),
        )
        connection.services.add(*services)
        return connection
