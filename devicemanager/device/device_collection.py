import re
from concurrent.futures import ThreadPoolExecutor

from alive_progress import alive_bar
from requests import RequestException

from ..exceptions import AuthException
from ..zabbix_info_dataclasses import ZabbixInventory
from .device_manager import DeviceManager
from .zabbix_api import zabbix_api


class DevicesCollection:
    """Создает коллекцию из узлов сети, для комплексной работы с ними"""

    def __init__(self, devs: list | tuple, intf_coll=False, zbx_coll=False):
        self.interfaces_collected = intf_coll  # Были собраны интерфейсы
        self.zabbix_collected = zbx_coll  # Были собраны из Zabbix данные
        self.auth_groups: list = []

        # Если верно передан параметр
        if isinstance(devs, (list, tuple)):
            if all(isinstance(d, DeviceManager) for d in devs):
                self.collection: list[DeviceManager] = list(devs)
            elif all(isinstance(d, str) for d in devs):
                self.collection = [DeviceManager(d) for d in devs]
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
    def from_ip(cls, ip: str) -> "DevicesCollection":
        """
        Создаем коллекцию оборудований по IP адресу
        Коллекция, потому что по данному IP могут быть несколько записей в Zabbix
        """
        try:
            with zabbix_api.connect() as zbx:
                hosts = zbx.host.get(filter={"ip": ip}, output=["name"])
        except RequestException:
            return DevicesCollection([])
        return DevicesCollection([DeviceManager(d["name"]) for d in hosts])

    @classmethod
    def from_zabbix_groups(cls, groups_name: str | list, zabbix_info: bool) -> "DevicesCollection":
        """
        Создаем коллекцию из групп узлов сети Zabbix

        :param groups_name: Имя группы или список имен групп Zabbix
        :param zabbix_info: Собрать информацию оборудования из Zabbix в момент создания коллекции?
        """
        try:
            with zabbix_api.connect() as zbx:
                groups = zbx.hostgroup.get(filter={"name": groups_name}, output=["groupid"])
                if groups:
                    hosts = zbx.host.get(
                        groupids=[g["groupid"] for g in groups],
                        output=["name"],
                        sortfield=["name"],
                    )
                else:
                    return DevicesCollection([])
        except RequestException:
            return DevicesCollection([])

        with alive_bar(len(hosts), title="Создаем коллекцию") as bar:
            devs = []
            for host in hosts:
                bar.text = f"-> Собираем данные с {host['name']}"
                devs.append(DeviceManager(host["name"], zabbix_info=zabbix_info))
                bar()
        return DevicesCollection(devs)

    @classmethod
    def from_zabbix_ips(cls, ips: list[str], zabbix_info: bool) -> "DevicesCollection":
        """
        Создаем коллекцию из переданных IP адресов

        :param ips: IP адрес или список IP адресов
        :param zabbix_info: Собрать информацию оборудования из Zabbix в момент создания коллекции?
        """
        try:
            with zabbix_api.connect() as zbx:
                hosts = zbx.host.get(filter={"ip": ips}, output=["name"], sortfield=["name"])
        except RequestException:
            return DevicesCollection([])

        if hosts:
            with alive_bar(len(hosts), title="Создаем коллекцию") as bar:
                devs = []
                for h in hosts:
                    bar.text = f"-> Собираем данные с {h['name']}"
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

        with alive_bar(self.count, title="Собираем интерфейсы") as bar, ThreadPoolExecutor() as ex:
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
