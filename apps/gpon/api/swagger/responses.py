from rest_framework import serializers

from ..serializers.common import SubscriberConnectionSerializer
from ..serializers.view_tech_data import TechDataListSerializer


class SwaggerSerializer(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class StringListResponseSwaggerSerializer(SwaggerSerializer):
    results = serializers.ListField(child=serializers.CharField())


class PaginatedTechDataListResponseSwaggerSerializer(SwaggerSerializer):
    count = serializers.IntegerField(min_value=0)
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = TechDataListSerializer(many=True)


class PaginatedSubscriberConnectionListResponseSwaggerSerializer(SwaggerSerializer):
    count = serializers.IntegerField(min_value=0)
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = SubscriberConnectionSerializer(many=True)
