from rest_framework import serializers


class DeviceQueryParamsSerializer(serializers.Serializer):
    current_status = serializers.BooleanField(default=False)
    vlans = serializers.BooleanField(default=False)
    add_links = serializers.BooleanField(default=True)
    add_comments = serializers.BooleanField(default=True)
    add_zabbix_graph = serializers.BooleanField(default=True)
