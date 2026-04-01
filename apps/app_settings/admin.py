"""
Admin configuration for platform settings models.
"""

from django import forms
from django.contrib import admin
from requests import RequestException
from unfold.admin import ModelAdmin

from apps.app_settings.models import (
    AccessRingSettings,
    LogsElasticStackSettings,
    VlanTracerouteConfig,
    ZabbixConfig,
)
from devicemanager.device.zabbix_api import zabbix_api


@admin.register(LogsElasticStackSettings)
class LogsElasticStackSettingsAdmin(ModelAdmin):
    """Admin for Elastic Stack integration settings."""

    compressed_fields = True
    warn_unsaved_form = True
    list_display = ["kibana_url", "time_range", "query_str"]
    fieldsets = (
        ("Kibana", {"classes": ("tab",), "fields": ("kibana_url", "time_range", "time_field")}),
        ("Query", {"classes": ("tab",), "fields": ("query_lang", "query_str", "output_columns")}),
    )


@admin.register(ZabbixConfig)
class ZabbixConfigAdmin(ModelAdmin):
    """Admin for Zabbix API settings."""

    compressed_fields = True
    warn_unsaved_form = True
    list_display = ["url", "login", "connectable"]
    fieldsets = (
        ("Подключение", {"classes": ("tab",), "fields": ("url", "login", "password")}),
    )

    @admin.display(description="Connectable")
    def connectable(self, obj: ZabbixConfig) -> str:
        """Return the current connectivity status for Zabbix API."""
        zabbix_api.set_lazy_attributes(obj)
        try:
            with zabbix_api.connect() as conn:
                return "✅ Подключено" if conn.is_authenticated else "❌ Не подключено"
        except (Exception, RequestException) as exc:  # pylint: disable=broad-exception-caught
            return str(exc)


@admin.register(VlanTracerouteConfig)
class VlanTracerouteConfigAdmin(ModelAdmin):
    """Admin for VLAN traceroute settings."""

    compressed_fields = True
    warn_unsaved_form = True
    list_display = ["find_device_pattern", "vlan_start", "vlan_start_regex", "ip_pattern", "cache_timeout"]
    fieldsets = (
        ("Старт", {"classes": ("tab",), "fields": ("vlan_start", "vlan_start_regex")}),
        ("Поиск", {"classes": ("tab",), "fields": ("find_device_pattern", "ip_pattern")}),
        ("Кеш", {"classes": ("tab",), "fields": ("cache_timeout",)}),
    )


class AccessRingSettingsModelForm(forms.ModelForm):
    """Styled form for access ring regex settings."""

    class Meta:
        model = AccessRingSettings
        fields = "__all__"
        widgets = {
            "agg_dev_name_regexp": forms.Textarea(
                attrs={"style": "font-family: monospace; font-size: 1.3rem;"}
            ),
            "access_dev_name_regexp": forms.Textarea(
                attrs={"style": "font-family: monospace; font-size: 1.3rem;"}
            ),
        }


@admin.register(AccessRingSettings)
class AccessRingSettingsAdmin(ModelAdmin):
    """Admin for access ring matching rules."""

    form = AccessRingSettingsModelForm
    compressed_fields = True
    warn_unsaved_form = True
    list_display = ["id", "agg_dev_name_regexp", "access_dev_name_regexp"]
    fieldsets = (
        ("Агрегация", {"classes": ("tab",), "fields": ("agg_dev_name_regexp",)}),
        ("Доступ", {"classes": ("tab",), "fields": ("access_dev_name_regexp",)}),
    )
