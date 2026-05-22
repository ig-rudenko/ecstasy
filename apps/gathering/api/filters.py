import re

from django.db.models import Q
from django_filters import rest_framework as rf_filters

from ..models import MacAddress, Vlan, VlanPort


class MacAddressFilter(rf_filters.FilterSet):
    device = rf_filters.CharFilter(method="search_by_device", label="Device by IP or name")
    address = rf_filters.CharFilter(method="search_by_address", label="MAC address")
    port = rf_filters.CharFilter(lookup_expr="icontains", label="Port")
    desc = rf_filters.CharFilter(lookup_expr="icontains", label="Description")

    class Meta:
        model = MacAddress
        fields = ["device_id", "device", "address", "vlan", "type", "port", "desc"]

    @staticmethod
    def search_by_device(queryset, name, value):
        """Filter MAC address rows by device name or IP address."""
        return queryset.filter(Q(device__name=value) | Q(device__ip=value))

    @staticmethod
    def search_by_address(queryset, name, search_term):
        """Filter MAC address rows by normalized MAC address value."""
        if re.match(r"^[0-9a-fA-F:-]+$", search_term):
            mac_search = "".join(re.findall(r"[0-9a-fA-F]", search_term))
            if len(mac_search) == 12:
                return queryset.filter(address__iexact=mac_search)
            if 6 <= len(mac_search) <= 12:
                return queryset.filter(address__icontains=mac_search)
        return queryset.none()


class VlanFilter(rf_filters.FilterSet):
    device = rf_filters.CharFilter(method="search_by_device", label="Device by IP or name")
    port = rf_filters.CharFilter(field_name="ports__port", lookup_expr="icontains", label="Port")

    class Meta:
        model = Vlan
        fields = ["device_id", "device", "vlan", "port"]

    @staticmethod
    def search_by_device(queryset, name, value):
        return queryset.filter(Q(device__name=value) | Q(device__ip=value))


class VlanPortFilter(rf_filters.FilterSet):
    device = rf_filters.CharFilter(method="search_by_device", label="Device by IP or name")
    device_id = rf_filters.NumberFilter(field_name="vlan__device__id", label="Device ID")
    vlan = rf_filters.NumberFilter(field_name="vlan__vlan", label="VLAN")
    port = rf_filters.CharFilter(lookup_expr="icontains", label="Port")

    class Meta:
        model = VlanPort
        fields = ["device_id", "device", "vlan", "port"]

    @staticmethod
    def search_by_device(queryset, name, value):
        return queryset.filter(Q(vlan__device__name=value) | Q(vlan__device__ip=value))
