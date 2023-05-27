import re
from itertools import islice
from datetime import timedelta

import orjson
from django.utils import timezone
from django.conf import settings

from check.models import Devices
from net_tools.models import DevicesInfo
from devicemanager.device import (
    DeviceManager,
    ZabbixAPIConfig as DeviceZabbixConfig,
    Interfaces,
)
from devicemanager.vendors.base import T_MACTable
from app_settings.models import ZabbixConfig
from devicemanager import exceptions
from ..models import MacAddress


class MacAddressTableGather:
    """
    # Этот класс используется для сбора таблицы MAC-адресов с устройства
    """

    def __init__(self, from_: Devices):
        if not DeviceZabbixConfig.ZABBIX_URL:
            DeviceZabbixConfig.set(ZabbixConfig.load())

        self.device: Devices = from_

        # Установка атрибута normalize_interface для лямбда-функции, которая возвращает переданное ей значение.
        self.normalize_interface = lambda x: x
        self.table: T_MACTable = []
        self.interfaces: Interfaces = Interfaces()
        self.interfaces_desc: dict = {}

        try:
            # Создание сеанса с устройством. С закрытием сессии после выхода из `with`.
            with self.device.connect(make_session_global=False) as session:
                # Если в сеансе есть функция с именем normalize_interface_name,
                # установите атрибут normalize_interface для этой функции.
                # Нормализация имени интерфейса необходима из-за разных вариантов записи одного и того же порта.
                # Например - `1/1` и `1`, `26(C)` и `26(F)`.
                if hasattr(session, "normalize_interface_name"):
                    self.normalize_interface = session.normalize_interface_name

                # Получение интерфейсов с устройства.
                self.interfaces = self.get_interfaces()

                # Создание словаря интерфейсов и их описаний.
                self.interfaces_desc = self.format_interfaces(self.interfaces)

                # Собираем таблицу MAC адресов с оборудования.
                self.table = self.get_mac_address_table(session)

            # Сохранение интерфейсов в базу данных.
            self.save_interfaces()

        except exceptions.DeviceException:
            pass

    def get_mac_address_table(self, session) -> T_MACTable:
        """
        # Если в сеансе есть функция с именем get_mac_table, вернуть результат вызова этой функции. В противном
        случае вернуть пустой список

        :param session: Объект сеанса, который используется для подключения к устройству
        :return: Список MAC-адресов на устройстве.
        """

        # Если сессия требует интерфейсов для работы
        if hasattr(session, "interfaces"):
            # Используется для MA5600T, где сбор интерфейсов происходит по snmp, а для получения таблицы MAC адресов
            # необходимо по очереди перебрать все интерфейсы
            session.interfaces = [(line.name, line.status, line.desc) for line in self.interfaces]
        if hasattr(session, "get_mac_table"):
            return session.get_mac_table() or []
        return []

    def get_interfaces(self) -> Interfaces:
        device_manager = DeviceManager.from_model(self.device)
        # Получение интерфейсов с устройства.
        device_manager.collect_interfaces(
            vlans=False, current_status=True, make_session_global=False
        )
        return device_manager.interfaces or Interfaces()

    def format_interfaces(self, old_interfaces: Interfaces) -> dict:
        """
        ## Принимает список интерфейсов, и формирует словарь из интерфейсов и их описаний

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

    def save_interfaces(self) -> None:
        """
        ## Он берет данные из переменной «interfaces», которая представляет собой список интерфейсов,
         и сохраняет их в базу данных.
        """
        if not self.interfaces:
            return

        interfaces_to_save = [
            {
                "Interface": line.name,
                "Status": line.status,
                "Description": line.desc,
            }
            for line in self.interfaces
        ]

        try:
            device_history = DevicesInfo.objects.get(dev_id=self.device.id)
        except DevicesInfo.DoesNotExist:
            device_history = DevicesInfo.objects.create(dev=self.device)

        device_history.interfaces = orjson.dumps(interfaces_to_save).decode()
        device_history.interfaces_date = timezone.now()
        device_history.save(update_fields=["interfaces", "interfaces_date"])

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

    def clear_old_records(self, timedelta_=timedelta(hours=48)) -> None:
        """
        ## Удаляет из базы данных все записи MAC адресов для оборудования старше 48 часов.

        :param timedelta_: Количество времени для хранения записей
        """
        MacAddress.objects.filter(
            device_id=self.device.id,
            datetime__lt=timezone.now() - timedelta_,
        ).delete()

    @property
    def bulk_options(self) -> dict:
        """
        # Эта функция возвращает словарь опций для bulk_create в зависимости от указанной в settings.py БД.
        """

        options = {
            # В базах данных (все, кроме Oracle и SQLite < 3.24),
            # установка параметра update_conflicts в значение `True`
            # указывает базе данных обновить update_fields, когда вставка строки не удалась из-за конфликтов.
            "update_conflicts": True,
            "update_fields": ["vlan", "type", "datetime", "desc"],
            # Параметр определяет, сколько объектов создается в одном запросе.
            "batch_size": 999,
        }

        # Получение имени ядра базы данных из файла settings.py.
        database_engine = settings.DATABASES["default"]["ENGINE"].rsplit(".", 1)[1]

        if database_engine in ["postgresql", "sqlite3"]:
            # В PostgreSQL и SQLite, в дополнение к update_fields,
            # необходимо предоставить список unique_fields, которые могут быть в конфликте.
            options["unique_fields"] = ["address", "port", "device"]

        return options

    def bulk_create(self) -> int:
        """
        ## Список MAC адресов создается или обновляется в базе данных.
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

        batch_size = self.bulk_options.get("batch_size", 999)

        count = 0  # Это счетчик, который подсчитывает количество созданных объектов.

        # Цикл while, который будет выполняться до тех пор, пока список объектов не станет пустым.
        while objects:
            # Взять первые 999 объектов из списка объектов и присвоить их переменной пакету.
            batch = list(islice(objects, batch_size))
            count += len(batch)
            if not batch:
                break
            # Создание пакета объектов в базе данных.
            MacAddress.objects.bulk_create(objs=batch, **self.bulk_options)

        return count
