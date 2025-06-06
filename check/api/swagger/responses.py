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
            "interfaces_count",
        ]


class LinkToAnotherDeviceSwaggerSerializer(SwaggerSerializer):
    """
    "Link": {
        "device_name": "DEVICE-1",
        "url": "/device/DEVICE-1"
    },
    """

    device_name = serializers.CharField()
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
            "Interface": "gi1/0/1",
            "Status": "up",
            "Description": "To_DEVICE-1",
            "Link": {
                "device_name": "DEVICE-1",
                "url": "/device/DEVICE-1"
            },
            "Comments": [
                {
                    "text": "Какой-то комментарий",
                    "user": "irudenko",
                    "id": 14
                }
            ]
        }
    """

    Interface = serializers.CharField()
    Status = serializers.CharField()
    Description = serializers.CharField()
    VLANS = serializers.ListField(allow_null=True, required=False)
    Link = LinkToAnotherDeviceSwaggerSerializer(allow_null=True, required=False)
    Comments = InterfaceCommentSerializer(many=True, allow_null=True, required=False)

    def __init__(self, **kwargs):
        """
        Меняем поле `VLANS` на `VLAN's`
        """
        super().__init__(**kwargs)
        if self._declared_fields.get("VLANS"):
            self._declared_fields["VLAN's"] = self._declared_fields["VLANS"]
            del self._declared_fields["VLANS"]


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
    result = serializers.ListSerializer(child=MacListSwaggerSerializer())
    count = serializers.IntegerField(min_value=0)


class InterfaceDetailInfoSwaggerSerializer(SwaggerSerializer):
    class PortDetailInfo(serializers.Serializer):
        type = serializers.ChoiceField(
            choices=("text", "html", "error", "adsl", "gpon", "eltex-gpon", "mikrotik")
        )

        data = serializers.SerializerMethodField()

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
    errors = serializers.ListSerializer(child=serializers.CharField())


class BrasPairSessionResultSwaggerSerializer(SwaggerSerializer):
    BRAS1 = BrasSessionSwaggerSerializer()
    BRAS2 = BrasSessionSwaggerSerializer()


class CutBrasSessionSwaggerSerializer(SwaggerSerializer):
    errors = serializers.ListSerializer(child=serializers.CharField())
    portReloadStatus = serializers.CharField()
