from requests import Session
from django.db import DatabaseError
from pyzabbix import ZabbixAPI

from app_settings.models import ZabbixConfig


class ZabbixAPIConnection:
    """Конфигурация для работы с Zabbix API"""

    ZABBIX_URL: str = ""
    ZABBIX_USER: str = ""
    ZABBIX_PASSWORD: str = ""

    def __init__(self, timeout: int = 2):
        self.timeout = timeout
        self._zabbix_connection: ZabbixAPI = ZabbixAPI()
        self._session = self.get_session()

    @staticmethod
    def get_session() -> Session:
        session = Session()
        session.verify = False
        return session

    @staticmethod
    def set(obj):
        """Задаем настройки"""
        ZabbixAPIConnection.ZABBIX_URL = obj.url
        ZabbixAPIConnection.ZABBIX_USER = obj.login
        ZabbixAPIConnection.ZABBIX_PASSWORD = obj.password

    def connect(self) -> ZabbixAPI:
        self._zabbix_connection = ZabbixAPI(
            server=self.ZABBIX_URL, session=self._session, timeout=self.timeout
        )
        self._zabbix_connection.login(user=self.ZABBIX_USER, password=self.ZABBIX_PASSWORD)
        return self._zabbix_connection


try:
    # Устанавливаем конфигурацию для работы с devicemanager
    ZabbixAPIConnection.set(ZabbixConfig.load())
except DatabaseError:
    pass
