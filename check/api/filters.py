from django_filters import rest_framework as rf_filters

from net_tools.models import DevicesInfo
from ..models import Devices


class DeviceFilter(rf_filters.FilterSet):
    group = rf_filters.CharFilter(field_name="group__name", lookup_expr="icontains")
    vendor = rf_filters.CharFilter(field_name="vendor", lookup_expr="icontains")
    model = rf_filters.CharFilter(field_name="model", lookup_expr="icontains")
    ip = rf_filters.CharFilter(field_name="ip", lookup_expr="icontains")
    serial_number = rf_filters.CharFilter(field_name="serial_number", lookup_expr="icontains")
    port_scan_protocol = rf_filters.ChoiceFilter(field_name="port_scan_protocol", choices=Devices.PROTOCOLS)
    cmd_protocol = rf_filters.ChoiceFilter(field_name="cmd_protocol", choices=Devices.PROTOCOLS[1:])
    active = rf_filters.BooleanFilter(field_name="active")
    collect_interfaces = rf_filters.BooleanFilter(field_name="collect_interfaces", label="Collect interfaces")
    collect_mac_addresses = rf_filters.BooleanFilter(field_name="collect_mac_addresses")
    collect_vlan_info = rf_filters.BooleanFilter(field_name="collect_vlan_info")
    collect_configurations = rf_filters.BooleanFilter(field_name="collect_configurations")
    connection_pool_size = rf_filters.NumberFilter(field_name="connection_pool_size")

    return_fields = rf_filters.CharFilter(
        method="get_return_fields", label="Список полей для возврата, по умолчанию все", exclude=True
    )

    def get_return_fields(self, queryset, name, value):
        return queryset

    class Meta:
        model = Devices
        fields = [
            "group",
            "vendor",
            "model",
            "ip",
            "serial_number",
            "port_scan_protocol",
            "cmd_protocol",
            "active",
            "collect_interfaces",
            "collect_mac_addresses",
            "collect_vlan_info",
            "collect_configurations",
            "connection_pool_size",
        ]


class DeviceInfoFilter(rf_filters.FilterSet):
    group = rf_filters.CharFilter(field_name="dev__group__name", lookup_expr="icontains")
    vendor = rf_filters.CharFilter(field_name="dev__vendor", lookup_expr="icontains")
    model = rf_filters.CharFilter(field_name="dev__model", lookup_expr="icontains")
    ip = rf_filters.CharFilter(field_name="dev__ip", lookup_expr="icontains")

    class Meta:
        model = DevicesInfo
        fields = ["dev"]
