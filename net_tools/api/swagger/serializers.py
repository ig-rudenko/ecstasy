from rest_framework import serializers


class GetVendorSerializer(serializers.Serializer):
    vendor = serializers.CharField()
    address = serializers.CharField()


class CommentSerializer(serializers.Serializer):
    createdTime = serializers.DateTimeField()
    user = serializers.CharField()
    text = serializers.CharField()


class FoundInterfaceSerializer(serializers.Serializer):
    Description = serializers.CharField()
    Device = serializers.CharField()
    Interface = serializers.CharField()
    SavedTime = serializers.DateTimeField(help_text='Формат: "31.01.2024 08:03:55"')
    Comment = CommentSerializer(many=True)


class FindByDescQuerySerializer(serializers.Serializer):
    pattern = serializers.CharField()


class GetVlanDescSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField()


# ================== VLAN TRACEROUTE ===================


class NodeFontSerializer(serializers.Serializer):
    color = serializers.CharField()


class TracerouteNodeSerializer(serializers.Serializer):
    title = serializers.CharField()
    group = serializers.IntegerField(min_value=0)
    hidden = serializers.BooleanField(required=False)
    id = serializers.IntegerField(min_value=0)
    label = serializers.CharField(label="Может быть и строкой и числом")  # type: ignore
    shape = serializers.CharField()
    value = serializers.IntegerField(min_value=1)
    font = NodeFontSerializer()


class TracerouteEdgeSerializer(serializers.Serializer):
    value = serializers.IntegerField()
    title = serializers.CharField()
    from_ = serializers.IntegerField(source="from", help_text="По факту вернется поле `from`")
    to = serializers.IntegerField()


class VlanTracerouteSerializer(serializers.Serializer):
    nodes = TracerouteNodeSerializer(many=True)
    edges = TracerouteEdgeSerializer(many=True)
    options = serializers.DictField(help_text="Параметры для отображения связей и физики")
