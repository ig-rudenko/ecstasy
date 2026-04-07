import re

from django.contrib import admin
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.views.main import ChangeList
from django.core.paginator import InvalidPage
from django.db.models import Q
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RangeDateTimeFilter, RelatedDropdownFilter

from ecstasy_project.admin_filters import distinct_dropdown_filter

from .models import MacAddress, Vlan, VlanPort
from .paginator import CachedLargeTablePaginator, LargeTablePaginator

VlanDropdownFilter = distinct_dropdown_filter("vlan", "vlan")
TypeDropdownFilter = distinct_dropdown_filter("type", "type")
PortDropdownFilter = distinct_dropdown_filter("port", "port")


class CustomChangeList(ChangeList):
    """ChangeList with a cached paginator for large MAC tables."""

    def get_results(self, request):
        """Override result loading to use the custom paginator."""
        paginator = self.model_admin.get_paginator(request, self.queryset, self.list_per_page)
        result_count = paginator.count

        if self.model_admin.show_full_result_count:
            paginator = CachedLargeTablePaginator(self.root_queryset, per_page=25)
            full_result_count = paginator.count
        else:
            full_result_count = None

        can_show_all = result_count <= self.list_max_show_all
        multi_page = result_count > self.list_per_page

        if (self.show_all and can_show_all) or not multi_page:
            result_list = self.queryset._clone()
        else:
            try:
                result_list = paginator.page(self.page_num).object_list
            except InvalidPage as exc:
                raise IncorrectLookupParameters from exc

        self.result_count = result_count
        self.show_full_result_count = self.model_admin.show_full_result_count
        self.show_admin_actions = not self.show_full_result_count or bool(full_result_count)
        self.full_result_count = full_result_count
        self.result_list = result_list
        self.can_show_all = can_show_all
        self.multi_page = multi_page
        self.paginator = paginator


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

    @admin.display(description="MAC")
    def mac_address(self, obj: MacAddress):
        """Render the MAC address in a readable colon-separated format."""
        return "{}{}:{}{}:{}{}:{}{}:{}{}:{}{}".format(*list(obj.address))

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

        search_term = "".join(re.findall(r"[0-9a-fA-F]", search_term))
        q = Q()

        if 4 <= len(search_term) <= 10:
            q |= Q(address__icontains=search_term)
        else:
            return queryset.none(), False

        return queryset.filter(q), False

    def get_changelist(self, request, **kwargs):
        """Use the custom changelist implementation."""
        del kwargs
        return CustomChangeList


@admin.register(Vlan)
class VlansAdmin(ModelAdmin):
    compressed_fields = True
    list_display = ["vlan", "desc", "device__name", "datetime"]
    search_fields = ["vlan", "desc", "device__name"]
    list_select_related = ["device"]
    list_filter = (("device", RelatedDropdownFilter), ("datetime", RangeDateTimeFilter))
    list_filter_submit = True
    paginator = LargeTablePaginator


@admin.register(VlanPort)
class VlanPortsAdmin(ModelAdmin):
    compressed_fields = True
    list_display = ["vlan_verbose", "vlan__device", "port", "desc"]
    search_fields = ["vlan__vlan", "port", "vlan__device__name"]
    list_select_related = ["vlan", "vlan__device__name"]
    list_filter = (("vlan__device", RelatedDropdownFilter), ("vlan", RelatedDropdownFilter))
    list_filter_submit = True
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
