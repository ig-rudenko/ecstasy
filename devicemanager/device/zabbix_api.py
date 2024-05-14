from datetime import datetime, timedelta
from typing import Callable, Any, Optional

from pyzabbix import ZabbixAPI, ZabbixAPIException
from requests import RequestException


class ZabbixAPIConnector:
    """Конфигурация для работы с Zabbix API"""

    __zabbix_url: str = ""
    __zabbix_user: str = ""
    __zabbix_password: str = ""
    __init_load_function: Optional[Callable[[], Any]] = None

    def __init__(self, timeout: int = 2):
        self.timeout = timeout
        self.__session_exists_timeout = 60
        self.__session_created: datetime | None = None
        self._zabbix_connection: ZabbixAPI = ZabbixAPI()

    def set_init_load_function(self, func: Callable):
        self.__init_load_function = func

    @property
    def zabbix_url(self):
        self.__init_load()
        return self.__zabbix_url

    @property
    def zabbix_user(self):
        self.__init_load()
        return self.__zabbix_user

    @property
    def zabbix_password(self):
        self.__init_load()
        return self.__zabbix_password

    def set(self, obj):
        """Задаем настройки"""
        self.__zabbix_url = str(getattr(obj, "url", ""))
        self.__zabbix_user = str(getattr(obj, "login", ""))
        self.__zabbix_password = str(getattr(obj, "password", ""))

    def connect(self):
        if not self.__session_created or self.__session_created < datetime.now() - timedelta(
            seconds=self.__session_exists_timeout
        ):
            self._zabbix_connection = ZabbixAPI(server=self.zabbix_url, timeout=self.timeout)
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

    def __init_load(self):
        """Загрузка настроек Zabbix API из функции"""
        if (
            self.__init_load_function is not None
            and callable(self.__init_load_function)
            and not (self.__zabbix_url and self.__zabbix_user and self.__zabbix_password)
        ):
            print("Загрузка настроек Zabbix API")
            self.set(self.__init_load_function())


zabbix_api = ZabbixAPIConnector()
