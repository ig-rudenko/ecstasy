from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import SimpleTestCase, TestCase
from requests import RequestException

from apps.app_settings.models import ZabbixConfig
from apps.app_settings.zabbix_config_cache import (
    ZABBIX_CONFIG_MISSING_VERSION,
    ZABBIX_CONFIG_VERSION_CACHE_KEY,
    build_zabbix_config_version,
)
from devicemanager.device.zabbix_api import (
    ZabbixAPIConnector,
    ZabbixConnectionSettings,
)


class DictCache:
    """Минимальный cache backend для проверки версий настроек."""

    def __init__(self):
        self.data = {}

    def get(self, key, default=None):
        """Возвращает значение из памяти."""
        return self.data.get(key, default)

    def set(self, key, value, timeout=None):
        """Сохраняет значение в памяти."""
        self.data[key] = value


class ZabbixConnectionSettingsTestCase(SimpleTestCase):
    """Проверяет преобразование настроек Zabbix в явную структуру."""

    def test_from_config_maps_zabbix_model_fields(self):
        """Настройки берутся из полей модели ZabbixConfig."""
        config = SimpleNamespace(url="https://zabbix.example", login="admin", password="secret")

        settings = ZabbixConnectionSettings.from_config(config)

        self.assertEqual(settings.url, "https://zabbix.example")
        self.assertEqual(settings.login, "admin")
        self.assertEqual(settings.password, "secret")


class ZabbixAPIConnectorTestCase(SimpleTestCase):
    """Проверяет управление настройками и соединением Zabbix API."""

    def test_connect_uses_config_and_logs_in(self):
        """Подключение создается с текущими настройками и выполняет login."""
        connector = ZabbixAPIConnector(
            config=SimpleNamespace(url="https://zabbix.example", login="admin", password="secret")
        )

        with patch("devicemanager.device.zabbix_api.ZabbixAPI") as zabbix_api_class:
            connection = zabbix_api_class.return_value

            with connector.connect() as zabbix:
                self.assertIs(zabbix, connection)

        zabbix_api_class.assert_called_once()
        self.assertEqual(zabbix_api_class.call_args.kwargs["server"], "https://zabbix.example")
        connection.login.assert_called_once_with(user="admin", password="secret")

    def test_connect_reuses_connection_when_config_is_unchanged(self):
        """Если cache-версия не изменилась, настройки повторно не читаются из БД."""
        config = SimpleNamespace(url="https://zabbix.example", login="admin", password="secret")
        version = build_zabbix_config_version(config)
        version_cache = DictCache()
        connector = ZabbixAPIConnector(version_cache=version_cache)

        with (
            patch.object(
                connector,
                "_ZabbixAPIConnector__load_settings_from_db",
                return_value=(ZabbixConnectionSettings.from_config(config), version),
            ) as config_loader,
            patch("devicemanager.device.zabbix_api.ZabbixAPI") as zabbix_api_class,
        ):
            connector.connect()
            connector.connect()

        self.assertEqual(config_loader.call_count, 1)
        zabbix_api_class.assert_called_once()

    def test_connect_recreates_connection_when_config_changed(self):
        """Изменение настроек пересоздает соединение до следующего запроса в Zabbix."""
        configs = [
            SimpleNamespace(url="https://zabbix-1.example", login="admin", password="secret"),
            SimpleNamespace(url="https://zabbix-2.example", login="admin", password="secret"),
        ]
        versions = [build_zabbix_config_version(config) for config in configs]
        version_cache = DictCache()
        connector = ZabbixAPIConnector(version_cache=version_cache)

        with (
            patch.object(
                connector,
                "_ZabbixAPIConnector__load_settings_from_db",
                side_effect=[
                    (ZabbixConnectionSettings.from_config(configs[0]), versions[0]),
                    (ZabbixConnectionSettings.from_config(configs[1]), versions[1]),
                ],
            ),
            patch("devicemanager.device.zabbix_api.ZabbixAPI") as zabbix_api_class,
        ):
            first_connection = MagicMock()
            second_connection = MagicMock()
            zabbix_api_class.side_effect = [first_connection, second_connection]

            connector.connect()
            version_cache.set(ZABBIX_CONFIG_VERSION_CACHE_KEY, versions[1])
            connector.connect()

        self.assertEqual(zabbix_api_class.call_count, 2)
        first_connection.__exit__.assert_called_once_with(None, None, None)
        second_connection.login.assert_called_once_with(user="admin", password="secret")

    def test_connect_caches_missing_config_version(self):
        """Отсутствие настроек в БД фиксируется cache-версией и не перечитывается каждый раз."""
        version_cache = DictCache()
        connector = ZabbixAPIConnector(version_cache=version_cache)

        with (
            patch.object(
                connector,
                "_ZabbixAPIConnector__load_settings_from_db",
                return_value=(ZabbixConnectionSettings(), ZABBIX_CONFIG_MISSING_VERSION),
            ) as config_loader,
            patch("devicemanager.device.zabbix_api.ZabbixAPI") as zabbix_api_class,
        ):
            connector.connect()
            connector.connect()

        self.assertEqual(config_loader.call_count, 1)
        self.assertEqual(version_cache.get(ZABBIX_CONFIG_VERSION_CACHE_KEY), ZABBIX_CONFIG_MISSING_VERSION)
        zabbix_api_class.assert_called_once()

    def test_connect_closes_failed_connection(self):
        """Неуспешный login не оставляет неавторизованную сессию для повторного использования."""
        connector = ZabbixAPIConnector(
            config=SimpleNamespace(url="https://zabbix.example", login="admin", password="secret")
        )

        with patch("devicemanager.device.zabbix_api.ZabbixAPI") as zabbix_api_class:
            connection = MagicMock()
            connection.login.side_effect = ConnectionError
            zabbix_api_class.return_value = connection

            with self.assertRaises(RequestException):
                connector.connect()

        connection.__exit__.assert_called_once_with(None, None, None)


class ZabbixConfigCacheVersionTestCase(TestCase):
    """Проверяет обновление cache-версии при изменении модели ZabbixConfig."""

    def setUp(self):
        """Очищает cache перед каждым тестом."""
        cache.clear()

    def test_save_updates_zabbix_config_version_cache(self):
        """Сохранение ZabbixConfig обновляет версию настроек в cache."""
        config = ZabbixConfig.objects.create(
            url="https://zabbix.example",
            login="admin",
            password="secret",
        )

        self.assertEqual(cache.get(ZABBIX_CONFIG_VERSION_CACHE_KEY), build_zabbix_config_version(config))

    def test_delete_sets_missing_zabbix_config_version_cache(self):
        """Удаление последнего ZabbixConfig фиксирует в cache отсутствие настроек."""
        config = ZabbixConfig.objects.create(
            url="https://zabbix.example",
            login="admin",
            password="secret",
        )

        config.delete()

        self.assertEqual(cache.get(ZABBIX_CONFIG_VERSION_CACHE_KEY), ZABBIX_CONFIG_MISSING_VERSION)
