import datetime
import re
from itertools import islice

from check.models import Devices
from .models import MacAddress
from devicemanager.vendors.base import InterfaceList
from devicemanager import exceptions


class GatherMacAddressTable:
    """
    Этот класс используется для сбора таблицы MAC-адресов с устройства
    """

    def __init__(self, from_: Devices):
        self.device: Devices = from_
        self.normalize_interface = None
        self.table: list = self.get_mac_address_table()
        self.interfaces: dict = {}
        if self.table:
            self.interfaces = self.format_interfaces(self.get_device_interfaces())

    def get_mac_address_table(self) -> list:
        """
        Если сеанс оборудования имеет функцию normalize_interface_name,
        установит атрибут normalize_interface для этой функции.
        Если в сеансе есть функция get_mac_table, вернуть результат вызова этой функции.
        В противном случае вернуть пустой список.
        :return: Список MAC адресов на оборудовании.
        """
        try:
            with self.device.connect() as session:
                if hasattr(session, "normalize_interface_name"):
                    self.normalize_interface = session.normalize_interface_name
                if hasattr(session, "get_mac_table"):
                    return session.get_mac_table()
        except exceptions.DeviceException:
            pass
        return []

    def get_device_interfaces(self) -> InterfaceList:
        """
        ## Эта функция возвращает список интерфейсов на устройстве
        :return: Список интерфейсов
        """
        try:
            with self.device.connect() as session:
                return session.get_interfaces()
        except exceptions.DeviceException:
            pass
        return []

    def format_interfaces(self, old_interfaces) -> dict:
        """
        ## Принимает список интерфейсов, и формирует словарь из интерфейсов и их описаний

        :param old_interfaces: Это список интерфейсов, которые вы хотите отформатировать
        :return: Словарь интерфейсов и соответствующих им описаний.
        """
        interfaces = {}

        # Перебираем список интерфейсов
        for line in old_interfaces:
            # Проверка наличия на устройстве функции normalize_interface.
            if self.normalize_interface:
                # Если это так, он будет использовать эту функцию для нормализации имени интерфейса.
                normal_interface = self.normalize_interface(line[0])
            else:
                # Если это не так, он просто будет использовать имя интерфейса как есть.
                normal_interface = line[0]

            # Проверка, не является ли имя интерфейса пустым.
            if normal_interface:
                # Добавление имени интерфейса в качестве ключа и описания в качестве значения в словарь.
                interfaces[normal_interface] = line[-1]

        return interfaces

    def get_desc(self, interface_name: str) -> str:
        """
        ## Эта функция возвращает описание интерфейса

        :param interface_name: Имя интерфейса для получения описания
        :return: Описание интерфейса.
        """
        normal_interface = self.normalize_interface(interface_name)
        if normal_interface:
            return self.interfaces.get(normal_interface, "")
        return ""

    @staticmethod
    def format_mac(mac_address: str) -> str:
        """
        ## Удаляет все небуквенно-цифровые символы в MAC адресе и возвращает результат.

        :param mac_address: MAC-адрес для форматирования
        :return: очищенный mac_address.
        """
        return re.sub(r"\W", "", mac_address)

    @staticmethod
    def format_type(mac_type: str) -> str:
        """
        :param mac_type: Тип MAC-адреса. Это может быть динамическим, статическим или защищенным
        :return: Буква для mac_type.
        """
        if mac_type.lower() == "dynamic":
            return "D"
        if mac_type.lower() == "static":
            return "S"
        if mac_type.lower() == "secured":
            return "E"
        return ""

    def clear_old_records(self, timedelta=datetime.timedelta(hours=48)):
        """
        ## Удаляет из базы данных все записи MAC адресов для оборудования старше 48 часов.

        :param timedelta: Количество времени для хранения записей
        """
        MacAddress.objects.filter(
            device_id=self.device.id,
            datetime__lt=datetime.datetime.now() - timedelta,
        ).delete()

    def bulk_create(self, batch_size=999) -> int:
        """
        ## Берет список MAC адресов и создает их в базе данных партиями по 999 штук.

        :param batch_size: Количество объектов, которые необходимо создать в каждом пакете, defaults to 999 (optional)
        """
        objects = (
            MacAddress(
                address=self.format_mac(mac),
                vlan=vid,
                type=self.format_type(type_),
                device=self.device,
                port=port,
                desc=self.get_desc(port),
            )
            for vid, mac, type_, port in self.table
            if self.normalize_interface(port)
        )
        count = 0
        while objects:
            batch = list(islice(objects, batch_size))
            count += len(batch)
            if not batch:
                break
            MacAddress.objects.bulk_create(
                objs=batch,
                batch_size=batch_size,
                update_conflicts=True,
                update_fields=["vlan", "type", "datetime", "desc"],
                unique_fields=["address", "port", "device"],
            )
        return count
