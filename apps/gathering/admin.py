import re

from django.contrib import admin
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.views.main import ChangeList
from django.core.paginator import InvalidPage
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RangeDateTimeFilter, RelatedDropdownFilter

from ecstasy_project.admin_filters import distinct_dropdown_filter

from .models import MacAddress, Vlan, VlanPort
from .paginator import CachedLargeTablePaginator, LargeTablePaginator

VlanDropdownFilter = distinct_dropdown_filter("vlan", "vlan", use_cache=True)
TypeDropdownFilter = distinct_dropdown_filter("type", "type", use_cache=True)
PortDropdownFilter = distinct_dropdown_filter("port", "port", use_cache=True)


@admin.register(MacAddress)
class MacAddressesAdmin(ModelAdmin):
    compressed_fields = True
    list_display = ["mac_address", "vlan", "device", "port", "desc", "datetime", "type"]
    search_fields = ["address"]
    list_select_related = ["device"]
    list_filter = [
        ("device", RelatedDropdownFilter),
        VlanDropdownFilter,
        TypeDropdownFilter,
        PortDropdownFilter,
        ("datetime", RangeDateTimeFilter),
    ]
    list_filter_submit = True
    paginator = CachedLargeTablePaginator
    list_per_page = 25
    autocomplete_fields = ["device"]

    @admin.display(description="MAC")
    def mac_address(self, obj: MacAddress):
        """Render the MAC address in a readable colon-separated format."""
        return mark_safe(
            "<span style='font-family: monospace;'>{}{}:{}{}:{}{}:{}{}:{}{}:{}{}</span>".format(
                *list(obj.address.upper())
            )
        )

    def get_queryset(self, request):
        """Optimize related loading for changelist rendering."""
        return (
            super()
            .get_queryset(request)
            .select_related("device")
            .only("address", "vlan", "device__name", "port", "desc", "datetime", "type", "device__ip")
        )

    def get_search_results(self, request, queryset, search_term):
        """Support MAC search in compact and separated forms."""
        if not search_term:
            return queryset, False

        if search_term.isdigit() and 1 <= int(search_term) <= 4096:
            return queryset.filter(vlan=int(search_term)), False

        if re.match(r"^[0-9a-fA-F:-]+$", search_term):
            mac_search = "".join(re.findall(r"[0-9a-fA-F]", search_term))
            if len(mac_search) == 12:
                return queryset.filter(address__iexact=mac_search), False
            if 6 <= len(mac_search) <= 12:
                return queryset.filter(address__icontains=mac_search), False

        return queryset.filter(device__name__icontains=search_term), False


@admin.register(Vlan)
class VlansAdmin(ModelAdmin):
    compressed_fields = True
    list_display = ["vlan", "desc", "device__name", "datetime"]
    search_fields = ["vlan", "desc", "device__name"]
    list_select_related = ["device"]
    list_filter = (("device", RelatedDropdownFilter), ("datetime", RangeDateTimeFilter))
    list_filter_submit = True
    list_per_page = 25
    autocomplete_fields = ["device"]
    paginator = LargeTablePaginator


class VlanDeviceDropdownFilter(RelatedDropdownFilter):
    """Filter by related VLAN with optimized label loading."""

    def field_choices(self, field, request: HttpRequest, model_admin: ModelAdmin):
        """Return VLAN choices with preloaded device to avoid N+1 in `Vlan.__str__`."""
        del field
        vlan_ids = model_admin.get_queryset(request).order_by().values_list("vlan_id", flat=True).distinct()
        vlans = (
            Vlan.objects.filter(pk__in=vlan_ids)
            .select_related("device")
            .only("id", "vlan", "desc", "device__name")
            .order_by("device__name", "vlan")
        )
        return [(vlan.pk, str(vlan)) for vlan in vlans]

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet | None:
        """Apply selected filter value to the changelist queryset."""
        qs = super().queryset(request, queryset)
        if qs is not None:
            return qs.select_related("vlan__device")
        return qs


@admin.register(VlanPort)
class VlanPortsAdmin(ModelAdmin):
    compressed_fields = True
    list_display = ["vlan_verbose", "vlan__device", "port", "desc"]
    search_fields = ["vlan__vlan", "port", "vlan__device__name"]
    list_filter = (("vlan__device", RelatedDropdownFilter),)
    list_per_page = 25
    list_filter_submit = True
    autocomplete_fields = ("vlan",)
    paginator = LargeTablePaginator

    def get_queryset(self, request):
        """Optimize related loading for changelist rendering."""
        return (
            super()
            .get_queryset(request)
            .select_related("vlan", "vlan__device")
            .only("port", "desc", "vlan__vlan", "vlan__desc", "vlan__device__name", "vlan__device__ip")
        )

    @admin.display(description="VLAN")
    def vlan_verbose(self, obj: VlanPort):
        """Render VLAN number and description in one column."""
        return f"{obj.vlan.vlan} - ({obj.vlan.desc})"
