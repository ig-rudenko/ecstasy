from django_filters import rest_framework as rf_filters

from net_tools.models import DevicesInfo
from ..models import Devices


class DeviceFilter(rf_filters.FilterSet):
    group = rf_filters.CharFilter(field_name="group__name", lookup_expr="icontains")
    vendor = rf_filters.CharFilter(field_name="vendor", lookup_expr="icontains")
    model = rf_filters.CharFilter(field_name="model", lookup_expr="icontains")
    ip = rf_filters.CharFilter(field_name="ip", lookup_expr="icontains")

    class Meta:
        model = Devices
        fields = ["name"]


class DeviceInfoFilter(rf_filters.FilterSet):
    group = rf_filters.CharFilter(field_name="dev__group__name", lookup_expr="icontains")
    vendor = rf_filters.CharFilter(field_name="dev__vendor", lookup_expr="icontains")
    model = rf_filters.CharFilter(field_name="dev__model", lookup_expr="icontains")
    ip = rf_filters.CharFilter(field_name="dev__ip", lookup_expr="icontains")

    class Meta:
        model = DevicesInfo
        fields = ["dev"]
