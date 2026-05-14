from rest_framework import serializers

from ..serializers.view_tech_data import TechDataListSerializer


class SwaggerSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class StringListResponseSwaggerSerializer(SwaggerSerializer):
    results = serializers.ListField(child=serializers.CharField())


class DictListResponseSwaggerSerializer(SwaggerSerializer):
    results = serializers.ListField(child=serializers.DictField())


class PaginatedDictListResponseSwaggerSerializer(SwaggerSerializer):
    count = serializers.IntegerField(min_value=0)
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = serializers.ListField(child=serializers.DictField())


class PaginatedTechDataListResponseSwaggerSerializer(SwaggerSerializer):
    count = serializers.IntegerField(min_value=0)
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = TechDataListSerializer(many=True)


class ErrorDetailResponseSwaggerSerializer(SwaggerSerializer):
    detail = serializers.CharField()
