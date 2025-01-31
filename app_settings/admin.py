"""
## Админка для указания основных настроек для работы с Zabbix, Elastic, VLAN Traceroute

Настройка Zabbix позволяет Ecstasy подключаться через API и брать информацию оборудования

Для Elastic указываются:

    Kibana discover URL: http://kibana:5601/app/discover#/
    Глубина временного диапазона: Например: 1d, 24h или 30m
    Колонки: Поля через запятую, которые должны отображаться как колонки.
    Например: message,host.ip
    Язык запросов: KQL
    Строка для поиска: Необходимо указать, как будет произведен поиск логов для отдельного устройства.
    Timestamp поле: @timestamp

Для VLAN Traceroute:

    Имя оборудования для начала трассировки:
    Регулярное выражение. Оно используется для того,
    чтобы найти в описании порта имя другого оборудования и продолжить трассировку
"""

from django import forms
from django.contrib import admin
from requests import RequestException

from app_settings.models import (
    LogsElasticStackSettings,
    ZabbixConfig,
    VlanTracerouteConfig,
    AccessRingSettings,
)
from devicemanager.device.zabbix_api import zabbix_api


@admin.register(LogsElasticStackSettings)
class LogsElasticStackSettingsAdmin(admin.ModelAdmin):
    """
    ## Админка для настроек ElasticStack
    """

    list_display = ["kibana_url", "time_range", "query_str"]


@admin.register(ZabbixConfig)
class ZabbixConfigAdmin(admin.ModelAdmin):
    """
    ## Админка для настроек Zabbix API
    """

    list_display = ["url", "login", "connectable"]

    @admin.display(description="Connectable")
    def connectable(self, obj: ZabbixConfig) -> str:
        """
        Отображает, можно ли подключиться к Zabbix по указанным настройкам
        """
        zabbix_api.set(obj)
        try:
            with zabbix_api.connect() as conn:
                return "✅ Подключено" if conn.is_authenticated else "❌ Не подключено"
        # pylint: disable-next=broad-exception-caught
        except (Exception, RequestException) as exc:
            return str(exc)


@admin.register(VlanTracerouteConfig)
class VlanTracerouteConfigAdmin(admin.ModelAdmin):
    """
    ## Админка для настроек работы VLAN Traceroute
    """

    list_display = ["find_device_pattern", "vlan_start", "vlan_start_regex", "ip_pattern", "cache_timeout"]


class AccessRingSettingsModelForm(forms.ModelForm):
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
class AccessRingSettingsAdmin(admin.ModelAdmin):
    """
    ## Админка для настроек работы Access Ring
    """

    form = AccessRingSettingsModelForm
    list_display = ["id", "agg_dev_name_regexp", "access_dev_name_regexp"]
