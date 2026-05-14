from django.db.models import Q
from django_filters import rest_framework as rf_filters

from ..models import End3, HouseOLTState, SubscriberConnection, TechCapability


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
    planStructure = rf_filters.CharFilter(
        field_name="house__address__plan_structure", lookup_expr="icontains"
    )
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


class SubscriberConnectionFilter(rf_filters.FilterSet):
    general = rf_filters.CharFilter(method="filter_general")
    region = rf_filters.CharFilter(field_name="address__region", lookup_expr="icontains")
    settlement = rf_filters.CharFilter(field_name="address__settlement", lookup_expr="icontains")
    planStructure = rf_filters.CharFilter(field_name="address__plan_structure", lookup_expr="icontains")
    street = rf_filters.CharFilter(field_name="address__street", lookup_expr="icontains")
    house = rf_filters.CharFilter(field_name="address__house", lookup_expr="icontains")
    block = rf_filters.CharFilter(method="filter_block")
    customerName = rf_filters.CharFilter(method="filter_customer_name")
    contract = rf_filters.CharFilter(field_name="customer__contract", lookup_expr="icontains")

    class Meta:
        model = SubscriberConnection
        fields = [
            "general",
            "region",
            "settlement",
            "planStructure",
            "street",
            "house",
            "block",
            "customerName",
            "contract",
        ]

    @staticmethod
    def filter_block(queryset, name, value):
        if value is None:
            return queryset
        value = str(value or "").strip()
        if not value:
            return queryset
        if not value.isdigit():
            return queryset.none()
        return queryset.filter(address__block=int(value))

    @staticmethod
    def filter_customer_name(queryset, name, value):
        value = str(value or "").strip()
        if not value:
            return queryset
        return queryset.filter(
            Q(customer__first_name__icontains=value)
            | Q(customer__surname__icontains=value)
            | Q(customer__last_name__icontains=value)
            | Q(customer__company_name__icontains=value)
        )

    @staticmethod
    def filter_general(queryset, name, value):
        value = str(value or "").strip()
        if not value:
            return queryset
        base_q = (
            Q(customer__first_name__icontains=value)
            | Q(customer__surname__icontains=value)
            | Q(customer__last_name__icontains=value)
            | Q(customer__company_name__icontains=value)
            | Q(customer__phone__icontains=value)
            | Q(customer__contract__icontains=value)
        )
        if value.isdigit():
            base_q |= Q(transit=int(value))
        return queryset.filter(base_q)
