from datetime import datetime, timedelta
from typing import Any

from django.conf import settings
from pyzabbix import ZabbixAPI, ZabbixAPIException
from requests import RequestException, Session

from app_settings.lazy_settings import LazyConfigLoader, LazyStringAttribute


class ZabbixAPIConnector(LazyConfigLoader):
    """Конфигурация для работы с Zabbix API"""

    zabbix_url: str = LazyStringAttribute()  # type: ignore
    zabbix_user: str = LazyStringAttribute()  # type: ignore
    zabbix_password: str = LazyStringAttribute()  # type: ignore

    def __init__(self, timeout: int = 2):
        self.timeout = timeout
        self.__session_exists_timeout = 60
        self.__session_created: datetime | None = None
        self._zabbix_connection: ZabbixAPI = ZabbixAPI()

    @staticmethod
    def get_session() -> Session:
        session = Session()
        if not settings.VERIFY_ZABBIX_CONNECTION:
            session.verify = False
        return session

    def set_lazy_attributes(self, obj: Any):
        print("Инициализация атрибутов класса ZabbixAPIConnector", obj)
        if not obj:
            return
        self.zabbix_url = str(getattr(obj, "url", ""))
        self.zabbix_user = str(getattr(obj, "login", ""))
        self.zabbix_password = str(getattr(obj, "password", ""))

    def connect(self):
        if not self.__session_created or self.__session_created < datetime.now() - timedelta(
            seconds=self.__session_exists_timeout
        ):
            self._zabbix_connection = ZabbixAPI(
                server=self.zabbix_url,
                timeout=self.timeout,
                session=self.get_session(),
            )
            self.__session_created = datetime.now()

            try:
                self._zabbix_connection.login(user=self.zabbix_user, password=self.zabbix_password)
            except (ConnectionError, ZabbixAPIException) as exc:
                raise RequestException("Не удалось подключиться к Zabbix") from exc

        return self

    def __enter__(self) -> ZabbixAPI:
        return self._zabbix_connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.__session_created and self.__session_created < datetime.now() - timedelta(
            seconds=self.__session_exists_timeout
        ):
            self._zabbix_connection.__exit__(exc_type, exc_val, exc_tb)


zabbix_api = ZabbixAPIConnector()
