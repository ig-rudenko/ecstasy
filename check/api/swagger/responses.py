from drf_yasg import openapi
from rest_framework import serializers

from ...models import Devices, InterfacesComments


class SwaggerSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


device_unavailable = openapi.Response(
    description="Device unavailable",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={"detail": openapi.Schema(type=openapi.TYPE_STRING, example="Device unavailable")},
    ),
)


class ConfigFileSwaggerSerializer(SwaggerSerializer):
    name = serializers.CharField()
    size = serializers.IntegerField(min_value=0)
    modTime = serializers.DateTimeField(format="%H:%M %d.%m.%Y")


class DevicesConfigsSwaggerSerializer(SwaggerSerializer):
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


class DevicesConfigListSwaggerSerializer(SwaggerSerializer):
    count = serializers.IntegerField(min_value=0)
    devices = DevicesConfigsSwaggerSerializer(many=True)


class InterfaceWorkloadSwaggerSerializer(SwaggerSerializer):
    count = serializers.IntegerField()
    abons = serializers.IntegerField()
    abons_up = serializers.IntegerField()
    abons_up_with_desc = serializers.IntegerField()
    abons_up_no_desc = serializers.IntegerField()
    abons_down = serializers.IntegerField()
    abons_down_with_desc = serializers.IntegerField()
    abons_down_no_desc = serializers.IntegerField()


class DevicesInterfaceWorkloadSwaggerSerializer(SwaggerSerializer):
    interfaces_count = InterfaceWorkloadSwaggerSerializer(many=True)
    ip = serializers.IPAddressField()
    name = serializers.CharField()
    vendor = serializers.CharField(allow_null=True)
    group = serializers.CharField()
    model = serializers.CharField(allow_null=True)

    class Meta:
        fields = [
            "ip",
            "name",
            "vendor",
            "model",
            "group",
            "interfaces_count",
        ]


class DevicesInterfaceWorkloadResultSwaggerSerializer(SwaggerSerializer):
    devices_count = serializers.IntegerField()
    devices = DevicesInterfaceWorkloadSwaggerSerializer(many=True)

    class Meta:
        fields = ["devices_count", "devices"]


class LinkToAnotherDeviceSwaggerSerializer(SwaggerSerializer):
    """
    "Link": {
        "deviceName": "DEVICE-1",
        "url": "/device/DEVICE-1"
    },
    """

    deviceName = serializers.CharField()
    url = serializers.URLField()


class InterfaceCommentSerializer(serializers.ModelSerializer):
    """
    {
        "text": "Какой-то комментарий",
        "user": "irudenko",
        "id": 14
    }
    """

    text = serializers.CharField(source="comment")
    user = serializers.CharField(source="user.username")

    class Meta:
        model = InterfacesComments
        fields = ["id", "user", "text"]


class InterfaceInfoSwaggerSerializer(SwaggerSerializer):
    """
    ## Интерфейсы оборудования

    Пример:

        {
            "name": "gi1/0/1",
            "status": "up",
            "description": "To_DEVICE-1",
            "vlans": [12, 13],
            "link": {
                "deviceName": "DEVICE-1",
                "url": "/device/DEVICE-1"
            },
            "comments": [
                {
                    "text": "Какой-то комментарий",
                    "user": "irudenko",
                    "id": 14
                }
            ]
        }
    """

    name = serializers.CharField()
    status = serializers.CharField()
    description = serializers.CharField()
    vlans = serializers.ListField(child=serializers.IntegerField())
    link = LinkToAnotherDeviceSwaggerSerializer(allow_null=True, required=False)
    comments = InterfaceCommentSerializer(many=True, allow_null=True, required=False)


class InterfacesListSwaggerSerializer(SwaggerSerializer):
    interfaces = InterfaceInfoSwaggerSerializer(many=True)
    deviceAvailable = serializers.BooleanField()
    collected = serializers.DateTimeField()


class DeviceInfoSwaggerSerializer(SwaggerSerializer):
    deviceName = serializers.CharField()
    deviceIP = serializers.CharField()
    elasticStackLink = serializers.URLField()
    zabbixHostID = serializers.CharField()
    zabbixInfo = serializers.DictField()
    permission = serializers.IntegerField(min_value=0, max_value=4)
    coords = serializers.ListField(child=serializers.FloatField(), min_length=2, max_length=2)
    uptime = serializers.IntegerField(min_value=-1)
    consoleURL = serializers.CharField()


# MAC List


class MacListSwaggerSerializer(SwaggerSerializer):
    vlanID = serializers.IntegerField(min_value=1, max_value=4096)
    mac = serializers.CharField()
    vlanName = serializers.CharField()


class MacListResultSwaggerSerializer(SwaggerSerializer):
    result = serializers.ListSerializer(child=MacListSwaggerSerializer())  # type: ignore
    count = serializers.IntegerField(min_value=0)


class InterfaceDetailInfoSwaggerSerializer(SwaggerSerializer):
    class PortDetailInfo(serializers.Serializer):
        type = serializers.ChoiceField(
            choices=("text", "html", "error", "adsl", "gpon", "eltex-gpon", "mikrotik")
        )

        data = serializers.SerializerMethodField()  # type: ignore

    portDetailInfo = PortDetailInfo()
    portConfig = serializers.CharField()
    portType = serializers.CharField()
    portErrors = serializers.CharField()
    hasCableDiag = serializers.BooleanField()


class ChangeDescriptionSwaggerSerializer(SwaggerSerializer):
    description = serializers.CharField()
    port = serializers.CharField()
    saved = serializers.CharField()


class BrasSessionSwaggerSerializer(SwaggerSerializer):
    session = serializers.CharField(allow_null=True)
    errors = serializers.ListSerializer(child=serializers.CharField())  # type: ignore


class BrasPairSessionResultSwaggerSerializer(SwaggerSerializer):
    BRAS1 = BrasSessionSwaggerSerializer()
    BRAS2 = BrasSessionSwaggerSerializer()


class CutBrasSessionSwaggerSerializer(SwaggerSerializer):
    errors = serializers.ListSerializer(child=serializers.CharField())  # type: ignore
    portReloadStatus = serializers.CharField()
