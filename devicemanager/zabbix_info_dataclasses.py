from dataclasses import dataclass, field

import tabulate


@dataclass
class ZabbixInventory:
    # pylint: disable=too-many-instance-attributes
    type: str = ""
    type_full: str = ""
    name: str = ""
    alias: str = ""
    os: str = ""
    os_full: str = ""
    os_short: str = ""
    serialno_a: str = ""
    serialno_b: str = ""
    tag: str = ""
    asset_tag: str = ""
    macaddress_a: str = ""
    macaddress_b: str = ""
    hardware: str = ""
    hardware_full: str = ""
    software: str = ""
    software_full: str = ""
    software_app_a: str = ""
    software_app_b: str = ""
    software_app_c: str = ""
    software_app_d: str = ""
    software_app_e: str = ""
    contact: str = ""
    location: str = ""
    location_lat: str = ""
    location_lon: str = ""
    notes: str = ""
    chassis: str = ""
    model: str = ""
    hw_arch: str = ""
    vendor: str = ""
    contract_number: str = ""
    installer_name: str = ""
    deployment_status: str = ""
    url_a: str = ""
    url_b: str = ""
    url_c: str = ""
    host_networks: str = ""
    host_netmask: str = ""
    host_router: str = ""
    oob_ip: str = ""
    oob_netmask: str = ""
    oob_router: str = ""
    date_hw_purchase: str = ""
    date_hw_install: str = ""
    date_hw_expiry: str = ""
    date_hw_decomm: str = ""
    site_address_a: str = ""
    site_address_b: str = ""
    site_address_c: str = ""
    site_city: str = ""
    site_state: str = ""
    site_country: str = ""
    site_zip: str = ""
    site_rack: str = ""
    site_notes: str = ""
    poc_1_name: str = ""
    poc_1_email: str = ""
    poc_1_phone_a: str = ""
    poc_1_phone_b: str = ""
    poc_1_cell: str = ""
    poc_1_screen: str = ""
    poc_1_notes: str = ""
    poc_2_name: str = ""
    poc_2_email: str = ""
    poc_2_phone_a: str = ""
    poc_2_phone_b: str = ""
    poc_2_cell: str = ""
    poc_2_screen: str = ""
    poc_2_notes: str = ""

    def coordinates(self, reverse=False) -> tuple:
        if not self.location_lat or not self.location_lon:
            return tuple()

        if reverse:
            return self.location_lon, self.location_lat

        return self.location_lat, self.location_lon

    def print(self):
        """Выводит в терминал данные инвентаризации, только те, что имеются"""
        print(tabulate.tabulate([[k, v] for k, v in self.__dict__.items() if v]))

    @property
    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if v}


@dataclass
class ZabbixHostGroup:
    groupid: str = ""
    name: str = ""


@dataclass
class ZabbixHostInfo:
    # pylint: disable=too-many-instance-attributes
    hostid: str = ""
    host: str = ""
    name: str = ""
    status: int = 0
    description: str = ""
    ip: tuple = field(default_factory=tuple)
    inventory: ZabbixInventory = field(default_factory=ZabbixInventory)
    hostgroups: list[ZabbixHostGroup] = field(default_factory=list)

    @property
    def host_group_names(self):
        return [g.name for g in self.hostgroups]

    def print(self):
        """Выводит в терминал данные, кроме данных инвентаризации"""
        res = []
        for key, value in self.__dict__.items():
            if key != "inventory":
                if key == "hostgroups":
                    res.append([key, ", ".join(self.host_group_names)])
                elif key == "ip":
                    res.append([key, ", ".join(self.ip)])
                else:
                    res.append([key, value])

        print(tabulate.tabulate(res))
