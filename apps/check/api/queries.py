from dataclasses import dataclass
from typing import Any

from rest_framework import serializers


@dataclass(kw_only=True, slots=True)
class DeviceInterfaceQuery:
    current_status: bool
    vlans: bool
    check_status: bool
    add_links: bool
    add_comments: bool
    add_zabbix_graph: bool


class DeviceInterfaceQuerySerializer(serializers.Serializer):
    current_status = serializers.BooleanField(default=False)
    vlans = serializers.BooleanField(default=False)
    check_status = serializers.BooleanField(default=True)
    add_links = serializers.BooleanField(default=True)
    add_comments = serializers.BooleanField(default=True)
    add_zabbix_graph = serializers.BooleanField(default=True)

    def create(self, validated_data: Any) -> DeviceInterfaceQuery:
        return DeviceInterfaceQuery(
            current_status=validated_data["current_status"],
            vlans=validated_data["vlans"],
            check_status=validated_data["check_status"],
            add_links=validated_data["add_links"],
            add_comments=validated_data["add_comments"],
            add_zabbix_graph=validated_data["add_zabbix_graph"],
        )
