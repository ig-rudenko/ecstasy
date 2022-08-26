from dataclasses import dataclass, field
from typing import Tuple
import tabulate


@dataclass
class ZabbixInventory:
    type: str = ''
    type_full: str = ''
    name: str = ''
    alias: str = ''
    os: str = ''
    os_full: str = ''
    os_short: str = ''
    serialno_a: str = ''
    serialno_b: str = ''
    tag: str = ''
    asset_tag: str = ''
    macaddress_a: str = ''
    macaddress_b: str = ''
    hardware: str = ''
    hardware_full: str = ''
    software: str = ''
    software_full: str = ''
    software_app_a: str = ''
    software_app_b: str = ''
    software_app_c: str = ''
    software_app_d: str = ''
    software_app_e: str = ''
    contact: str = ''
    location: str = ''
    location_lat: str = ''
    location_lon: str = ''
    notes: str = ''
    chassis: str = ''
    model: str = ''
    hw_arch: str = ''
    vendor: str = ''
    contract_number: str = ''
    installer_name: str = ''
    deployment_status: str = ''
    url_a: str = ''
    url_b: str = ''
    url_c: str = ''
    host_networks: str = ''
    host_netmask: str = ''
    host_router: str = ''
    oob_ip: str = ''
    oob_netmask: str = ''
    oob_router: str = ''
    date_hw_purchase: str = ''
    date_hw_install: str = ''
    date_hw_expiry: str = ''
    date_hw_decomm: str = ''
    site_address_a: str = ''
    site_address_b: str = ''
    site_address_c: str = ''
    site_city: str = ''
    site_state: str = ''
    site_country: str = ''
    site_zip: str = ''
    site_rack: str = ''
    site_notes: str = ''
    poc_1_name: str = ''
    poc_1_email: str = ''
    poc_1_phone_a: str = ''
    poc_1_phone_b: str = ''
    poc_1_cell: str = ''
    poc_1_screen: str = ''
    poc_1_notes: str = ''
    poc_2_name: str = ''
    poc_2_email: str = ''
    poc_2_phone_a: str = ''
    poc_2_phone_b: str = ''
    poc_2_cell: str = ''
    poc_2_screen: str = ''
    poc_2_notes: str = ''

    @property
    def coordinates(self, reverse=False):
        if reverse:
            return self.location_lon, self.location_lat
        else:
            return self.location_lat, self.location_lon

    def print(self):
        """Выводит в терминал данные инвентаризации, только те, что имеются"""
        print(tabulate.tabulate([[i, self.__dict__[i]] for i in self.__dict__ if self.__dict__[i]]))

    @property
    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if v}


@dataclass
class ZabbixHostGroup:
    groupid: str = ''
    name: str = ''


@dataclass
class ZabbixHostInfo:
    hostid: str = ''
    host: str = ''
    name: str = ''
    status: int = ''
    description: str = ''
    ip: tuple = tuple()
    inventory: ZabbixInventory = ZabbixInventory()
    hostgroups: Tuple[ZabbixHostGroup] = tuple()

    @property
    def host_group_names(self):
        return [g.name for g in self.hostgroups]

    def print(self):
        """Выводит в терминал данные, кроме данных инвентаризации"""
        res = []
        for key in self.__dict__:
            if key != 'inventory':
                if key == 'hostgroups':
                    res.append([key, ', '.join(self.host_group_names)])
                elif key == 'ip':
                    res.append([key, ', '.join(self.ip)])
                else:
                    res.append([key, self.__dict__[key]])

        print(tabulate.tabulate(res))


@dataclass
class Interface:
    name: str = ''
    status: str = ''
    desc: str = ''
    vlan: list = field(default_factory=[])


@dataclass
class Location:
    state: str
    city: str
    district: str
    street: str
    house_number: str

    def __init__(self, **kwargs):
        self.state = kwargs.get('state') or ''
        self.city = kwargs.get('town') or kwargs.get('city') or ''
        self.district = kwargs.get('city_district') or kwargs.get('state_district') or ''
        self.street = ' '.join([kwargs.get('allotments') or '', kwargs.get('road') or '']).strip()
        print(f'"{self.street}"')
        self.house_number = kwargs.get('house_number') or ''

    def __str__(self):
        return ', '.join([r for r in [self.city, self.street, self.house_number] if r])
