from django.apps import AppConfig


class AppSettingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.app_settings"
    verbose_name = "App settings"

    def ready(self):
        from devicemanager.device import zabbix_api

        from .models import ZabbixConfig

        zabbix_api.set_init_load_function(ZabbixConfig.load)
