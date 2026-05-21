"""Shared admin filters for Unfold-based Django admin."""

from django.core.cache import cache
from django.core.exceptions import EmptyResultSet
from unfold.contrib.filters.admin import DropdownFilter


def distinct_dropdown_filter(field_name: str, title: str | None = None, use_cache: bool = False):
    """Create a dropdown filter class backed by distinct model field values."""

    resolved_title = title or field_name.replace("__", " ")

    class DistinctFieldDropdownFilter(DropdownFilter):
        """Dropdown filter for distinct values of a model field."""

        title = resolved_title
        parameter_name = field_name

        def lookups(self, request, model_admin):
            """Return distinct field values from the current model."""
            del request
            try:
                values = (
                    model_admin.model.objects.order_by(field_name)
                    .values_list(field_name, flat=True)
                    .distinct()
                )
            except EmptyResultSet:
                return []

            cache_key = f"DistinctFieldDropdownFilter:{model_admin.model._meta.app_label}.{model_admin.model.__name__}.{field_name}"

            if use_cache and (data := cache.get(cache_key)):
                return data

            data = [(value, str(value)) for value in values if value not in (None, "")]

            if use_cache:
                cache.set(cache_key, data, timeout=60)

            return data

        def queryset(self, request, queryset):
            """Apply exact filtering using the selected dropdown value."""
            del request
            if self.value() in (None, ""):
                return queryset
            return queryset.filter(**{field_name: self.value()})

    return DistinctFieldDropdownFilter
