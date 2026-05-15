from rest_framework import serializers


class GeoJSONFeature(serializers.Serializer):
    type = serializers.CharField(label="Feature Type")
    id = serializers.CharField(label="Feature ID")
    geometry = serializers.DictField(label="Geometry")
    properties = serializers.DictField(label="Properties")


class GeoJSONFeatureCollection(serializers.Serializer):
    type = serializers.CharField(label="FeatureCollection", default="FeatureCollection")
    features = GeoJSONFeature(many=True, label="Features")


class MapLayerRenderSerializer(serializers.Serializer):
    name = serializers.CharField(label="Layer Name")
    type = serializers.ChoiceField(label="Layer Type", choices=["geojson", "zabbix"])
    properties = serializers.DictField(label="Layer Properties", required=False)
    features = GeoJSONFeatureCollection(label="GeoJSON")


class MapProblemSerializer(serializers.Serializer):
    id = serializers.CharField(label="Feature ID")
    acknowledges = serializers.ListSerializer(
        child=serializers.ListSerializer(child=serializers.CharField(), label="Текст и время")
    )


class MapUpdateLayersSerializer(serializers.Serializer):
    problems = MapProblemSerializer(many=True)
