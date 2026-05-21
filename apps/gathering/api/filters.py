from django.db.models import Q
from django_filters import rest_framework as rf_filters

from ..models import Vlan, VlanPort


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
