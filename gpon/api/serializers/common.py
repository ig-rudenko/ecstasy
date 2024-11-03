from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .address import AddressSerializer
from .types import ServicesType
from ...models import End3, Customer, SubscriberConnection


class End3Serializer(serializers.ModelSerializer):
    address = AddressSerializer()

    class Meta:
        model = End3
        fields = ["id", "address", "capacity", "location", "type"]


class CustomerSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source="first_name", allow_null=True, allow_blank=True)
    lastName = serializers.CharField(source="last_name", allow_null=True, allow_blank=True)
    companyName = serializers.CharField(source="company_name", allow_null=True, allow_blank=True)

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
        ref_name = "CommonCustomerSerializer"

    def validate(self, validated_data):
        if validated_data["type"] == Customer.Type.person.value:
            if not validated_data.get("first_name"):
                raise ValidationError("Вы должны указать имя для физ. лица")
            elif not validated_data.get("surname"):
                raise ValidationError("Вы должны указать фамилию для физ. лица")
            elif not validated_data.get("last_name"):
                raise ValidationError("Вы должны указать отчество для физ. лица")
        else:
            if not validated_data.get("company_name"):
                raise ValidationError("Вы должны указать название компании")

        return validated_data


class SubscriberConnectionSerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    services: ServicesType = serializers.ListSerializer(child=serializers.CharField())
    status = serializers.CharField(source="tech_capability.status")
    end3Port = serializers.IntegerField(source="tech_capability.number")
    customer = CustomerSerializer()

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
            "end3Port",
            "customer",
        ]
