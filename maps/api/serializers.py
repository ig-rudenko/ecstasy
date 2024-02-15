from rest_framework import serializers


class MapLayerField(serializers.CharField):
    def to_representation(self, value):
        if value.type == "zabbix":
            return value.zabbix_group_name
        elif value.type == "file":
            return value.name
        return "None"


GroupsType = serializers.ListSerializer[MapLayerField]


class MapLayerSerializer(serializers.Serializer):
    groups: GroupsType = serializers.ListSerializer(child=MapLayerField(), source="layers")
