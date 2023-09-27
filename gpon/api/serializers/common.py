from rest_framework import serializers

from gpon.api.serializers.address import AddressSerializer
from gpon.models import End3


class End3Serializer(serializers.ModelSerializer):
    address = AddressSerializer()

    class Meta:
        model = End3
        fields = ["id", "address", "capacity", "location", "type"]
