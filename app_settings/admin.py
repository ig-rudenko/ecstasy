from django.contrib import admin
from app_settings.models import LogsElasticStackSettings, ZabbixConfig, VlanTracerouteConfig
from pyzabbix import ZabbixAPI


@admin.register(LogsElasticStackSettings)
class LogsElasticStackSettingsAdmin(admin.ModelAdmin):
    list_display = ['kibana_url', 'time_range', 'query_str']


@admin.register(ZabbixConfig)
class ZabbixConfigAdmin(admin.ModelAdmin):
    list_display = ['url', 'login', 'connectable']

    @admin.display(description="Connectable")
    def connectable(self, obj: ZabbixConfig):
        try:
            zabbix_api = ZabbixAPI(server=obj.url)
            zabbix_api.login(user=obj.login, password=obj.password)
            return '✅' if zabbix_api.api_version() else '❌'
        except:
            return '❌'


@admin.register(VlanTracerouteConfig)
class VlanTracerouteConfigAdmin(admin.ModelAdmin):
    list_display = ['vlan_start', 'find_device_pattern']
