from rest_framework import serializers

from ...models import Devices, InterfacesComments


class SwaggerSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class ConfigFileSwaggerSerializer(SwaggerSerializer):
    name = serializers.CharField()
    size = serializers.IntegerField(min_value=0)
    modTime = serializers.DateTimeField(format="%H:%M %d.%m.%Y")


class CollectConfigResponseSwaggerSerializer(SwaggerSerializer):
    status = serializers.CharField()


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
    interfaces_count = InterfaceWorkloadSwaggerSerializer()
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


class ZabbixMapSwaggerSerializer(SwaggerSerializer):
    sysmapid = serializers.IntegerField()
    name = serializers.CharField()


class DeviceZabbixInfoSwaggerSerializer(SwaggerSerializer):
    description = serializers.CharField()
    monitoringAvailable = serializers.BooleanField()
    inventory = serializers.DictField()
    maps = ZabbixMapSwaggerSerializer(many=True)


class DeviceInfoSwaggerSerializer(SwaggerSerializer):
    deviceName = serializers.CharField()
    deviceIP = serializers.CharField()
    vendor = serializers.CharField(allow_null=True)
    model = serializers.CharField(allow_null=True)
    serialNumber = serializers.CharField(allow_null=True)
    osVersion = serializers.CharField(allow_null=True)
    elasticStackLink = serializers.URLField()
    zabbixHostID = serializers.IntegerField()
    zabbixURL = serializers.URLField()
    zabbixInfo = DeviceZabbixInfoSwaggerSerializer()
    permission = serializers.IntegerField(min_value=0, max_value=4)
    coords = serializers.ListField(
        child=serializers.FloatField(), min_length=2, max_length=2, allow_null=True
    )
    uptime = serializers.IntegerField()
    consoleURL = serializers.URLField()


class DeviceStatsSwaggerSerializer(SwaggerSerializer):
    cpu = serializers.JSONField()
    ram = serializers.JSONField()
    flash = serializers.JSONField()
    temp = serializers.JSONField()


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


class CableDiagnosticPairSwaggerSerializer(SwaggerSerializer):
    status = serializers.CharField()
    len = serializers.CharField()


class CableDiagnosticResultSwaggerSerializer(SwaggerSerializer):
    len = serializers.CharField()
    status = serializers.CharField()
    pair1 = CableDiagnosticPairSwaggerSerializer(required=False)
    pair2 = CableDiagnosticPairSwaggerSerializer(required=False)
    pair3 = CableDiagnosticPairSwaggerSerializer(required=False)
    pair4 = CableDiagnosticPairSwaggerSerializer(required=False)
    sfp = serializers.DictField(required=False)


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


class DevicePoolStatusesSwaggerSerializer(SwaggerSerializer):
    connectionPoolSize = serializers.IntegerField(min_value=1)
    statuses = serializers.ListSerializer(child=serializers.BooleanField())  # type: ignore


class BulkCommandLaunchDeviceSwaggerSerializer(SwaggerSerializer):
    deviceId = serializers.IntegerField(min_value=1)
    deviceName = serializers.CharField()
    detail = serializers.CharField(required=False, allow_blank=True)


class BulkCommandLaunchResponseSwaggerSerializer(SwaggerSerializer):
    taskId = serializers.CharField()
    devices = BulkCommandLaunchDeviceSwaggerSerializer(many=True)
    skipped = BulkCommandLaunchDeviceSwaggerSerializer(many=True)


class BulkCommandTaskResultSwaggerSerializer(SwaggerSerializer):
    deviceId = serializers.IntegerField(min_value=1)
    deviceName = serializers.CharField()
    status = serializers.CharField()
    commandId = serializers.IntegerField(min_value=1)
    commandText = serializers.CharField()
    output = serializers.CharField(allow_blank=True)
    detail = serializers.CharField(allow_blank=True)
    error = serializers.CharField(allow_blank=True)
    duration = serializers.FloatField(min_value=0)


class BulkCommandTaskStatusSwaggerSerializer(SwaggerSerializer):
    taskId = serializers.CharField()
    status = serializers.CharField()
    progress = serializers.IntegerField(min_value=0, max_value=100, required=False)
    processed = serializers.IntegerField(min_value=0, required=False)
    total = serializers.IntegerField(min_value=0, required=False)
    resultsCount = serializers.IntegerField(min_value=0)
    resultDeviceIds = serializers.ListField(child=serializers.IntegerField(min_value=1))
    results = BulkCommandTaskResultSwaggerSerializer(many=True)


class GetDeviceByZabbixSerializer(SwaggerSerializer):
    device = serializers.CharField()
