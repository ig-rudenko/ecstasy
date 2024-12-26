from rest_framework import serializers

from ..models import Layers, Maps


class MapLayerField(serializers.CharField):
    def to_representation(self, value):
        if value.type == "zabbix":
            return value.zabbix_group_name
        elif value.type == "file":
            return value.name
        return "None"


class MapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maps
        fields = ["id", "name", "description", "interactive", "preview_image", "type"]


class MapDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maps
        fields = ["id", "name", "description", "interactive", "preview_image", "type", "from_file", "map_url"]


GroupsType = serializers.ListSerializer[MapLayerField]


class MapLayerSerializer(serializers.Serializer):
    groups: GroupsType = serializers.ListSerializer(child=MapLayerField(), source="layers")


class LayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Layers
        fields = [
            "id",
            "name",
            "description",
            "type",
            "from_file",
        ]
