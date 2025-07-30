import re

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.core.cache import cache
from django.db.models import Q

from check.models import Devices
from .models import MacAddress, Vlan, VlanPort
from .paginator import LargeTablePaginator, CachedLargeTablePaginator

LIST_FILTER_CACHE_TIMEOUT = 60 * 10


class CachedDeviceFilter(SimpleListFilter):
    title = "device"
    parameter_name = "device"

    def lookups(self, request, model_admin):
        cache_key = "admin_device_filter_lookups"
        result = cache.get(cache_key)
        if not result:
            result = [(d.id, d.name) for d in Devices.objects.all()]
            cache.set(cache_key, result, LIST_FILTER_CACHE_TIMEOUT)  # кеш на 1 час
        return result

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(device__id=self.value())
        return queryset


class CachedVlanFilter(SimpleListFilter):
    title = "vlan"
    parameter_name = "vlan"

    def lookups(self, request, model_admin):
        cache_key = "admin_vlan_filter_lookups"
        result = cache.get(cache_key)
        if not result:
            result = sorted(set(model_admin.model.objects.values_list("vlan", flat=True).distinct()))
            result = [(v, str(v)) for v in result if v is not None]
            cache.set(cache_key, result, LIST_FILTER_CACHE_TIMEOUT)
        return result

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(vlan=self.value())
        return queryset


class CachedTypeFilter(SimpleListFilter):
    title = "type"
    parameter_name = "type"

    def lookups(self, request, model_admin):
        cache_key = "admin_type_filter_lookups"
        result = cache.get(cache_key)
        if not result:
            result = sorted(set(model_admin.model.objects.values_list("type", flat=True).distinct()))
            result = [(t, str(t)) for t in result if t is not None]
            cache.set(cache_key, result, LIST_FILTER_CACHE_TIMEOUT)
        return result

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(type=self.value())
        return queryset


class CachedPortFilter(SimpleListFilter):
    title = "port"
    parameter_name = "port"

    def lookups(self, request, model_admin):
        cache_key = "admin_port_filter_lookups"
        result = cache.get(cache_key)
        if not result:
            result = sorted(set(model_admin.model.objects.values_list("port", flat=True).distinct()))
            result = [(p, str(p)) for p in result if p is not None]
            cache.set(cache_key, result, LIST_FILTER_CACHE_TIMEOUT)
        return result

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(port=self.value())
        return queryset


@admin.register(MacAddress)
class MacAddressesAdmin(admin.ModelAdmin):
    list_display = ["mac_address", "vlan", "device", "port", "desc", "datetime", "type"]
    search_fields = ["address"]
    list_select_related = ["device"]
    list_filter = [CachedDeviceFilter, CachedVlanFilter, CachedTypeFilter, CachedPortFilter]
    paginator = CachedLargeTablePaginator

    @admin.display(description="MAC")
    def mac_address(self, obj: MacAddress):
        return "{}{}:{}{}:{}{}:{}{}:{}{}".format(*list(obj.address))

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("device")
            .only("address", "vlan", "device__name", "port", "desc", "datetime", "type", "device__ip")
        )

    def get_search_results(self, request, queryset, search_term):
        if not search_term:
            return queryset, False

        search_term = "".join(re.findall(r"[0-9a-fA-F]", search_term))
        q = Q()

        if 4 <= len(search_term) <= 10:
            # address — BinaryField or CharField with MAC-like values
            q |= Q(address__icontains=search_term)
        else:
            return queryset.none(), False

        return queryset.filter(q), False


@admin.register(Vlan)
class VlansAdmin(admin.ModelAdmin):
    list_display = ["vlan", "desc", "device__name", "datetime"]
    search_fields = ["vlan", "desc", "device__name"]
    list_select_related = ["device"]
    paginator = LargeTablePaginator


@admin.register(VlanPort)
class VlanPortsAdmin(admin.ModelAdmin):
    list_display = ["vlan_verbose", "vlan__device", "port", "desc"]
    search_fields = ["vlan__vlan", "port", "vlan__device__name"]
    list_select_related = ["vlan", "vlan__device__name"]
    list_filter = ["vlan__device", "vlan__vlan"]
    paginator = LargeTablePaginator

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("vlan", "vlan__device")
            .only("port", "desc", "vlan__vlan", "vlan__desc", "vlan__device__name", "vlan__device__ip")
        )

    @admin.display(description="VLAN")
    def vlan_verbose(self, obj: VlanPort):
        return f"{obj.vlan.vlan} - ({obj.vlan.desc})"
