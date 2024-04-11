from django.apps import AppConfig


class AppSettingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_settings"
    verbose_name = "App settings"

    def ready(self):
        from app_settings.models import ZabbixConfig
        from devicemanager.device import zabbix_api

        zabbix_api.set_init_load_function(ZabbixConfig.load)
