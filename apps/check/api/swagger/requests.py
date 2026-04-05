from rest_framework import serializers


class ChangeDescriptionRequestSwaggerSerializer(serializers.Serializer):
    port = serializers.CharField()
    description = serializers.CharField(allow_blank=True)


class ExecuteBulkDeviceCommandRequestSwaggerSerializer(serializers.Serializer):
    device_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)
    port = serializers.DictField(child=serializers.CharField(), required=False)
    ip = serializers.DictField(child=serializers.CharField(), required=False)
    mac = serializers.DictField(child=serializers.CharField(), required=False)
    number = serializers.DictField(child=serializers.IntegerField(), required=False)
    word = serializers.DictField(child=serializers.CharField(), required=False)
