from rest_framework import serializers


class MapLayerField(serializers.CharField):
    def to_representation(self, value):
        if value.type == "zabbix":
            return value.zabbix_group_name
        elif value.type == "file":
            return value.name
        return "None"


class MapLayerSerializer(serializers.Serializer):
    groups = serializers.ListSerializer(child=MapLayerField(), source="layers")
