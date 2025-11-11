from django_filters import rest_framework as rf_filters

from ..models import End3, TechCapability


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
