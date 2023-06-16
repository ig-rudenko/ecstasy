"""
Модуль для взаимодействия с узлами сети через Zabbix API
Сбор интерфейсов
"""

import re
import orjson
from typing import Any, List, Sequence, Optional
from concurrent.futures import ThreadPoolExecutor

import tabulate
from django.db import DatabaseError
from ping3 import ping as socket_ping
from pyzabbix import ZabbixAPI
from requests import ConnectionError as ZabbixConnectionError
from alive_progress import alive_bar
from geopy.geocoders import Nominatim

from app_settings.models import ZabbixConfig
from ecstasy_project.settings import NON_ABON_INTERFACES_PATTERN
from . import snmp
from .dc import DeviceFactory
from .exceptions import (
    AuthException,
    TelnetConnectionError,
    TelnetLoginError,
    UnknownDeviceError,
)
from .vendors.base.helpers import range_to_numbers
from .zabbix_info_dataclasses import (
    ZabbixHostInfo,
    ZabbixInventory,
    ZabbixHostGroup,
    Interface,
    Location,
)


class ZabbixAPIConfig:
    """Конфигурация для работы с Zabbix API"""

    ZABBIX_URL: str = ""
    ZABBIX_USER: str = ""
    ZABBIX_PASSWORD: str = ""
    TABLE_FORMAT = "simple"

    @staticmethod
    def set(obj):
        """Задаем настройки"""
        ZabbixAPIConfig.ZABBIX_URL = obj.url
        ZabbixAPIConfig.ZABBIX_USER = obj.login
        ZabbixAPIConfig.ZABBIX_PASSWORD = obj.password


try:
    # Устанавливаем конфигурацию для работы с devicemanager
    ZabbixAPIConfig.set(ZabbixConfig.load())
except DatabaseError:
    pass


class Interfaces:
    """
    Взаимодействие с интерфейсами оборудования

    >>> Interfaces(['eth1', 'up', 'description', [10, 20]])

    >>> Interfaces([{"Interface": "eth1", "Status": "up", "Description": "desc", "VLAN's": [10, 20]}])

    >>> Interfaces([{'Interface': '1', 'Admin Status': 'up', 'Link': 'up', 'Description': 'desc', "VLAN's": [1, 2]}])

    >>> Interfaces([Interface()])

    """

    @staticmethod
    def _parse_vlans_line(vlans: list) -> List[int]:
        """
        Эта функция принимает список VLAN, преобразует любые диапазоны VLAN, указанные в виде строк, в список
        целых чисел и возвращает список всех VLAN в виде целых чисел.

        Сначала функция проверяет, является ли каждый элемент во входном списке строкой или целым числом.
        Если это строка, она использует функцию `range_to_numbers()`, чтобы преобразовать ее в список целых чисел
        и добавить ее в `vlans_list`.

        :param vlans: Ожидается, что параметр "vlans" будет списком VLAN, который может быть либо целым числом, либо
        строкой, представляющей диапазон VLAN.

        :return: Список целых чисел, представляющих VLAN. Если ввод не является списком, возвращается пустой список.
        """

        if not isinstance(vlans, list):
            return []

        vlans_list = []
        for vlan in vlans:
            if isinstance(vlan, str):
                vlans_list += range_to_numbers(vlan)
            if isinstance(vlan, int):
                vlans_list.append(vlan)
        return vlans_list

    def __init__(self, data: Optional[Sequence] = None):
        if not data:  # Если не были переданы интерфейсы, то создаем пустой список
            self.__interfaces = []
        else:
            self.__interfaces: List[Interface] = []

            for intf in data:
                # Если был передан словарь
                if isinstance(intf, dict):
                    if intf.get("Status") is None:
                        intf["Status"] = (
                            "admin down" if intf["Admin Status"] == "down" else intf["Link"]
                        )

                    self.__interfaces.append(
                        Interface(
                            intf["Interface"].strip(),
                            intf["Status"],
                            intf["Description"].strip(),
                            self._parse_vlans_line(intf.get("VLAN's", [])),
                        )
                    )

                # Если был передан список, кортеж
                elif isinstance(intf, (list, tuple)):
                    if len(intf) == 3:  # Без VLAN
                        self.__interfaces.append(Interface(intf[0], intf[1], intf[2], []))
                    elif len(intf) == 4:  # + VLAN
                        self.__interfaces.append(
                            Interface(intf[0], intf[1], intf[2], self._parse_vlans_line(intf[3]))
                        )

                # Если был передан объект Interface
                elif isinstance(intf, Interface):
                    self.__interfaces.append(intf)

    def __str__(self):
        if not self.__interfaces:
            return "None"
        return tabulate.tabulate(
            [
                [
                    i.name,
                    i.status,
                    i.desc.strip(),
                    ", ".join(map(str, i.vlan)) or " " if i.vlan else " ",
                ]
                for i in self.__interfaces
            ],
            headers=["Interface", "Status", "Description", "VLAN"],
            maxcolwidths=[None, None, None, 40],
            tablefmt=ZabbixAPIConfig.TABLE_FORMAT,
        )

    def __getitem__(self, item):
        """Обращение к интерфейсам"""
        if not self.__interfaces:
            # Если не существует интерфейсов, то возвращаем пустой, чтобы не было ошибки
            return Interface()
        if isinstance(item, int):
            return self.__interfaces[item]
        if isinstance(item, str):
            for i in self.__interfaces:
                if i.name == item:
                    return i
        return Interface()

    def __enter__(self):
        return self.__interfaces

    def __iter__(self):
        return iter(self.__interfaces)

    def __bool__(self):
        return bool(self.__interfaces)

    @property
    def count(self) -> int:
        """Количество интерфейсов"""
        return len(self.__interfaces)

    def json(self):
        return [
            {
                "Interface": line.name,
                "Status": line.status,
                "Description": line.desc,
                "VLAN's": line.vlan,
            }
            for line in self.__interfaces
        ]

    def physical(self):
        res = []
        i = 0
        intf = self.__interfaces

        while i < len(intf):
            # Комбо-порт. Надо выбрать один.
            if (
                "(C)" in intf[i].name
                and "(F)" in intf[i + 1].name
                and re.findall(r"^\d+", intf[i].name) == re.findall(r"^\d+", intf[i].name)
            ):
                # Выбираем, какой комбо порт добавить.
                # Смотрим состояние и добавляем активный.
                combo_interface = intf[i] if intf[i].is_up else intf[i + 1]
                # Выбираем описание комбо порта, если нет на (C), то берем с (F).
                combo_interface.desc = intf[i].desc if intf[i].has_desc else intf[i + 1].desc
                res.append(combo_interface)
                i += 2  # Пропускаем 2 комбо-порта.

            else:
                # Добавляем обычные порты.
                res.append(intf[i])
                i += 1

        return Interfaces(res)

    def up(self, only_count=False):
        """
        Интерфейсы, состояние которых UP

        :param only_count: bool Только кол-во?
        """
        count = 0
        intf = []
        for i in self.__interfaces:
            if i.is_up:
                count += 1
                if not only_count:
                    intf.append(i)
        return count if only_count else Interfaces(intf)

    def with_description(self, only_count=False):
        """
        Интерфейсы, на которых есть описание
        :param only_count: bool Только кол-во?
        """
        count = 0
        intf = []
        for i in self.__interfaces:
            if i.has_desc:
                count += 1
                if not only_count:
                    intf.append(i)
        return count if only_count else Interfaces(intf)

    def down(self, only_count=False):
        """Интерфейсы, состояние которых DOWN

        :param only_count: bool Только кол-во?
        """
        count = 0
        intf = []
        for i in self.__interfaces:
            if not i.is_up:
                count += 1
                if not only_count:
                    intf.append(i)
        return count if only_count else Interfaces(intf)

    def admin_down(self, only_count=False):
        """Интерфейсы, состояние которых ADMIN DOWN

        :param only_count: bool Только кол-во?
        """
        count = 0
        intf = []
        for i in self.__interfaces:
            if i.status == "admin down":
                count += 1
                if not only_count:
                    intf.append(i)
        return count if only_count else Interfaces(intf)

    def free(self, only_count=False):
        """
        Возвращает список свободных интерфейсов или только их кол-во

        :param only_count: bool Только кол-во?
        """
        count = 0
        intf = []
        for i in self.__interfaces:
            if not i.is_up and not i.has_desc:
                count += 1
                if not only_count:
                    intf.append(i)
        return count if only_count else Interfaces(intf)

    def non_system(self, only_count=False):
        """
        Возвращает список интерфейсов, которые не используются для связи с другими узлами сети

        :param only_count: bool Только кол-во?
        """
        count = 0
        intf = []
        for i in self.__interfaces:
            if NON_ABON_INTERFACES_PATTERN.findall(i.desc):
                continue
            if not only_count:
                intf.append(i)
        return count if only_count else Interfaces(intf)

    @property
    def unique_vlans(self) -> list:
        """Возвращает отсортированный список VLAN'ов, которые имеются на портах"""
        vlans = set()
        for i in self.__interfaces:
            vlans = vlans.union({v for v in i.vlan if v.isdigit()})
        return sorted([int(v) for v in vlans])

    def with_vlans(self, vlans: list):
        """
        Интерфейсы, которые имеют переданные vlans

        :param vlans: Список vlan'ов
        :return: Interfaces
        """
        if isinstance(vlans, list):
            vlans = list(map(int, vlans))
            return Interfaces([i for i in self.__interfaces if set(vlans) & set(i.vlan)])
        return Interfaces()

    def filter_by_desc(self, pattern: str):
        """Интерфейсы, описание которых совпадает с шаблоном"""
        return Interfaces([i for i in self.__interfaces if re.findall(pattern, i.desc)])


class DevicesCollection:
    """Создает коллекцию из узлов сети, для комплексной работы с ними"""

    def __init__(self, devs: (list, tuple), intf_coll=False, zbx_coll=False):
        self.interfaces_collected = intf_coll  # Были собраны интерфейсы
        self.zabbix_collected = zbx_coll  # Были собраны из Zabbix данные
        self.auth_groups: list = []

        # Если верно передан параметр
        if isinstance(devs, (list, tuple)):
            if all(isinstance(d, DeviceManager) for d in devs):
                self.collection: List[DeviceManager] = devs
            elif all(isinstance(d, str) for d in devs):
                self.collection: List[DeviceManager] = [DeviceManager(d) for d in devs]
            else:
                raise TypeError(
                    "Коллекция должна состоять из объектов DeviceManager или содержать имена устройств"
                )
        else:
            raise TypeError(f'Коллекция принимает список или кортеж, а не "{type(devs)}"')

    @property
    def count(self) -> int:
        """Количество устройств в коллекции"""

        return len(self.collection)

    @classmethod
    def from_zabbix_groups(cls, groups_name: (str, list), zabbix_info: bool) -> "DevicesCollection":
        """
        Создаем коллекцию из групп узлов сети Zabbix

        :param groups_name: Имя группы или список имен групп Zabbix
        :param zabbix_info: Собрать информацию оборудования из Zabbix в момент создания коллекции?
        """
        try:
            with ZabbixAPI(server=ZabbixAPIConfig.ZABBIX_URL) as zbx:
                zbx.login(ZabbixAPIConfig.ZABBIX_USER, ZabbixAPIConfig.ZABBIX_PASSWORD)
                groups = zbx.hostgroup.get(filter={"name": groups_name}, output=["groupid"])
                if groups:
                    hosts = zbx.host.get(
                        groupids=[g["groupid"] for g in groups],
                        output=["name"],
                        sortfield=["name"],
                    )
                else:
                    return DevicesCollection([])
        except ZabbixConnectionError:
            return DevicesCollection([])

        with alive_bar(len(hosts), title="Создаем коллекцию") as bar:
            devs = []
            for host in hosts:
                bar.text = f'-> Собираем данные с {host["name"]}'
                devs.append(DeviceManager(host["name"], zabbix_info=zabbix_info))
                bar()
        return DevicesCollection(devs)

    @classmethod
    def from_zabbix_ips(cls, ips: (str, list), zabbix_info: bool) -> "DevicesCollection":
        """
        Создаем коллекцию из переданных IP адресов

        :param ips: IP адрес или список IP адресов
        :param zabbix_info: Собрать информацию оборудования из Zabbix в момент создания коллекции?
        """

        if ips.count(" "):
            ips = ips.split()
        try:
            with ZabbixAPI(server=ZabbixAPIConfig.ZABBIX_URL) as zbx:
                zbx.login(ZabbixAPIConfig.ZABBIX_USER, ZabbixAPIConfig.ZABBIX_PASSWORD)
                hosts = zbx.host.get(filter={"ip": ips}, output=["name"], sortfield=["name"])
        except ZabbixConnectionError:
            return DevicesCollection([])

        if hosts:
            with alive_bar(len(hosts), title="Создаем коллекцию") as bar:
                devs = []
                for h in hosts:
                    bar.text = f'-> Собираем данные с {h["name"]}'
                    devs.append(DeviceManager(h["name"], zabbix_info=zabbix_info))
                    bar()
            return DevicesCollection(devs)

        return DevicesCollection([])

    def __str__(self):
        string = "DevicesCollection:\n"
        s = len(str(len(self.collection)))  # Длина поля индекса

        # Если коллекция больше 7 элементов
        if len(self.collection) > 7:
            for i, d in enumerate(self.collection[:3]):  # Первые 3 устройства
                string += f"{i:<{s}}  {d}\n"
            string += " " * s + "  ...\n"
            # Последние 3 устройства
            for i, d in enumerate(self.collection[-3:], len(self.collection) - 3):
                string += f"{i:<{s}}  {d}\n"

        # Вывод всех устройств
        else:
            for i, d in enumerate(self.collection):
                string += f"{i:<{s}}  {d}\n"

        return string

    def filter_by_name(self, pattern: str) -> "DevicesCollection":
        """
        Фильтр по имени узлов сети с помощью регулярного выражения
        """
        return DevicesCollection([dev for dev in self.collection if re.search(pattern, dev.name)])

    def filter_by(self, field: str, pattern: str) -> "DevicesCollection":
        """
        Фильтр по переданному полю узлов сети с помощью регулярного выражения
        """
        return DevicesCollection(
            [dev for dev in self.collection if re.search(pattern, str(dev.__dict__[field]))]
        )

    def filter_by_inventory(self, inventory: str, pattern: str) -> "DevicesCollection":
        """
        Фильтр по переданному полю в инвентаризации узлов сети с помощью регулярного выражения
        """
        if not self.zabbix_collected:
            self.collect_zabbix_info()
        return DevicesCollection(
            [
                d
                for d in self.collection
                if re.match(pattern, str(d.zabbix_info.inventory.__dict__[inventory]))
            ]
        )

    def __getitem__(self, item):
        return self.collection[item]

    def __add__(self, other):
        if isinstance(other, DeviceManager):
            self.collection += [other]
        if isinstance(other, DevicesCollection):
            self.collection += other.collection
        return self.collection

    def __radd__(self, other):
        if isinstance(other, DeviceManager):
            self.collection = [other] + self.collection
        if isinstance(other, DevicesCollection):
            self.collection = other.collection + self.collection
        return self.collection

    def __iadd__(self, other):
        return self.__add__(other)

    def collect_interfaces(self, vlans, current_status=False) -> "DevicesCollection":
        """Конкурентно собираем интерфейсы оборудования из коллекции"""

        if current_status and not self.auth_groups:
            raise AuthException("Не указаны группы авторизации для коллекции!")

        with alive_bar(self.count, title="Собираем интерфейсы") as bar:
            with ThreadPoolExecutor() as ex:
                for device in self.collection:
                    ex.submit(device.collect_interfaces, vlans, current_status, bar)
        self.interfaces_collected = True
        return self

    def collect_zabbix_info(self) -> "DevicesCollection":
        """Конкурентно собираем информацию об устройствах в коллекции из Zabbix"""

        with ThreadPoolExecutor() as ex:
            for device in self.collection:
                ex.submit(device.collect_zabbix_info)
        self.zabbix_collected = True
        return self

    @property
    def available(self) -> "DevicesCollection":
        """
        Возвращаем новую коллекцию, в которой все узлы сети по информации из Zabbix находятся в активном статусе
        """

        return DevicesCollection([d for d in self.collection if d.zabbix_info.status])

    @property
    def unavailable(self) -> "DevicesCollection":
        """
        Возвращаем новую коллекцию, в которой все узлы сети по информации из Zabbix имеют неактивный статус
        """

        return DevicesCollection([d for d in self.collection if not d.zabbix_info.status])

    def sort_by(self, field: str) -> "DevicesCollection":
        """
        Сортировка коллекции по указанному параметру

        :param field: name, ip, description, type, type_full, name, alias, os, os_full, os_short, serialno_a,
                    serialno_b, tag, asset_tag, macaddress_a, macaddress_b, hardware, hardware_full, software,
                    software_full, software_app_a, software_app_b, software_app_c, software_app_d, software_app_e,
                    contact, location, location_lat, location_lon, notes, chassis, model, hw_arch, vendor,
                    contract_number, installer_name, deployment_status, url_a, url_b, url_c, host_networks,
                    host_netmask, host_router, oob_ip, oob_netmask, oob_router, date_hw_purchase, date_hw_install,
                    date_hw_expiry, date_hw_decomm, site_address_a, site_address_b, site_address_c, site_city,
                    site_state, site_country, site_zip, site_rack, site_notes, poc_1_name, poc_1_email, poc_1_phone_a,
                    poc_1_phone_b, poc_1_cell, poc_1_screen, poc_1_notes, poc_2_name, poc_2_email, poc_2_phone_a,
                    poc_2_phone_b, poc_2_cell, poc_2_screen, poc_2_notes
        :return: "DeviceCollection"
        """
        if not self.zabbix_collected and field != "name":
            self.collect_zabbix_info()

        if field in ZabbixInventory.__dict__:
            return DevicesCollection(
                sorted(
                    self.collection,
                    key=lambda d: d.zabbix_info.inventory.__dict__[field],
                )
            )

        return DevicesCollection(sorted(self.collection, key=lambda d: d.__dict__[field]))

    def ping_devs(self, unavailable=False) -> "DevicesCollection":
        """
        Конкурентно пингуем оборудования из коллекции и возвращаем новую коллекцию
         из доступных или недоступных узлов сети в зависимости от параметра unavailable

        :param unavailable: Возвращать недоступные?
        """

        available_devices, unavailable_devices = [], []

        def __ping_device(dev):
            """Пингуем оборудование и записываем его в нужный список"""
            if dev.ping() and not unavailable:
                available_devices.append(dev)

            elif unavailable:
                unavailable_devices.append(dev)

        # Запускаем пинг
        with ThreadPoolExecutor() as executor:
            for device in self.collection:
                executor.submit(__ping_device, device)

        if unavailable:
            return DevicesCollection(unavailable_devices)

        return DevicesCollection(available_devices)


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
            with ZabbixAPI(server=ZabbixAPIConfig.ZABBIX_URL, timeout=5) as zbx:
                zbx.login(ZabbixAPIConfig.ZABBIX_USER, ZabbixAPIConfig.ZABBIX_PASSWORD)
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
            with ZabbixAPI(server=ZabbixAPIConfig.ZABBIX_URL) as zbx:
                zbx.login(ZabbixAPIConfig.ZABBIX_USER, ZabbixAPIConfig.ZABBIX_PASSWORD)
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
    def from_ip(cls, ip: str) -> DevicesCollection:
        """
        Создаем коллекцию оборудований по IP адресу
        Коллекция, потому что по данному IP могут быть несколько записей в Zabbix
        """
        try:
            with ZabbixAPI(server=ZabbixAPIConfig.ZABBIX_URL) as zbx:
                zbx.login(ZabbixAPIConfig.ZABBIX_USER, ZabbixAPIConfig.ZABBIX_PASSWORD)
                hosts = zbx.host.get(filter={"ip": ip}, output=["name"])
        except ZabbixConnectionError:
            return DevicesCollection([])
        return DevicesCollection([DeviceManager(d["name"]) for d in hosts])

    @classmethod
    def from_hostid(cls, hostid: str) -> ("DeviceManager", None):
        """Создаем объект через переданный hostid Zabbix"""
        try:
            with ZabbixAPI(server=ZabbixAPIConfig.ZABBIX_URL) as zbx:
                zbx.login(ZabbixAPIConfig.ZABBIX_USER, ZabbixAPIConfig.ZABBIX_PASSWORD)
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
