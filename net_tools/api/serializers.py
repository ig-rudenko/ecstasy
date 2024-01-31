from rest_framework import serializers


class GetVlanDescQuerySerializer(serializers.Serializer):
    vlan = serializers.IntegerField(max_value=4096, min_value=1)


class VlanTracerouteQuerySerializer(serializers.Serializer):
    vlan = serializers.IntegerField(max_value=4096, min_value=1)
    ep = serializers.BooleanField(
        default=False,
        required=False,
        help_text="Показывать пустые порты",
    )
    ad = serializers.BooleanField(
        default=False,
        required=False,
        help_text="Указывать выключенные порты",
    )
    double_check = serializers.BooleanField(
        default=False, required=False,
        help_text="Двухстороннее соответствие VLAN на соседних портах"
    )
    graph_min_length = serializers.IntegerField(
        min_value=0,
        default=0,
        max_value=1024,
        required=False,
        help_text="Минимальное количество узлов в одном графе"
    )
