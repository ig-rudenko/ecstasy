import hashlib
import re
import datetime
import json
import filecmp
import pathlib

from itertools import islice
from typing import Union

from django.conf import settings

from check.models import Devices
from net_tools.models import DevicesInfo
from .config_storage import ConfigStorage
from .models import MacAddress
from devicemanager.device import (
    Device as ZabbixDevice,
    Config as DeviceZabbixConfig,
    Interfaces,
)
from devicemanager.vendors.base import T_MACTable
from app_settings.models import ZabbixConfig
from devicemanager import exceptions


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
            session.interfaces = [
                (line.name, line.status, line.desc) for line in self.interfaces
            ]
        if hasattr(session, "get_mac_table"):
            return session.get_mac_table() or []
        return []

    def get_interfaces(self) -> Interfaces:
        device_manager = ZabbixDevice.from_model(self.device)
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

        device_history.interfaces = json.dumps(interfaces_to_save)
        device_history.interfaces_date = datetime.datetime.now()
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

    def clear_old_records(self, timedelta=datetime.timedelta(hours=48)) -> None:
        """
        ## Удаляет из базы данных все записи MAC адресов для оборудования старше 48 часов.

        :param timedelta: Количество времени для хранения записей
        """
        MacAddress.objects.filter(
            device_id=self.device.id,
            datetime__lt=datetime.datetime.now() - timedelta,
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


class ConfigurationGather:
    def __init__(self, storage: ConfigStorage):

        self.storage = storage
        self.files = self.storage.files_list()

        self.last_config_file = self.files[0] if self.files else None
        self.re_pattern_space = re.compile(r"\s")

    def delete_outdated_configs(self):
        """
        ##  Удаляет файлы, если их больше 10
        """
        # Удаление файлов в каталоге, кроме 10 самых последних.
        for file in self.files[:-10]:
            self.storage.delete(file.name)

    def save_by_content(self, current_config: Union[str, bytes]) -> bool:
        """
        ## Берет текущую конфигурацию, удаляет все пробелы, хеширует ее и сравниваем с последней конфигурацией.
        Если они совпадают, то возвращает False.
        Если они разные, то сохраняет текущую конфигурацию в хранилище и возвращает True.

        :param current_config: [str, bytes] - текущая конфигурация устройства
        :return: Правда или ложь.
        """

        # Сохраняем в исходном виде конфигурацию
        unformatted_config = current_config

        read_mode = "rb"
        last_config: bytes = b""

        if isinstance(current_config, str):
            read_mode = "r"
            current_config: bytes = self.re_pattern_space.sub(
                "", current_config
            ).encode()

        if self.last_config_file:
            try:
                # Открытие файла в режиме чтения.
                with self.storage.open(
                    self.last_config_file.name, mode=read_mode
                ) as file:
                    # Чтение последнего файла конфигурации.
                    last_config = file.read()
            # Резервный вариант, когда файл не в формате ascii.
            except UnicodeError:
                last_config: str = ""

        if isinstance(last_config, str):
            last_config: bytes = self.re_pattern_space.sub("", last_config).encode()

        # Берем текущую конфигурацию и удаляем все пробелы, а затем хешируем ее.
        current_config_hash = hashlib.sha3_224(current_config).hexdigest()

        # Берем прошлую конфигурацию и удаляем все пробелы, а затем хешируем ее.
        last_config_hash = hashlib.sha3_224(last_config).hexdigest()

        # Проверяем, совпадает ли last_config с current_config.
        if last_config_hash == current_config_hash:
            return False

        # Создание нового имени файла для нового файла конфигурации.
        new_file_name = "config_file_" + current_config_hash[:15] + ".txt"

        self.storage.add(new_file_name, file_content=unformatted_config)

        return True

    def save_config(self, new_config) -> bool:
        """
        Сохраняем конфигурацию в зависимости от типа (str или pathlib.Path)
        """

        # Если файл представлен в виде строки
        if isinstance(new_config, str):
            return self.save_by_content(new_config)

        # Если файл был скачан, то используем его путь
        if isinstance(new_config, pathlib.Path) and new_config.is_file():

            # Записываем содержимое скачанного файла
            with new_config.open("rb") as f:
                file_data = f.read()
            # Удаляем его, так как далее будет сохранен новый файл в хранилище
            new_config.unlink()

            # Обрабатываем содержимое файла
            return self.save_by_content(file_data)

        return False

    def collect_config_file(self) -> bool:
        """
        Подключаемся к оборудованию и вызываем метод для получения текущей конфигурации
        """

        with self.storage.device.connect(make_session_global=False) as session:
            if hasattr(session, "get_current_configuration"):
                current_config = session.get_current_configuration(
                    folder_path=self.storage._storage
                )
            else:
                return False

        return self.save_config(current_config)