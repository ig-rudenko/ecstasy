from rest_framework import serializers

from ..models import TransportRing


class RingSerializer(serializers.ModelSerializer):
    vlans = serializers.ListSerializer(child=serializers.IntegerField())

    class Meta:
        model = TransportRing
        fields = ["name", "description", "vlans"]


class PointInterfacesSerializer(serializers.Serializer):
    name = serializers.CharField()
    status = serializers.CharField()
    description = serializers.CharField(source="desc")
    vlans = serializers.ListSerializer(source="vlan", child=serializers.IntegerField())

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class PointRingSerializer(serializers.Serializer):
    name = serializers.CharField(source="device.name")
    ip = serializers.CharField(source="device.ip")
    available = serializers.BooleanField(source="ping")
    port_to_prev_dev = PointInterfacesSerializer()
    port_to_next_dev = PointInterfacesSerializer()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
