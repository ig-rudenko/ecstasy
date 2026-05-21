from rest_framework import serializers


class GetVendorSerializer(serializers.Serializer):
    vendor = serializers.CharField()
    address = serializers.CharField()


class CommentSerializer(serializers.Serializer):
    createdTime = serializers.DateTimeField()
    user = serializers.CharField()
    text = serializers.CharField()


class FoundInterfaceSerializer(serializers.Serializer):
    name = serializers.CharField()
    status = serializers.CharField()
    description = serializers.CharField()
    vlans = serializers.CharField()
    savedTime = serializers.DateTimeField(help_text='Формат: "2 года, 6 месяцев назад"')


class FoundDeviceInterfacesSerializer(serializers.Serializer):
    devices = serializers.CharField()
    comments = CommentSerializer(many=True)
    interfaces = FoundInterfaceSerializer()


class SearchInterfaceByDescResultSerializer(serializers.Serializer):
    interfaces = FoundDeviceInterfacesSerializer(many=True)


class FindByDescQuerySerializer(serializers.Serializer):
    is_regex = serializers.BooleanField(default=False)
    pattern = serializers.CharField()


class GetVlanDescSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField()


# ================== TRACEROUTE ===================


class NodeFontSerializer(serializers.Serializer):
    color = serializers.CharField()


class TracerouteNodeSerializer(serializers.Serializer):
    title = serializers.CharField(required=False)
    group = serializers.IntegerField(min_value=0, required=False)
    hidden = serializers.BooleanField(required=False)
    id = serializers.CharField(help_text="Node id (string or number serialized to string).")
    label = serializers.CharField(label="Может быть и строкой и числом")  # type: ignore
    shape = serializers.CharField()
    value = serializers.IntegerField(min_value=1)
    font = NodeFontSerializer(required=False)


class TracerouteEdgeSerializer(serializers.Serializer):
    value = serializers.IntegerField()
    title = serializers.DictField(help_text="Structured tooltip payload object.")
    from_ = serializers.CharField(source="from", help_text="По факту вернется поле `from`")  # type: ignore[assignment]
    to = serializers.CharField()


class TracerouteSerializer(serializers.Serializer):
    nodes = TracerouteNodeSerializer(many=True)
    edges = TracerouteEdgeSerializer(many=True)
    options = serializers.DictField(help_text="Параметры для отображения связей и физики")


class TracerouteMapNodeSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()  # type: ignore[assignment]
    lat = serializers.FloatField()
    lon = serializers.FloatField()
    title = serializers.CharField(required=False, allow_blank=True)
    device = serializers.DictField(required=False, allow_null=True)
    inherited_from = serializers.CharField(required=False)  # type: ignore[assignment]
    kind = serializers.CharField(required=False)


class TracerouteMapEdgeSerializer(serializers.Serializer):
    from_ = serializers.CharField(source="from", help_text="По факту вернется поле `from`")  # type: ignore[assignment]
    to = serializers.CharField()
    title = serializers.DictField(required=False)
    value = serializers.IntegerField(required=False)


class TracerouteMapSkippedNodeSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()  # type: ignore[assignment]
    reason = serializers.CharField()


class TracerouteMapSerializer(serializers.Serializer):
    nodes = TracerouteMapNodeSerializer(many=True)
    edges = TracerouteMapEdgeSerializer(many=True)
    skipped_nodes = TracerouteMapSkippedNodeSerializer(many=True)
    vlansInfo = serializers.ListField(child=serializers.DictField(), required=False)
