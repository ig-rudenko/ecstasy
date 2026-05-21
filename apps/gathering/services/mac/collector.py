import re
from datetime import timedelta
from itertools import islice

from django.conf import settings
from django.utils import timezone

from apps.gathering.models import MacAddress
from devicemanager.remote.exceptions import InvalidMethod
from devicemanager.vendors.base.types import MACTableType

from ..collectors import AbstractRealtimeCollector


class MacAddressTableGather(AbstractRealtimeCollector):
    """
    # Этот класс используется для сбора таблицы MAC-адресов с устройства
    """

    def collect(self) -> None:
        # Собираем таблицу MAC адресов с оборудования.
        table = self._get_mac_address_table()
        self._bulk_create(table)

    def _get_mac_address_table(self) -> MACTableType:
        """
        # Если в сеансе есть функция с именем get_mac_table, вернуть результат вызова этой функции. В противном
        случае вернуть пустой список

        :return: Список MAC-адресов на устройстве.
        """

        # Если сессия требует интерфейсов для работы
        if hasattr(self.session, "interfaces"):
            # Используется для MA5600T, где сбор интерфейсов происходит по snmp, а для получения таблицы MAC адресов
            # необходимо по очереди перебрать все интерфейсы
            self.session.interfaces = [(line.name, line.status, line.desc) for line in self.interfaces]
        try:
            if hasattr(self.session, "get_mac_table"):
                return self.session.get_mac_table() or []
        except InvalidMethod:
            pass
        return []

    def _bulk_create(self, table: MACTableType) -> int:
        """
        ## Список MAC адресов создается или обновляется в базе данных.
        """
        objects = (
            # Создание нового объекта MacAddress.
            MacAddress(
                address=self._format_mac(mac),
                vlan=vid,
                type=self._format_type(type_),
                device=self.device,
                port=port,
                desc=self._get_desc(port),
            )
            # Цикл for, который перебирает список MAC-адресов.
            for vid, mac, type_, port in table
            if self.normalize_interface(port)
        )

        batch_size = self._bulk_options.get("batch_size", 999)

        count = 0  # Это счетчик, который подсчитывает количество созданных объектов.

        # Цикл while, который будет выполняться до тех пор, пока список объектов не станет пустым.
        while objects:
            # Взять первые 999 объектов из списка объектов и присвоить их переменной пакету.
            batch = list(islice(objects, batch_size))
            count += len(batch)
            if not batch:
                break
            # Создание пакета объектов в базе данных.
            MacAddress.objects.bulk_create(objs=batch, **self._bulk_options)  # noqa

        return count

    def _get_desc(self, interface_name: str) -> str:
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
    def _format_mac(mac_address: str) -> str:
        """
        ## Удаляет все не шестнадцатеричные символы в MAC адресе и возвращает результат.

        :param mac_address: MAC-адрес для форматирования
        :return: очищенный mac_address.
        """
        return re.sub(r"\W", "", mac_address)

    @staticmethod
    def _format_type(mac_type: str) -> str:
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
    def _bulk_options(self) -> dict:
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
        database_engine = str(settings.DATABASES["default"]["ENGINE"]).rsplit(".", 1)[1]

        if database_engine in ["postgresql", "sqlite3"]:
            # В PostgreSQL и SQLite, в дополнение к update_fields,
            # необходимо предоставить список unique_fields, которые могут быть в конфликте.
            options["unique_fields"] = ["address", "port", "device"]

        return options
