from django_filters.rest_framework import CharFilter, FilterSet


class IdNameFilter(FilterSet):
    id = CharFilter(field_name="id", method="filter_id")
    name = CharFilter(field_name="name", lookup_expr="icontains")

    def filter_id(self, queryset, name, value):
        value_list = value.split(",")
        return queryset.filter(id__in=value_list)
