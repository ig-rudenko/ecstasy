from rest_framework import serializers

from gpon.api.serializers.address import AddressSerializer
from gpon.models import End3, Customer


class End3Serializer(serializers.ModelSerializer):
    address = AddressSerializer()

    class Meta:
        model = End3
        fields = ["id", "address", "capacity", "location", "type"]


class CustomerSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source="first_name")
    lastName = serializers.CharField(source="last_name")
    companyName = serializers.CharField(source="company_name")

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
