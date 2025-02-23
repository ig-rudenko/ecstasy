from django.contrib import admin

from .models import MacAddress, Vlan, VlanPort
from .paginator import LargeTablePaginator


@admin.register(MacAddress)
class MacAddressesAdmin(admin.ModelAdmin):
    list_display = ["address", "vlan", "device", "port", "desc", "datetime"]
    search_fields = ["address", "vlan"]
    list_select_related = ["device"]
    paginator = LargeTablePaginator


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
