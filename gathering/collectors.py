import datetime
import re
from itertools import islice

from check.models import Devices
from .models import MacAddress
from devicemanager.device import (
    Device as ZabbixDevice,
    Config as DeviceZabbixConfig,
    Interfaces,
)
from app_settings.models import ZabbixConfig
from devicemanager import exceptions


class GatherMacAddressTable:
    """
    # Этот класс используется для сбора таблицы MAC-адресов с устройства
    """

    def __init__(self, from_: Devices):

        if not DeviceZabbixConfig.ZABBIX_URL:
            DeviceZabbixConfig.set(ZabbixConfig.load())

        self.device: Devices = from_

        # Установка атрибута normalize_interface для лямбда-функции, которая возвращает переданное ей значение.
        self.normalize_interface = lambda x: x
        self.table: list = []
        self.interfaces: Interfaces = Interfaces()
        self.interfaces_desc: dict = {}

        try:
            # Создание сеанса с устройством. С закрытием сессии после выхода из `with`.
            with self.device.connect(make_session_global=False) as session:
                # Создание словаря интерфейсов и их описаний.
                self.interfaces = self.get_interfaces()
                self.interfaces_desc = self.format_interfaces(self.interfaces)
                self.table: list = self.get_mac_address_table(session)

        except exceptions.DeviceException:
            pass

    def get_mac_address_table(self, session) -> list:
        """
        ## Если в сеансе есть функция с именем normalize_interface_name, установите атрибут normalize_interface для этой
        функции.
        Если в сеансе есть функция с именем get_mac_table, вернуть результат вызова этой функции. В противном
        случае вернуть пустой список

        :param session: Объект сеанса, который используется для подключения к устройству
        :return: Список MAC-адресов на устройстве.
        """

        # Если сессия требует интерфейсов для работы
        if hasattr(session, "interfaces"):
            session.interfaces = [
                (line.name, line.status, line.desc)
                for line in self.interfaces
            ]

        if hasattr(session, "normalize_interface_name"):
            self.normalize_interface = session.normalize_interface_name
        if hasattr(session, "get_mac_table"):
            return session.get_mac_table() or []
        return []

    def get_interfaces(self) -> Interfaces:
        device_manager = ZabbixDevice.from_model(self.device)
        # Получение интерфейсов с устройства.
        device_manager.collect_interfaces(
            vlans=False, current_status=True, make_session_global=False
        )
        print(device_manager.interfaces)
        return device_manager.interfaces

    def format_interfaces(self, old_interfaces: Interfaces) -> dict:
        """
        ## Принимает список интерфейсов, и формирует словарь из интерфейсов и их описаний

        :param old_interfaces: Это список интерфейсов, которые вы хотите отформатировать
        :return: Словарь интерфейсов и соответствующих им описаний.
        """
        interfaces = {}

        # Перебираем список интерфейсов
        for line in old_interfaces:
            normal_interface = self.normalize_interface(line.name)

            # Проверка, не является ли имя интерфейса пустым.
            if normal_interface:
                # Добавление имени интерфейса в качестве ключа и описания в качестве значения в словарь.
                interfaces[normal_interface] = line.desc

        return interfaces

    def get_desc(self, interface_name: str) -> str:
        """
        ## Эта функция возвращает описание интерфейса

        :param interface_name: Имя интерфейса для получения описания
        :return: Описание интерфейса.
        """
        normal_interface = self.normalize_interface(interface_name)
        if normal_interface:
            return self.interfaces_desc.get(normal_interface, "")
        return ""

    @staticmethod
    def format_mac(mac_address: str) -> str:
        """
        ## Удаляет все не шестнадцатеричные символы в MAC адресе и возвращает результат.

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
        if mac_type.lower() == "security":
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
            # Создание нового объекта MacAddress.
            MacAddress(
                address=self.format_mac(mac),
                vlan=vid,
                type=self.format_type(type_),
                device=self.device,
                port=port,
                desc=self.get_desc(port),
            )
            # Цикл for, который перебирает список MAC-адресов.
            for vid, mac, type_, port in self.table
            if self.normalize_interface(port)
        )

        count = 0  # Это счетчик, который подсчитывает количество созданных объектов.
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
