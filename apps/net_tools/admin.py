import json

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RangeDateTimeFilter, RelatedDropdownFilter
from unfold.contrib.import_export.forms import ImportForm, SelectableFieldsExportForm
from unfold.utils import prettify_json

from apps.net_tools.export_resources import DescNameFormatResource, VlanNameResource
from apps.net_tools.models import DescNameFormat, DevicesForMacSearch, DevicesInfo, VlanName


@admin.register(DevicesInfo)
class DevicesInfoAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = True
    list_display = ["dev", "interfaces_date", "vlans_date"]
    search_fields = ["dev__name", "dev__ip"]
    autocomplete_fields = ["dev"]
    readonly_fields = [
        "interfaces",
        "interfaces_date",
        "vlans",
        "vlans_date",
        "verbose_interfaces",
        "verbose_vlans",
    ]
    list_filter = (
        ("dev", RelatedDropdownFilter),
        ("interfaces_date", RangeDateTimeFilter),
        ("vlans_date", RangeDateTimeFilter),
    )
    fieldsets = (
        ("Устройство", {"classes": ("tab",), "fields": ("dev",)}),
        ("Интерфейсы", {"classes": ("tab",), "fields": ("interfaces_date", "verbose_interfaces")}),
        ("VLAN", {"classes": ("tab",), "fields": ("vlans_date", "verbose_vlans")}),
    )

    @staticmethod
    def _render_json(value: str | None):
        """Render JSON payload with the same syntax highlighting style as JSONField."""
        try:
            data = json.loads(value or "null")
        except (TypeError, ValueError):
            return format_html("<pre>{}</pre>", value or "")

        pretty = prettify_json(data, None)
        if pretty is not None:
            return pretty
        return format_html("<pre>{}</pre>", json.dumps(data, indent=4, ensure_ascii=False))

    @admin.display(description="interfaces")
    def verbose_interfaces(self, obj: DevicesInfo) -> str:
        return mark_safe(self._render_json(obj.interfaces))

    @admin.display(description="vlans")
    def verbose_vlans(self, obj: DevicesInfo) -> str:
        return mark_safe(self._render_json(obj.vlans))


@admin.register(DescNameFormat)
class DescNameFormatAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm
    resource_class = DescNameFormatResource
    compressed_fields = True
    warn_unsaved_form = True
    list_display = ["standard", "replacement"]
    search_fields = ["standard", "replacement"]


@admin.register(VlanName)
class VlanNameAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = SelectableFieldsExportForm
    resource_class = VlanNameResource
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
