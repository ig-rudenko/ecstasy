from django.contrib import admin
from net_tools.models import DescNameFormat, VlanName, DevicesForMacSearch


@admin.register(DescNameFormat)
class DescNameFormatAdmin(admin.ModelAdmin):
    list_display = search_fields = ["standard", "replacement"]


@admin.register(VlanName)
class VlanNameAdmin(admin.ModelAdmin):
    list_display = search_fields = ["vid", "name", "description"]


@admin.register(DevicesForMacSearch)
class DevicesForMacSearchAdmin(admin.ModelAdmin):
    list_display = search_fields = ["device", "description"]
    raw_id_fields = ["device"]
