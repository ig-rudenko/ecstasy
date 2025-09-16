from typing import Any, Optional

import orjson
from ping3 import ping as socket_ping
from pyzabbix.api import ZabbixAPIException
from requests import RequestException

from check.models import Devices
from check.services.zabbix import get_zabbix_host_info
from devicemanager.remote import RemoteDevice, remote_connector
from devicemanager.zabbix_info_dataclasses import ZabbixHostGroup, ZabbixHostInfo, ZabbixInventory

from ..device_connector.factory import DEFAULT_POOL_SIZE
from ..exceptions import AuthException, BaseDeviceException
from ..vendors.base.types import SimpleAuthObjectProtocol
from .interfaces import Interfaces
from .zabbix_api import zabbix_api


class DeviceManager:
    """
    Собирает информации с Zabbix для одного узла сети.
    Сканирует интерфейсы оборудования в реальном времени.
    """

    def __init__(self, name: str, zabbix_info=True):
        self.name: str = name
        self.ip: str = ""
        self._zabbix_info: ZabbixHostInfo = ZabbixHostInfo()
        self._location = None
        self._zabbix_info_collected = False  # Уже была собрана информация от Zabbix
        if zabbix_info:  # Собираем данные с Zabbix
            self.collect_zabbix_info()

        self.interfaces = Interfaces()
        self.protocol: str = "telnet"
        self.snmp_community = ""
        self.auth_obj: SimpleAuthObjectProtocol | None = None
        self.success_auth: dict = {}
        self.pool_size = DEFAULT_POOL_SIZE

    def collect_zabbix_info(self):
        """Собирает информацию по данному оборудованию из Zabbix"""
        zabbix_info = get_zabbix_host_info(self.name)
        if not zabbix_info:
            return

        # Форматируем вывод активировано/деактивировано для узла сети
        zabbix_info["status"] = 1 if zabbix_info["status"] == "0" else 0
        # Создаем уникальный кортеж ip адресов
        zabbix_info["interfaces"] = tuple(sorted({i["ip"] for i in zabbix_info["interfaces"]}))

        # Инвентарные данные
        inventory = zabbix_info["inventory"].values() if zabbix_info["inventory"] else {}
        del zabbix_info["inventory"]

        # Группы
        groups = zabbix_info["groups"] if zabbix_info["groups"] else {}
        del zabbix_info["groups"]

        self._zabbix_info = ZabbixHostInfo(
            *zabbix_info.values(),
            inventory=ZabbixInventory(*inventory),
            hostgroups=[ZabbixHostGroup(*group.values()) for group in groups],
        )
        self._zabbix_info_collected = True

        if not self.ip:
            self.ip = [
                i
                for i in self.zabbix_info.ip
                if len(self.zabbix_info.ip) > 1 and i != "127.0.0.1" or len(self.zabbix_info.ip) == 1
            ][0]

    def push_zabbix_inventory(self):
        """Обновляем инвентарные данные узла сети в Zabbix"""
        try:
            with zabbix_api.connect() as zbx:
                zbx.host.update(
                    hostid=self.zabbix_info.hostid,
                    inventory={
                        key: value
                        for key, value in self.zabbix_info.inventory.__dict__.items()
                        if value  # Только заполненные поля
                    },
                )
        except (RequestException, ZabbixAPIException):
            pass

    @property
    def zabbix_info(self) -> ZabbixHostInfo:
        """Обращаемся к информации из Zabbix"""
        return self._zabbix_info

    @classmethod
    def from_model(cls, model_dev: Devices, zabbix_info=True) -> "DeviceManager":
        dev = cls(model_dev.name, zabbix_info=False)
        dev.ip = model_dev.ip
        dev.protocol = model_dev.port_scan_protocol
        dev.snmp_community = model_dev.snmp_community or ""
        dev.auth_obj = model_dev.auth_group  # type: ignore
        dev.pool_size = model_dev.connection_pool_size
        if zabbix_info:
            dev.collect_zabbix_info()
        return dev

    @classmethod
    def from_hostid(cls, hostid: str) -> Optional["DeviceManager"]:
        """Создаем объект через переданный hostid Zabbix"""
        try:
            with zabbix_api.connect() as zbx:
                host = zbx.host.get(hostids=hostid, output=["name"])
            if host:
                return DeviceManager(host[0]["name"])
        except (RequestException, ZabbixAPIException):
            pass
        return None

    def collect_interfaces(
        self,
        vlans=True,
        current_status=False,
        auth_obj=None,
        raise_exception=False,
        make_session_global=True,
    ) -> None:
        """Собираем интерфейсы оборудования"""

        if not current_status:  # Смотрим из истории
            self._get_interfaces_from_history(with_vlans=vlans)

        elif self.protocol in {"snmp", "telnet", "ssh"}:
            # CMD
            try:
                self._get_interfaces_from_connection(
                    with_vlans=vlans,
                    auth_obj=auth_obj,
                    make_session_global=make_session_global,
                )
            except BaseDeviceException as exc:
                if raise_exception:
                    raise exc

    def _get_interfaces_from_history(self, with_vlans: bool):
        from net_tools.models import DevicesInfo

        try:
            device_data_history = DevicesInfo.objects.get(dev__name=self.name)
            json_data = device_data_history.vlans if with_vlans else device_data_history.interfaces
            self.interfaces = Interfaces(orjson.loads(json_data or "[]"))

        except DevicesInfo.DoesNotExist:
            self.interfaces = Interfaces()

    def _get_interfaces_from_connection(self, with_vlans: bool, auth_obj, make_session_global=True):
        auth_obj = auth_obj or self.auth_obj
        if not auth_obj:
            raise AuthException("Не указан объект авторизации!", ip=self.ip)

        session = remote_connector.create(
            ip=self.ip,
            port_scan_protocol=self.protocol,
            cmd_protocol=self.protocol if self.protocol != "snmp" else "telnet",
            snmp_community=self.snmp_community,
            auth_obj=auth_obj or self.auth_obj,
            make_session_global=make_session_global,
            pool_size=self.pool_size,
        )

        sys_info = session.get_system_info()

        if sys_info.get("model"):
            self.zabbix_info.inventory.model = sys_info["model"]

        if sys_info.get("vendor"):
            self.zabbix_info.inventory.vendor = sys_info["vendor"]

        if sys_info.get("serialno"):
            self.zabbix_info.inventory.serialno_a = sys_info["serialno"]

        if sys_info.get("mac"):
            self.zabbix_info.inventory.macaddress_a = sys_info["mac"]

        if sys_info.get("os_version"):
            self.zabbix_info.inventory.os_full = sys_info["os_version"]

        if with_vlans:
            # Если не получилось собрать vlan тогда собираем интерфейсы
            self.interfaces = Interfaces(session.get_vlans())
        else:
            self.interfaces = Interfaces(session.get_interfaces())

    def __str__(self):
        return f'DeviceManager(name="{self.name}", ip="{"; ".join(self._zabbix_info.ip)}")'

    def __repr__(self):
        return self.__str__()

    def ping(self) -> int:
        """Пингуем устройство"""

        if not self.ip:
            self.collect_zabbix_info()
            if not self.ip:
                return -1
        if socket_ping(self.ip, timeout=2):
            return 1

        return 0

    def connect(self, protocol: str = "", auth_obj: Any = None, make_session_global=True) -> RemoteDevice:
        """
        Устанавливаем подключение к оборудованию
        """

        return remote_connector.create(
            self.ip,
            cmd_protocol=protocol or self.protocol,
            port_scan_protocol=protocol or self.protocol,
            snmp_community="",
            auth_obj=auth_obj or self.auth_obj,
            make_session_global=make_session_global,
            pool_size=self.pool_size,
        )
