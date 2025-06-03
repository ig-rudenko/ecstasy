from rest_framework import serializers


class ChangeDescriptionRequestSwaggerSerializer(serializers.Serializer):
    port = serializers.CharField()
    description = serializers.CharField()
