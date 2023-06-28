import orjson
from typing import Any

from ping3 import ping as socket_ping
from requests import ConnectionError as ZabbixConnectionError
from geopy.geocoders import Nominatim

from .interfaces import Interfaces
from .zabbix_api import ZabbixAPIConnection
from .. import snmp
from ..dc import DeviceFactory
from ..exceptions import (
    TelnetConnectionError,
    TelnetLoginError,
    UnknownDeviceError,
)
from devicemanager.zabbix_info_dataclasses import (
    ZabbixHostInfo,
    ZabbixInventory,
    ZabbixHostGroup,
    Location,
)


class DeviceManager:
    """
    Собирает информации с Zabbix для одного узла сети.
    Сканирует интерфейсы оборудования в реальном времени.
    """

    def __init__(self, name, zabbix_info=True):
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
        self.auth_obj = None
        self.success_auth: dict = {}

    def collect_zabbix_info(self):
        """Собирает информацию по данному оборудованию из Zabbix"""

        try:
            with ZabbixAPIConnection().connect() as zbx:
                zabbix_info = zbx.host.get(
                    filter={"name": self.name},
                    output=["hostid", "host", "name", "status", "description"],
                    selectGroups=["groupid", "name"],
                    selectInterfaces=["ip"],
                    selectInventory="extend",
                )
        except ZabbixConnectionError:
            return

        if zabbix_info:
            # Форматируем вывод активировано/деактивировано для узла сети
            zabbix_info[0]["status"] = 1 if zabbix_info[0]["status"] == "0" else 0
            # Создаем уникальный кортеж ip адресов
            zabbix_info[0]["interfaces"] = tuple(
                sorted(list({i["ip"] for i in zabbix_info[0]["interfaces"]}))
            )

            # Инвентарные данные
            inventory = zabbix_info[0]["inventory"].values() if zabbix_info[0]["inventory"] else {}
            del zabbix_info[0]["inventory"]

            # Группы
            groups = zabbix_info[0]["groups"] if zabbix_info[0]["groups"] else {}
            del zabbix_info[0]["groups"]

            self._zabbix_info = ZabbixHostInfo(
                *zabbix_info[0].values(),
                inventory=ZabbixInventory(*inventory),
                hostgroups=tuple(ZabbixHostGroup(*group.values()) for group in groups),
            )
            self._zabbix_info_collected = True

            if not self.ip:
                self.ip = [
                    i
                    for i in self.zabbix_info.ip
                    if len(self.zabbix_info.ip) > 1
                    and i != "127.0.0.1"
                    or len(self.zabbix_info.ip) == 1
                ][0]

    def push_zabbix_inventory(self):
        """Обновляем инвентарные данные узла сети в Zabbix"""
        try:
            with ZabbixAPIConnection().connect() as zbx:
                zbx.host.update(
                    hostid=self.zabbix_info.hostid,
                    inventory={
                        key: value
                        for key, value in self.zabbix_info.inventory.__dict__.items()
                        if value  # Только заполненные поля
                    },
                )
        except ZabbixConnectionError:
            pass

    @property
    def zabbix_info(self) -> ZabbixHostInfo:
        """Обращаемся к информации из Zabbix"""
        return self._zabbix_info

    @classmethod
    def from_model(cls, model_dev, zabbix_info=True) -> "DeviceManager":
        dev = cls(model_dev.name, zabbix_info=False)
        dev.ip = model_dev.ip
        dev.protocol = model_dev.port_scan_protocol
        dev.snmp_community = model_dev.snmp_community
        dev.auth_obj = model_dev.auth_group
        if zabbix_info:
            dev.collect_zabbix_info()
        return dev

    @classmethod
    def from_hostid(cls, hostid: str) -> ("DeviceManager", None):
        """Создаем объект через переданный hostid Zabbix"""
        try:
            with ZabbixAPIConnection().connect() as zbx:
                host = zbx.host.get(hostids=hostid, output=["name"])
            if host:
                return DeviceManager(host[0]["name"])
        except ZabbixConnectionError:
            pass
        return None

    def collect_interfaces(
        self, vlans=True, current_status=False, auth_obj=None, *args, **kwargs
    ) -> str:
        """Собираем интерфейсы оборудования"""

        if not current_status:  # Смотрим из истории
            from net_tools.models import DevicesInfo

            try:
                device_data_history = DevicesInfo.objects.get(dev__name=self.name)

                self.interfaces = Interfaces(
                    orjson.loads(
                        device_data_history.vlans if vlans else device_data_history.interfaces
                    )
                )
            except DevicesInfo.DoesNotExist:
                self.interfaces = Interfaces()

        # Собираем интерфейсы в реальном времени с устройства
        elif self.protocol == "snmp":
            # SNMP
            raw_interfaces = snmp.show_interfaces(device_ip=self.ip, community=self.snmp_community)
            self.interfaces = Interfaces(
                [
                    {
                        "Interface": line[0],
                        "Status": "admin down" if "down" in line[1] else line[2],
                        "Description": line[3],
                    }
                    for line in raw_interfaces
                    if snmp.physical_interface(line[0])
                ]
            )

        else:
            # CMD
            if not auth_obj and not self.auth_obj:
                return "Не указан профиль авторизации для данного оборудования"
            if not self.protocol:
                return "Не указан протокол для подключения к оборудованию"

            try:
                with self.connect(
                    self.protocol, auth_obj=auth_obj or self.auth_obj, *args, **kwargs
                ) as session:
                    if session.model:
                        self.zabbix_info.inventory.model = session.model

                    if session.vendor:
                        self.zabbix_info.inventory.vendor = session.vendor

                    if session.serialno:
                        self.zabbix_info.inventory.serialno_a = session.serialno

                    if session.mac:
                        self.zabbix_info.inventory.macaddress_a = session.mac

                    # Получаем верные логин/пароль
                    self.success_auth = session.auth

                    if vlans:
                        # Если не получилось собрать vlan тогда собираем интерфейсы
                        self.interfaces = Interfaces(
                            session.get_vlans() or session.get_interfaces()
                        )
                    else:
                        self.interfaces = Interfaces(session.get_interfaces())

            except (TelnetConnectionError, TelnetLoginError, UnknownDeviceError) as e:
                return str(e)

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

    def address(self):
        """Выводит местоположение оборудования"""

        if not self._zabbix_info_collected:
            self.collect_zabbix_info()
        if self._zabbix_info.inventory.location:
            return self._zabbix_info.inventory.location
        if (
            self._zabbix_info.inventory.location_lat
            and self._zabbix_info.inventory.location_lon
            and not self._location
        ):
            location = Nominatim(user_agent="coordinateconverter").reverse(
                ", ".join(self._zabbix_info.inventory.coordinates())
            )
            if location:
                self._location = Location(**location.raw["address"])
        return self._location

    def connect(self, protocol: str = None, auth_obj: Any = None, *args, **kwargs) -> DeviceFactory:
        """
        Устанавливаем подключение к оборудованию

        :param protocol: Протокол подключения telnet/ssh
        :param auth_obj: Объект профиля авторизации с атрибутами "login", "password", "privilege_mode_password"
        :return: Экземпляр класса в зависимости от типа оборудования с установленным подключением
        """

        return DeviceFactory(
            self.ip,
            protocol=protocol or self.protocol,
            auth_obj=auth_obj or self.auth_obj,
            *args,
            **kwargs,
        )