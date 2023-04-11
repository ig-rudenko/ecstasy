from rest_framework import serializers
from ...models import Devices


class ConfigFileSwaggerSerializer(serializers.Serializer):
    name = serializers.CharField()
    size = serializers.IntegerField(min_value=0)
    modTime = serializers.DateTimeField(
        format="%H:%M %d.%m.%Y", default="%H:%M %d.%m.%Y"
    )
    isDir = serializers.BooleanField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class DevicesConfigsSwaggerSerializer(serializers.ModelSerializer):
    files = ConfigFileSwaggerSerializer(many=True)
    group = serializers.CharField(source="group.name")

    class Meta:
        model = Devices
        fields = [
            "ip",
            "name",
            "vendor",
            "group",
            "model",
            "port_scan_protocol",
            "files",
        ]


class DevicesConfigListSwaggerSerializer(serializers.Serializer):
    count = serializers.IntegerField(min_value=0)
    devices = DevicesConfigsSwaggerSerializer(many=True)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
