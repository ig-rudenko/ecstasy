from rest_framework import serializers

from ..models import TransportRing


class TransportRingSerializer(serializers.ModelSerializer):
    vlans = serializers.ListSerializer(child=serializers.IntegerField())

    class Meta:
        model = TransportRing
        fields = ["name", "description", "vlans"]


class AccessRingSerializer(serializers.Serializer):
    head_name = serializers.CharField()
    ports = serializers.CharField()
    description = serializers.CharField()
    is_normal_rotate_status = serializers.BooleanField()


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
