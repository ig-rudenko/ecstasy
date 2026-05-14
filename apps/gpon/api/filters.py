from django_filters import rest_framework as rf_filters

from ..models import End3, HouseOLTState, TechCapability


class End3Filer(rf_filters.FilterSet):
    street = rf_filters.CharFilter(method="street_filter", lookup_expr="icontains", label="Улица")
    house = rf_filters.CharFilter(method="house_filter", lookup_expr="exact", label="Дом")
    block = rf_filters.CharFilter(method="block_filter", lookup_expr="exact", label="Блок")
    tech_capability_status = rf_filters.ChoiceFilter(
        method="techcapability_status_filter",
        label="Статус тех. возможности",
        choices=TechCapability.Status.choices,
    )

    class Meta:
        model = End3
        fields = ["house", "block", "tech_capability_status"]

    def street_filter(self, queryset, name, value):
        return queryset.filter(address__street__icontains=str(value).upper())

    def house_filter(self, queryset, name, value):
        return queryset.filter(address__house__iexact=value)

    def block_filter(self, queryset, name, value):
        return queryset.filter(address__block__iexact=value)

    def techcapability_status_filter(self, queryset, name, value):
        return queryset.filter(techcapability__status__iexact=str(value).upper())


class TechDataFilter(rf_filters.FilterSet):
    region = rf_filters.CharFilter(field_name="house__address__region", lookup_expr="icontains")
    settlement = rf_filters.CharFilter(field_name="house__address__settlement", lookup_expr="icontains")
    planStructure = rf_filters.CharFilter(field_name="house__address__plan_structure", lookup_expr="icontains")
    street = rf_filters.CharFilter(field_name="house__address__street", lookup_expr="icontains")
    house = rf_filters.CharFilter(field_name="house__address__house", lookup_expr="icontains")
    block = rf_filters.CharFilter(method="filter_block")
    deviceName = rf_filters.CharFilter(field_name="statement__device__name", lookup_expr="icontains")
    devicePort = rf_filters.CharFilter(field_name="statement__olt_port", lookup_expr="icontains")

    class Meta:
        model = HouseOLTState
        fields = [
            "region",
            "settlement",
            "planStructure",
            "street",
            "house",
            "block",
            "deviceName",
            "devicePort",
        ]

    def filter_block(self, queryset, name, value):
        if value is None:
            return queryset
        value = str(value or "").strip()
        if not value:
            return queryset
        if not value.isdigit():
            return queryset.none()
        return queryset.filter(house__address__block=int(value))
