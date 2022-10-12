import json

import requests
import tabulate
import re
import os
import subprocess
from pyzabbix import ZabbixAPI
from typing import List
from concurrent.futures import ThreadPoolExecutor
from geopy.geocoders import Nominatim
from . import snmp

from .zabbix_info_dataclasses import ZabbixHostInfo, ZabbixInventory, ZabbixHostGroup, Interface, Location
from .exceptions import AuthException
from .dc import DeviceFactory, _range_to_numbers
from alive_progress import alive_bar

from typing import Any


class Config:
    ZABBIX_URL: str
    ZABBIX_USER: str
    ZABBIX_PASSWORD: str
    INTERFACE_API_KEY: str
    INTERFACE_API_URL: str
    AUTH_FILE = 'auth.yaml'
    TABLE_FORMAT = "simple"

    @staticmethod
    def set(obj):
        Config.ZABBIX_URL = obj.url
        Config.ZABBIX_USER = obj.login
        Config.ZABBIX_PASSWORD = obj.password


class Interfaces:
    def __init__(self, data=None):
        if not data:  # Если не были переданы интерфейсы, то создаем пустой список
            self.__interfaces = []
        else:
            self.__interfaces: List[Interface, None] = []
            for i, intf in enumerate(data):

                # Если был передан словарь от API
                if isinstance(intf, dict):
                    vlans = []
                    for v in intf.get("VLAN's") or []:
                        vlans += _range_to_numbers(v)

                    if not intf.get('Status'):
                        intf['Status'] = 'admin down' if intf['Admin Status'] == 'down' else intf['Link']

                    self.__interfaces.append(Interface(
                        intf['Interface'].strip(),
                        intf['Status'],
                        intf['Description'].strip(),
                        vlans
                    ))

                # Если был передан список
                elif isinstance(intf, list):
                    if len(intf) == 3:  # Без VLAN
                        self.__interfaces.append(Interface(
                            intf[0], intf[1], intf[2], []
                        ))
                    elif len(intf) == 4:  # + VLAN
                        self.__interfaces.append(Interface(
                            intf[0], intf[1], intf[2], intf[3]
                        ))

                # Если был передан объект Interface
                elif isinstance(intf, Interface):
                    self.__interfaces.append(intf)

    def __str__(self):
        if not self.__interfaces:
            return 'None'
        return tabulate.tabulate(
            [[i.name, i.status, i.desc.strip(), ", ".join(map(str, i.vlan)) or ' ' if i.vlan else ' '] for i in self.__interfaces],
            headers=['Interface', 'Status', 'Description', 'VLAN'],
            maxcolwidths=[None, None, None, 40],
            tablefmt=Config.TABLE_FORMAT
        )

    def __getitem__(self, item):
        """Обращение к интерфейсам"""
        if not self.__interfaces:
            return Interface()  # Если не существует интерфейсов, то возвращаем пустой, чтобы не было ошибки
        return self.__interfaces[item]

    def __bool__(self):
        return self.__interfaces

    @property
    def count(self) -> int:
        """Количество интерфейсов"""
        return len(self.__interfaces)

    def up(self, only_count=False):
        """Интерфейсы, состояние которых UP

        :param only_count: bool Только кол-во?
        """
        c = 0
        intf = []
        for i in self.__interfaces:
            if 'down' not in i.status and 'disable' not in i.status.lower():
                c += 1
                if not only_count:
                    intf.append(i)
        return c if only_count else Interfaces(intf)

    def down(self, only_count=False):
        """Интерфейсы, состояние которых DOWN

        :param only_count: bool Только кол-во?
        """
        c = 0
        intf = []
        for i in self.__interfaces:
            if i.status == 'down':
                c += 1
                if not only_count:
                    intf.append(i)
        return c if only_count else Interfaces(intf)

    def admin_down(self, only_count=False):
        """Интерфейсы, состояние которых ADMIN DOWN

        :param only_count: bool Только кол-во?
        """
        c = 0
        intf = []
        for i in self.__interfaces:
            if i.status == 'admin down':
                c += 1
                if not only_count:
                    intf.append(i)
        return c if only_count else Interfaces(intf)

    def free(self, only_count=False):
        """
        Возвращает список свободных интерфейсов или только их кол-во

        :param only_count: bool Только кол-во?
        """
        c = 0
        intf = []
        for i in self.__interfaces:
            if 'down' in i.status.lower() and (not i.desc or 'HUAWEI, Quidway Series' in i.desc):
                c += 1
                if not only_count:
                    intf.append(i)
        return c if only_count else Interfaces(intf)

    def abons(self, only_count=False):
        """
        Возвращает список интерфейсов, которые не используются для связи с другими узлами сети

        :param only_count: bool Только кол-во?
        """
        c = 0
        intf = []
        for i in self.__interfaces:
            if re.findall(r'power_monitoring|[as]sw\d|dsl|co[pr]m|msan|core|cr\d|nat|mx-\d|dns|bras', i.desc.lower()):
                continue
            if not i.desc and 'down' in i.status:
                continue
            if i.status == 'admin down' or '(F)' in i.name or '(C)' in i.name:
                continue
            if re.findall('Quidway Series', i.desc) and i.status == 'down':
                continue
            c += 1
            if not only_count:
                intf.append(i)
        return c if only_count else Interfaces(intf)

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

    def filter_by_desc(self, pattern: str):
        """Интерфейсы, описание которых совпадает с шаблоном"""
        return Interfaces([i for i in self.__interfaces if re.findall(pattern, i.desc)])


class DevicesCollection:

    def __init__(self, devs: (list, tuple), intf_coll=False, zbx_coll=False):

        self.interfaces_collected = intf_coll  # Были собраны интерфейсы
        self.zabbix_collected = zbx_coll  # Были собраны из Zabbix данные
        self.auth_groups: list = []

        # Если верно передан параметр
        if isinstance(devs, (list, tuple)):
            if all(isinstance(d, Device) for d in devs):
                self.collection: List[Device] = devs
            elif all(isinstance(d, str) for d in devs):
                self.collection: List[Device] = [Device(d) for d in devs]
            else:
                raise TypeError('Коллекция должна состоять из объектов Device или содержать имена устройств')
        else:
            raise TypeError(f'Коллекция принимает список или кортеж, а не "{type(devs)}"')

    @property
    def count(self) -> int:
        return len(self.collection)

    @classmethod
    def from_zabbix_groups(cls, groups_name: (str, list), zabbix_info: bool):
        with ZabbixAPI(server=Config.ZABBIX_URL) as zbx:
            zbx.login(Config.ZABBIX_USER, Config.ZABBIX_PASSWORD)
            groups = zbx.hostgroup.get(
                filter={'name': groups_name},
                output=['groupid']
            )
            if groups:
                hosts = zbx.host.get(
                    groupids=[g['groupid'] for g in groups],
                    output=['name'],
                    sortfield=['name']
                )
            else:
                return []
        with alive_bar(len(hosts), title='Создаем коллекцию') as bar:
            devs = []
            for h in hosts:
                bar.text = f'-> Собираем данные с {h["name"]}'
                devs.append(Device(h['name'], zabbix_info=zabbix_info))
                bar()
        return DevicesCollection(devs)

    @classmethod
    def from_zabbix_ips(cls, ips: (str, list), zabbix_info: bool):
        if ips.count(' '):
            ips = ips.split()
        with ZabbixAPI(server=Config.ZABBIX_URL) as zbx:
            zbx.login(Config.ZABBIX_USER, Config.ZABBIX_PASSWORD)
            hosts = zbx.host.get(
                filter={'ip': ips},
                output=['name'],
                sortfield=['name']
            )
            if hosts:
                with alive_bar(len(hosts), title='Создаем коллекцию') as bar:
                    devs = []
                    for h in hosts:
                        bar.text = f'-> Собираем данные с {h["name"]}'
                        devs.append(Device(h['name'], zabbix_info=zabbix_info))
                        bar()
                return DevicesCollection(devs)
            else:
                return []

    def __str__(self):
        string = 'DevicesCollection:\n'
        s = len(str(len(self.collection)))  # Длина поля индекса

        # Если коллекция больше 7 элементов
        if len(self.collection) > 7:
            for i, d in enumerate(self.collection[:3]):  # Первые 3 устройства
                string += f'{i:<{s}}  {d}\n'
            string += ' '*s + '  ...\n'
            for i, d in enumerate(self.collection[-3:], len(self.collection)-3):  # Последние 3 устройства
                string += f'{i:<{s}}  {d}\n'

        # Вывод всех устройств
        else:
            for i, d in enumerate(self.collection):
                string += f'{i:<{s}}  {d}\n'

        return string

    def filter_by_name(self, pattern: str):
        """Фильтр по имени узлов сети с помощью регулярного выражения"""
        return DevicesCollection([dev for dev in self.collection if re.search(pattern, dev.name)])

    def filter_by(self, field: str, pattern: str):
        """Фильтр по переданному полю узлов сети с помощью регулярного выражения"""
        return DevicesCollection([dev for dev in self.collection if re.search(pattern, str(dev.__dict__[field]))])

    def filter_by_inventory(self, inventory: str, pattern: str):
        """Фильтр по переданному полю в инвентаризации узлов сети с помощью регулярного выражения"""
        if not self.zabbix_collected:
            self.collect_zabbix_info()
        return DevicesCollection(
            [d for d in self.collection if re.match(pattern, str(d.zabbix_info.inventory.__dict__[inventory]))]
        )

    def __getitem__(self, item):
        return self.collection[item]

    def __add__(self, other):
        if isinstance(other, Device):
            self.collection += [other]
        if isinstance(other, DevicesCollection):
            self.collection += other.collection
        return self.collection

    def __radd__(self, other):
        if isinstance(other, Device):
            self.collection = [other] + self.collection
        if isinstance(other, DevicesCollection):
            self.collection = other.collection + self.collection
        return self.collection

    def __iadd__(self, other):
        return self.__add__(other)

    def collect_interfaces(self, vlans, current_status=False):
        if current_status and not self.auth_groups:
            raise AuthException(f'Не указаны группы авторизации для коллекции!')

        with alive_bar(self.count, title='Собираем интерфейсы') as bar:
            with ThreadPoolExecutor() as ex:
                for d in self.collection:
                    ex.submit(d.collect_interfaces, vlans, current_status, bar)
        self.interfaces_collected = True
        return self

    def collect_zabbix_info(self):
        with ThreadPoolExecutor() as ex:
            for d in self.collection:
                ex.submit(d.collect_zabbix_info)
        self.zabbix_collected = True
        return self

    @property
    def available(self):
        return DevicesCollection([d for d in self.collection if d.zabbix_info.status])

    @property
    def unavailable(self):
        return DevicesCollection([d for d in self.collection if not d.zabbix_info.status])

    def sort_by(self, field: str):
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
        :return:
        """
        if not self.zabbix_collected and field != 'name':
            self.collect_zabbix_info()

        if field in ZabbixInventory.__dict__.keys():
            key_ = lambda d: d.zabbix_info.inventory.__dict__[field]
        else:
            key_ = lambda d: d.__dict__[field]
        return DevicesCollection(sorted(self.collection, key=key_))

    def ping_devs(self, unavailable=False):
        a, u = [], []

        def pd(dev):
            if dev.ping():
                a.append(dev)
            else:
                u.append(dev)

        with ThreadPoolExecutor() as executor:
            for d in self.collection:
                executor.submit(pd, d)

        if unavailable:
            return DevicesCollection(u)
        return DevicesCollection(a)


class Device:

    def __init__(self, name, zabbix_info=True):
        self.name: str = name
        self.ip: str = ''
        self._zabbix_info: ZabbixHostInfo = ZabbixHostInfo()
        self._location = None
        self._zabbix_info_collected = False  # Уже была собрана информация от Zabbix
        if zabbix_info:  # Собираем данные с Zabbix
            self.collect_zabbix_info()

        self.interfaces = Interfaces()
        self.protocol: str = 'telnet'
        self.snmp_community = ''
        self.auth_obj = None
        self.success_auth: dict = {}

    def collect_zabbix_info(self):
        with ZabbixAPI(server=Config.ZABBIX_URL) as zbx:
            zbx.login(Config.ZABBIX_USER, Config.ZABBIX_PASSWORD)
            zabbix_info = zbx.host.get(
                filter={'name': self.name},
                output=[
                        'hostid',
                        'host',
                        'name',
                        'status',
                        'description'
                    ],
                selectGroups=['groupid', 'name'],
                selectInterfaces=['ip'],
                selectInventory='extend'
            )
        if zabbix_info:
            # Форматируем вывод активировано/деактивировано для узла сети
            zabbix_info[0]['status'] = 1 if zabbix_info[0]['status'] == '0' else 0
            # Создаем уникальный кортеж ip адресов
            zabbix_info[0]['interfaces'] = tuple(sorted(list({i['ip'] for i in zabbix_info[0]['interfaces']})))

            # Инвентарные данные
            inventory = zabbix_info[0]['inventory'].values() if zabbix_info[0]['inventory'] else {}
            del zabbix_info[0]['inventory']

            # Группы
            groups = zabbix_info[0]['groups'] if zabbix_info[0]['groups'] else {}
            del zabbix_info[0]['groups']

            self._zabbix_info = ZabbixHostInfo(
                *zabbix_info[0].values(),
                ZabbixInventory(*inventory),
                tuple([ZabbixHostGroup(*g.values()) for g in groups])
            )
            self._zabbix_info_collected = True

            self.ip = [i for i in self.zabbix_info.ip if len(self.zabbix_info.ip) > 1 and i != '127.0.0.1' or len(self.zabbix_info.ip) == 1][0]
        else:
            self._zabbix_info = ZabbixHostInfo()

    def push_zabbix_inventory(self):
        """Обновляем инвентарные данные узла сети в Zabbix"""
        with ZabbixAPI(server=Config.ZABBIX_URL) as zbx:
            zbx.login(Config.ZABBIX_USER, Config.ZABBIX_PASSWORD)
            resp = zbx.host.update(
                hostid=self.zabbix_info.hostid,
                inventory={k: v for k, v in self.zabbix_info.inventory.__dict__.items() if v}  # Только заполненные поля
            )

    @property
    def zabbix_info(self) -> ZabbixHostInfo:
        return self._zabbix_info

    @classmethod
    def from_ip(cls, ip: str) -> DevicesCollection:
        with ZabbixAPI(server=Config.ZABBIX_URL) as zbx:
            zbx.login(Config.ZABBIX_USER, Config.ZABBIX_PASSWORD)
            hosts = zbx.host.get(filter={'ip': ip}, output=['name'])
        return DevicesCollection([Device(d['name']) for d in hosts])

    @classmethod
    def from_hostid(cls, hostid: str):
        with ZabbixAPI(server=Config.ZABBIX_URL) as zbx:
            zbx.login(Config.ZABBIX_USER, Config.ZABBIX_PASSWORD)
            host = zbx.host.get(hostids=hostid, output=['name'])
        if host:
            return Device(host[0]['name'])

    def collect_interfaces(self, vlans=True, current_status=False, auth_obj=None):
        """Собираем интерфейсы оборудования"""
        if not current_status:  # Смотрим из истории

            from net_tools.models import DevicesInfo

            device_data_history = DevicesInfo.objects.get(device_name=self.name)

            self.interfaces = Interfaces(json.loads(
                device_data_history.vlans if vlans else device_data_history.interfaces
            ))

        # Собираем интерфейсы в реальном времени с устройства
        elif self.protocol == 'snmp':

            # SNMP
            raw_interfaces = snmp.show_interfaces(device_ip=self.ip, community=self.snmp_community)
            self.interfaces = Interfaces([
                {'Interface': line[0], 'Status': 'admin down' if 'down' in line[1] else line[2], 'Description': line[3]}
                for line in raw_interfaces if snmp.physical_interface(line[0])
            ])

        else:

            # CMD
            if not auth_obj and not self.auth_obj:
                return 'Не указан профиль авторизации для данного оборудования'
            if not self.protocol:
                return 'Не указан протокол для подключения к оборудованию'
            with self.connect(self.protocol, auth_obj=auth_obj or self.auth_obj) as s:
                if isinstance(s, str) or s is None:
                    return s or 'None'

                if s.model:
                    self.zabbix_info.inventory.model = s.model

                if s.vendor:
                    self.zabbix_info.inventory.vendor = s.vendor

                # Получаем верные логин/пароль
                self.success_auth = s.auth

                if vlans:
                    # Если не получилось собрать vlan тогда собираем интерфейсы
                    self.interfaces = Interfaces(s.get_vlans() or s.get_interfaces())
                else:
                    self.interfaces = Interfaces(s.get_interfaces())

    def __str__(self):
        return f'Device(name="{self.name}", ip="{"; ".join(self._zabbix_info.ip)}")'

    def __repr__(self):
        return self.__str__()

    def ping(self) -> int:
        if not self.ip:
            self.collect_zabbix_info()
            if not self.ip:
                return -1
        flags = '-w 500 -n 1' if os.name == 'nt' else '-W 1 -c 1'
        if not subprocess.call(f'ping {flags} {self.ip}', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True):
            return 1
        else:
            return 0

    def address(self):
        """Выводит местоположение оборудования"""
        if not self._zabbix_info_collected:
            self.collect_zabbix_info()
        if self._zabbix_info.inventory.location:
            return self._zabbix_info.inventory.location
        if self._zabbix_info.inventory.location_lat and self._zabbix_info.inventory.location_lon and not self._location:
            l = Nominatim(user_agent='coordinateconverter').reverse(', '.join(self._zabbix_info.inventory.coordinates))
            if l:
                self._location = Location(**l.raw['address'])
        return self._location

    def connect(self, protocol=None, auth_obj=None):
        d: Any = DeviceFactory(self.ip, protocol=protocol or self.protocol, auth_obj=auth_obj or self.auth_obj)
        return d

