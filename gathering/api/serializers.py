from rest_framework import serializers


class MacGatherStatusSerializer(serializers.Serializer):
    status = serializers.CharField(allow_null=True, read_only=True)
    progress = serializers.CharField(allow_null=True, read_only=True)


class MacGatherScanTaskSerializer(serializers.Serializer):
    task_id = serializers.UUIDField(allow_null=True, read_only=True)
class VlanGatherStatusSerializer(serializers.Serializer):
    status = serializers.CharField(allow_null=True, read_only=True)
    progress = serializers.CharField(allow_null=True, read_only=True)


class VlanGatherScanTaskSerializer(serializers.Serializer):
    task_id = serializers.UUIDField(allow_null=True, read_only=True)