import re

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .address import AddressSerializer
from .types import ServicesType
from ...models import SubscriberConnection, Customer, Service, TechCapability


class CustomerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(allow_null=True)
    firstName = serializers.CharField(
        max_length=256,
        source="first_name",
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    lastName = serializers.CharField(
        max_length=256,
        source="last_name",
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    companyName = serializers.CharField(
        max_length=256,
        source="company_name",
        required=False,
        allow_blank=True,
        allow_null=True,
    )

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
        ref_name = "CreateCustomerSerializer"


class SubscriberDataSerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    customer = CustomerSerializer()
    services: ServicesType = serializers.ListSerializer(child=serializers.CharField())
    ip = serializers.IPAddressField(required=False, allow_null=True, allow_blank=True)
    ont_mac = serializers.CharField(max_length=20, allow_null=True, allow_blank=True, required=False)

    class Meta:
        model = SubscriberConnection
        fields = [
            "address",
            "tech_capability",
            "customer",
            "description",
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

        tech_capability: TechCapability = validated_data["tech_capability"]
        address = AddressSerializer.create(validated_data["address"])
        services = Service.objects.filter(name__in=validated_data["services"])
        connection: SubscriberConnection = SubscriberConnection.objects.create(
            address=address,
            customer=customer,
            tech_capability=tech_capability,
            description=validated_data.get("description", None),
            ont_id=validated_data.get("ont_id", None),
            ont_serial=validated_data.get("ont_serial", None),
            ont_mac=validated_data.get("ont_mac", None),
            order=validated_data.get("order", None),
            ip=validated_data.get("ip", None),
            transit=validated_data.get("transit", None),
            connected_at=validated_data.get("connected_at", None),
        )
        if tech_capability.status == TechCapability.Status.empty.value:
            tech_capability.status = TechCapability.Status.active.value
            tech_capability.save(update_fields=["status"])

        connection.services.add(*services)
        return connection


class UpdateSubscriberDataSerializer(SubscriberDataSerializer):
    tech_capability_id = serializers.PrimaryKeyRelatedField(
        source="tech_capability", queryset=TechCapability.objects, required=False
    )

    class Meta:
        model = SubscriberConnection
        fields = [
            "address",
            "ip",
            "tech_capability_id",
            "description",
            "ont_id",
            "ont_serial",
            "ont_mac",
            "order",
            "transit",
            "connected_at",
            "services",
        ]

    def update(self, instance: SubscriberConnection, validated_data):
        updated_fields = []
        for attr, value in validated_data.items():
            if attr == "address":
                address = AddressSerializer.create(validated_data.get("address"))
                instance.address = address
                updated_fields.append("address")
            elif attr == "services":
                services = Service.objects.filter(name__in=validated_data["services"])
                instance.services.clear()
                instance.services.add(*services)
            elif attr == "tech_capability":
                if instance.tech_capability is not None and instance.tech_capability.id != value.id:
                    instance.tech_capability.status = TechCapability.Status.empty.value
                    instance.tech_capability.save(update_fields=["status"])
                instance.tech_capability = value
                value.status = TechCapability.Status.active.value
                value.save()
                updated_fields.append(attr)
            else:
                setattr(instance, attr, value)
                updated_fields.append(attr)
        instance.save(update_fields=updated_fields)
        return instance
