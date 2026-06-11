from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from django.conf import settings
from django.core.cache import BaseCache, cache
from pyzabbix import ZabbixAPI, ZabbixAPIException
from requests import RequestException, Session

from apps.app_settings.zabbix_config_cache import (
    ZABBIX_CONFIG_MISSING_VERSION,
    ZABBIX_CONFIG_VERSION_CACHE_KEY,
    build_zabbix_config_version,
)


@dataclass(frozen=True)
class ZabbixConnectionSettings:
    """Параметры подключения к Zabbix API."""

    url: str = ""
    login: str = ""
    password: str = ""

    @classmethod
    def from_config(cls, config: Any) -> "ZabbixConnectionSettings":
        """Создает настройки подключения из объекта ZabbixConfig."""
        if not config:
            return cls()
        return cls(
            url=str(getattr(config, "url", "") or ""),
            login=str(getattr(config, "login", "") or ""),
            password=str(getattr(config, "password", "") or ""),
        )


class ZabbixAPIConnector:
    """Управляет настройками и сессией подключения к Zabbix API."""

    def __init__(
        self,
        timeout: int = 2,
        config: Any = None,
        session_exists_timeout: int = 60,
        version_cache: BaseCache = cache,
    ):
        self.timeout = timeout
        self.__session_exists_timeout = session_exists_timeout
        self.__session_created: datetime | None = None
        self.__use_db_settings = config is None
        self.__settings_loaded = config is not None
        self.__settings_version = build_zabbix_config_version(config) if config is not None else None
        self.__version_cache = version_cache
        self.__settings = ZabbixConnectionSettings.from_config(config)
        self._zabbix_connection: ZabbixAPI | None = None

    @property
    def zabbix_url(self) -> str:
        """Возвращает URL текущего Zabbix."""
        return self._get_settings().url

    @property
    def zabbix_user(self) -> str:
        """Возвращает пользователя текущего Zabbix."""
        return self._get_settings().login

    @property
    def zabbix_password(self) -> str:
        """Возвращает пароль текущего Zabbix."""
        return self._get_settings().password

    @staticmethod
    def get_session() -> Session:
        """Создает requests-сессию для Zabbix API."""
        session = Session()
        if not settings.VERIFY_ZABBIX_CONNECTION:
            session.verify = False
        return session

    def connect(self):
        """Возвращает контекстный менеджер с подключением к Zabbix API."""
        current_settings = self._get_settings()
        if self.__connection_expired():
            self.close()

        if self._zabbix_connection is None:
            self._zabbix_connection = ZabbixAPI(
                server=current_settings.url,
                timeout=self.timeout,
                session=self.get_session(),
            )
            self.__session_created = datetime.now()

            try:
                self._zabbix_connection.login(user=current_settings.login, password=current_settings.password)
            except (ConnectionError, ZabbixAPIException) as exc:
                self.close()
                raise RequestException("Не удалось подключиться к Zabbix") from exc

        return self

    def close(self, exc_type=None, exc_val=None, exc_tb=None):
        """Закрывает текущее подключение к Zabbix API."""
        if self._zabbix_connection is not None:
            exit_method = getattr(self._zabbix_connection, "__exit__", None)
            if exit_method:
                exit_method(exc_type, exc_val, exc_tb)
        self._zabbix_connection = None
        self.__session_created = None

    def __enter__(self) -> ZabbixAPI:
        if self._zabbix_connection is None:
            self.connect()
        if self._zabbix_connection is None:
            raise RequestException("Не удалось подключиться к Zabbix")
        return self._zabbix_connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.__connection_expired():
            self.close(exc_type, exc_val, exc_tb)

    def _get_settings(self) -> ZabbixConnectionSettings:
        """Возвращает текущие настройки, при необходимости загружая их из источника."""
        if not self.__use_db_settings:
            return self.__settings

        cached_version = self.__version_cache.get(ZABBIX_CONFIG_VERSION_CACHE_KEY)
        if (
            self.__settings_loaded
            and cached_version is not None
            and cached_version == self.__settings_version
        ):
            return self.__settings

        _settings, version = self.__load_settings_from_db()
        self.__version_cache.set(ZABBIX_CONFIG_VERSION_CACHE_KEY, version, timeout=None)
        self.__set_settings(_settings, version)
        return self.__settings

    def __load_settings_from_db(self) -> tuple[ZabbixConnectionSettings, str]:
        """Загружает настройки из БД и возвращает их вместе с версией."""
        # pylint: disable-next=import-outside-toplevel
        from apps.app_settings.models import ZabbixConfig

        try:
            config = ZabbixConfig.objects.get()
        except ZabbixConfig.DoesNotExist:
            return ZabbixConnectionSettings(), ZABBIX_CONFIG_MISSING_VERSION

        return ZabbixConnectionSettings.from_config(config), build_zabbix_config_version(config)

    def __set_settings(self, new_settings: ZabbixConnectionSettings, new_version: str):
        """Сохраняет настройки и сбрасывает соединение, если они изменились."""
        if new_settings != self.__settings or new_version != self.__settings_version:
            self.close()
        self.__settings = new_settings
        self.__settings_version = new_version
        self.__settings_loaded = True

    def __connection_expired(self) -> bool:
        """Проверяет, истекло ли время жизни текущего подключения."""
        if self.__session_created is None:
            return False
        return self.__session_created < datetime.now() - timedelta(seconds=self.__session_exists_timeout)


zabbix_api = ZabbixAPIConnector()
