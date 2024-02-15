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

from django.contrib import admin
from pyzabbix import ZabbixAPI, ZabbixAPIException
from requests import ConnectionError as ZabbixConnectionError, Session

from app_settings.models import (
    LogsElasticStackSettings,
    ZabbixConfig,
    VlanTracerouteConfig,
)


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

    @admin.display(description="Connectable", boolean=True)
    def connectable(self, obj: ZabbixConfig) -> bool:
        """
        Отображает, можно ли подключиться к Zabbix по указанным настройкам
        """

        session = Session()
        session.verify = False
        try:
            with ZabbixAPI(server=obj.url, session=session, timeout=2) as zabbix_api:
                zabbix_api.login(user=obj.login, password=obj.password)
                return zabbix_api.is_authenticated
        except (ZabbixAPIException, ZabbixConnectionError):
            return False
        # pylint: disable-next=broad-exception-caught
        except Exception as error:
            print(error)
            return False


@admin.register(VlanTracerouteConfig)
class VlanTracerouteConfigAdmin(admin.ModelAdmin):
    """
    ## Админка для настроек работы VLAN Traceroute
    """

    list_display = ["vlan_start", "find_device_pattern"]
