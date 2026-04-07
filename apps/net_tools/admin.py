from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RangeDateTimeFilter, RelatedDropdownFilter

from apps.net_tools.models import DescNameFormat, DevicesForMacSearch, DevicesInfo, VlanName


@admin.register(DevicesInfo)
class DevicesInfoAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = True
    list_display = ["dev", "interfaces_date", "vlans_date"]
    search_fields = ["dev__name", "dev__ip"]
    autocomplete_fields = ["dev"]
    readonly_fields = ["interfaces", "interfaces_date", "vlans", "vlans_date"]
    list_filter = (
        ("dev", RelatedDropdownFilter),
        ("interfaces_date", RangeDateTimeFilter),
        ("vlans_date", RangeDateTimeFilter),
    )
    fieldsets = (
        ("Устройство", {"classes": ("tab",), "fields": ("dev",)}),
        ("Интерфейсы", {"classes": ("tab",), "fields": ("interfaces", "interfaces_date")}),
        ("VLAN", {"classes": ("tab",), "fields": ("vlans", "vlans_date")}),
    )


@admin.register(DescNameFormat)
class DescNameFormatAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_display = ["standard", "replacement"]
    search_fields = ["standard", "replacement"]


@admin.register(VlanName)
class VlanNameAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_display = ["vid", "name", "description"]
    search_fields = ["vid", "name", "description"]


@admin.register(DevicesForMacSearch)
class DevicesForMacSearchAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_display = ["device", "description"]
    search_fields = ["device__name", "device__ip", "description"]
    autocomplete_fields = ["device"]
