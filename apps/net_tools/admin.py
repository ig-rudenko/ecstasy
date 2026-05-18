import json

from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RangeDateTimeFilter, RelatedDropdownFilter
from unfold.contrib.import_export.forms import ImportForm, SelectableFieldsExportForm
from unfold.utils import prettify_json

from apps.net_tools.export_resources import DescNameFormatResource, VlanNameResource
from apps.net_tools.models import (
    DescNameFormat,
    DevicesForMacSearch,
    DevicesInfo,
    TracerouteNodeKind,
    TracerouteNodeStyleRule,
    VlanName,
)


class TracerouteNodeStyleRuleAdminForm(forms.ModelForm):
    class Meta:
        model = TracerouteNodeStyleRule
        fields = "__all__"
        widgets = {
            "color_background": forms.TextInput(attrs={"type": "color"}),
            "color_border": forms.TextInput(attrs={"type": "color"}),
            "color_font": forms.TextInput(attrs={"type": "color"}),
        }


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


@admin.register(TracerouteNodeKind)
class TracerouteNodeKindAdmin(ModelAdmin):
    compressed_fields = True
    warn_unsaved_form = True
    list_display = [
        "code",
        "name",
        "marker_prefix",
        "marker_suffix",
        "value_source",
        "hide_when_nodes_only",
    ]
    search_fields = ["code", "name", "marker_prefix", "marker_suffix", "description"]
    list_filter = ["value_source", "hide_when_nodes_only"]
    ordering = ["code"]
    fieldsets = (
        (
            "Основное",
            {"classes": ("tab",), "fields": ("code", "name", "description")},
        ),
        (
            "Маркер и label",
            {
                "classes": ("tab",),
                "fields": ("marker_prefix", "marker_suffix", "value_source", "hide_when_nodes_only"),
                "description": "Например, p:(...)/d:(...) или разделитель '-->' для значения после стрелки.",
            },
        ),
    )


@admin.register(TracerouteNodeStyleRule)
class TracerouteNodeStyleRuleAdmin(ModelAdmin):
    form = TracerouteNodeStyleRuleAdminForm
    compressed_fields = True
    warn_unsaved_form = True
    list_filter_submit = True
    list_display = [
        "name",
        "is_active",
        "priority",
        "node_kind",
        "match_type",
        "pattern",
        "group_id",
        "color_preview",
        "shape",
        "fixed_value",
        "stop_processing",
    ]
    list_editable = ["is_active", "priority", "group_id", "shape", "fixed_value", "stop_processing"]
    search_fields = ["name", "pattern", "description", "node_kind__code", "node_kind__name"]
    list_filter = ["is_active", "match_type", "shape", "stop_processing", ("node_kind", RelatedDropdownFilter)]
    autocomplete_fields = ["node_kind"]
    ordering = ["priority", "id"]
    fieldsets = (
        (
            "Основное",
            {"classes": ("tab",), "fields": ("name", "is_active", "priority", "description")},
        ),
        (
            "Условие срабатывания",
            {"classes": ("tab",), "fields": ("node_kind", "match_type", "pattern", "stop_processing")},
        ),
        (
            "Отображение",
            {
                "classes": ("tab",),
                "fields": ("group_id", "color_background", "color_border", "color_font", "shape", "fixed_value"),
                "description": "Поля можно оставлять пустыми, чтобы правило меняло только нужные параметры.",
            },
        ),
    )

    @admin.display(description="Colors")
    def color_preview(self, obj: TracerouteNodeStyleRule) -> str:
        background = obj.color_background or "#999999"
        border = obj.color_border or "#444444"
        font = obj.color_font or "#ffffff"
        return format_html(
            '<span style="display:inline-block;padding:2px 8px;border-radius:10px;'
            'background:{};border:1px solid {};color:{};">Aa</span>',
            background,
            border,
            font,
        )
