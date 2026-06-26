import io
import re
import string
from abc import ABC, abstractmethod
from functools import wraps
from pathlib import Path
from threading import RLock
from typing import Literal

import pexpect

from devicemanager.device_connector.types import RemoteCommand

from .helpers import remove_ansi_escape_codes
from .types import (
    ArpInfoResult,
    CableDiagResult,
    DeviceAuthDict,
    InterfaceListType,
    InterfaceVLANListType,
    MACListType,
    MACTableType,
    PortInfoType,
    SystemInfo,
    VlanTableType,
)


class AbstractDevice(ABC):
    """
    # Абстрактный класс для устройств.
    Содержит обязательные методы для выполнения удаленных команд.
    """

    @abstractmethod
    def get_interfaces(self) -> InterfaceListType:
        """
        Интерфейсы на оборудовании

        :return: ```[ ('name', 'status', 'desc'), ... ]```
        """

    @abstractmethod
    def get_vlans(self) -> InterfaceVLANListType:
        """
        Интерфейсы и VLAN на оборудовании

        :return: ```[ ('name', 'status', 'desc', ['vlans', ...]), ... ]```
        """

    @abstractmethod
    def get_mac(self, port: str) -> MACListType:
        """
        Поиск маков на порту

        :return: ```[ ('vid', 'mac'), ... ]```
        """

    @abstractmethod
    def get_mac_table(self) -> MACTableType:
        """Возвращает всю таблицу MAC адресов оборудования"""

    @abstractmethod
    def get_vlan_table(self) -> VlanTableType:
        """Возвращает сконфигурированные активные на оборудовании VLAN и на каких интерфейсах имеются"""

    @abstractmethod
    def reload_port(self, port: str, save_config=True) -> str:
        """Перезагрузка порта"""

    @abstractmethod
    def set_port(self, port: str, status: Literal["up", "down"], save_config=True) -> str:
        """Изменение состояния порта"""

    @abstractmethod
    def save_config(self) -> str:
        """Сохраняем конфигурацию оборудования"""

    @abstractmethod
    def set_description(self, port: str, desc: str) -> dict:
        """Изменяем описание порта"""

    @abstractmethod
    def get_port_info(self, port: str) -> PortInfoType:
        """Информация о порте"""

    @abstractmethod
    def get_port_type(self, port: str) -> str:
        """Тип порта"""

    @abstractmethod
    def get_port_config(self, port: str) -> str:
        """Конфигурация порта"""

    @abstractmethod
    def get_port_errors(self, port: str) -> str:
        """Ошибки на порту"""

    @abstractmethod
    def get_device_info(self) -> dict:
        """Словарь с информацией о нагрузке CPU, RAM, Flash, температуры и др."""

    @abstractmethod
    def get_system_info(self):
        """Возвращает характеристики оборудования: MAC, Serial Number, Vendor, Model"""


class AbstractSearchDevice(ABC):
    @abstractmethod
    def search_ip(self, ip_address: str) -> list[ArpInfoResult]:
        """Ищем IP адрес в таблице ARP оборудования"""

    @abstractmethod
    def search_mac(self, mac_address: str) -> list[ArpInfoResult]:
        """Ищем MAC адрес в таблице ARP оборудования"""


class AbstractConfigDevice(ABC):
    @abstractmethod
    def get_current_configuration(self) -> io.BytesIO | Path:
        pass


class AbstractPOEDevice(ABC):
    @abstractmethod
    def set_poe_out(self, port: str, status: str):
        pass


class AbstractCableTestDevice(ABC):
    @abstractmethod
    def virtual_cable_test(self, port: str) -> CableDiagResult:
        pass


class AbstractDSLProfileDevice(ABC):
    @abstractmethod
    def change_profile(self, port: str, profile_index: int):
        pass


class AbstractUserSessionsDevice(ABC):
    @abstractmethod
    def get_access_user_data(self, mac: str) -> str:
        pass

    @abstractmethod
    def cut_access_user_session(self, mac: str) -> str:
        pass


class BaseDevice(AbstractDevice, ABC):
    """
    # Базовый класс для устройств, все типы устройств должны наследоваться от него.
    """

    # Регулярное выражение, которое указывает на приглашение для ввода следующей команды
    prompt: str

    # Регулярное выражение, которое указывает на ожидание ввода клавиши, для последующего отображения информации
    space_prompt: str | None

    mac_format = ""  # Регулярное выражение, которое определяет отображение МАС адреса
    SAVED_OK = "Saved OK"  # Конфигурация была сохранена
    SAVED_ERR = "Saved Error"  # Ошибка при сохранении конфигурации
    vendor: str
    supported_models: re.Pattern[str] | None = None  # Регулярное выражение поддерживаемых моделей, либо все

    def __init__(
        self,
        session,
        ip: str,
        auth: DeviceAuthDict,
        model: str = "",
        snmp_community: str = "",
        snmp_port: int = 161,
    ):
        self.session: pexpect.spawn = session
        self.ip = ip
        self.model: str = model
        self.auth: DeviceAuthDict = auth
        self.mac: str = ""
        self.serialno: str = ""
        self.os: str = ""
        self.os_version: str = ""
        self.snmp_community = snmp_community
        self.snmp_port = snmp_port
        self.connection_protocol = ""
        self._session_lock = RLock()

    def acquire_session(self, blocking: bool = True) -> bool:
        """Зарезервировать терминальную сессию для текущего потока."""

        return self._get_session_lock().acquire(blocking=blocking)

    def release_session(self) -> None:
        """Освободить терминальную сессию, зарезервированную текущим потоком."""

        self._get_session_lock().release()

    def _get_session_lock(self) -> RLock:
        """Вернуть блокировку, создавая её для объектов без вызова конструктора."""

        session_lock = getattr(self, "_session_lock", None)
        if session_lock is None:
            session_lock = self._session_lock = RLock()
        return session_lock

    def __getstate__(self) -> dict:
        """Вернуть состояние без некопируемого объекта блокировки."""

        state = self.__dict__.copy()
        state.pop("_session_lock", None)
        return state

    def __setstate__(self, state: dict) -> None:
        """Восстановить состояние и создать отдельную блокировку сессии."""

        self.__dict__.update(state)
        self._session_lock = RLock()

    def get_system_info(self) -> SystemInfo:
        return {
            "mac": self.mac,
            "vendor": self.vendor,
            "model": self.model,
            "serialno": self.serialno,
            "os_version": self.os_version,
        }

    @staticmethod
    def normalize_interface_name(intf: str) -> str:
        """
        Возвращает отформатированное название интерфейса без подключения к оборудованию.
        """
        return intf

    def normalize_interface_name_realtime(self, intf: str) -> str:
        """
        Функция для форматирования интерфейса в реальном времени.
        Требуется подключение к оборудованию.
        """
        return intf

    @staticmethod
    def clear_description(desc: str) -> str:
        """
        Очищаем описание порта от лишних символов

        Также переводит русские символы в английские. Заменяет пробелы на "_".
        Удаляет другие пробельные символы "\\t \\n \\r \\f \\v"

        Максимальная длина строки 220

        >>> BaseDevice.clear_description("test desc \\n desc")
        'test_desc__desc'

        >>> BaseDevice.clear_description("Описание порта")
        'Opisanie_porta'

        :param desc: Описание
        :return: Очищенное описание
        """

        unicode_ascii = {
            "а": "a",
            "б": "b",
            "в": "v",
            "г": "g",
            "д": "d",
            "е": "e",
            "ё": "e",
            "ж": "zh",
            "з": "z",
            "и": "i",
            "й": "i",
            "к": "k",
            "л": "l",
            "м": "m",
            "н": "n",
            "о": "o",
            "п": "p",
            "р": "r",
            "с": "s",
            "т": "t",
            "у": "u",
            "ф": "f",
            "х": "h",
            "ц": "c",
            "ч": "cz",
            "ш": "sh",
            "щ": "scz",
            "ъ": "",
            "ы": "y",
            "ь": "",
            "э": "e",
            "ю": "u",
            "я": "ja",
            "А": "A",
            "Б": "B",
            "В": "V",
            "Г": "G",
            "Д": "D",
            "Е": "E",
            "Ё": "E",
            "Ж": "ZH",
            "З": "Z",
            "И": "I",
            "Й": "I",
            "К": "K",
            "Л": "L",
            "М": "M",
            "Н": "N",
            "О": "O",
            "П": "P",
            "Р": "R",
            "С": "S",
            "Т": "T",
            "У": "U",
            "Ф": "F",
            "Х": "H",
            "Ц": "C",
            "Ч": "CZ",
            "Ш": "SH",
            "Щ": "SCH",
            "Ъ": "",
            "Ы": "y",
            "Ь": "",
            "Э": "E",
            "Ю": "U",
            "Я": "YA",
            " ": "_",
            "'": "/",
            "\\": "/",
            "[": "(",
            "]": ")",
            "{": "(",
            "}": ")",
            "—": "-",
        }

        ascii_str = ""
        for i in desc:
            if i in unicode_ascii:
                ascii_str += unicode_ascii[i]
            elif i in string.whitespace:
                continue
            elif i.isascii():
                ascii_str += i

        return ascii_str[:220]

    @staticmethod
    def find_or_empty(pattern: str, string_: str, *args, **kwargs):
        """
        Возвращает первое совпадение регулярного выражения в строке или пустую строку, если совпадений нет.

        :param pattern: Шаблон регулярного выражения для поиска
        :param string_: Строка для поиска
        """

        m = re.findall(pattern, string_, *args, **kwargs)
        return m[0] if m else ""

    @staticmethod
    def lock_session(func):
        """
        Используется для синхронизации доступа к удаленному терминалу оборудования между
        несколькими потоками.
        Блокирует доступ к удаленному терминалу для другого метода текущего оборудования
        на время выполнения данного метода.

        Необходимо декорировать каждый метод, в котором происходит отправка команд на
        оборудование, чтобы не было наложения команд, так как удаленная сессия для одного
        оборудования общая.
        """

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            with BaseDevice._get_session_lock(self):
                return func(self, *args, **kwargs)

        return wrapper

    def send_command(
        self,
        command: str,
        before_catch: str | None = None,
        expect_command=True,
        num_of_expect=10,
        space_prompt=None,
        prompt=None,
        pages_limit=None,
        command_linesep="\n",
        timeout: int = 20,
    ) -> str:
        """
        ## Отправляет команду на оборудование и считывает её вывод.

        Вывод будет содержать в себе строки от момента ввода команды, до (prompt: str), указанного в классе.

        :param command: Команда, которую необходимо выполнить на оборудовании.
        :param before_catch: Регулярное выражение, указывающее начало.
        :param expect_command: Не вносить текст команды в вывод.
        :param num_of_expect: Кол-во символов с конца команды, по которым необходимо её находить.
        :param space_prompt: Регулярное выражение, которое указывает на ожидание ввода клавиши,
                             для последующего отображения информации.
        :param prompt: Регулярное выражение, которое указывает на приглашение для ввода следующей команды.
        :param pages_limit: Кол-во страниц, если надо, которые будут выведены при постраничном отображении.
        :param command_linesep: Символ отправки команды (по умолчанию ```\\n```).
        :param timeout: Время ожидания ответа от оборудования.
        :return: Строка с результатом команды.
        """

        if space_prompt is None:
            space_prompt = self.space_prompt
        if prompt is None:
            prompt = self.prompt

        # Убираем предыдущий вывод до промпта, если он был.
        self.session.expect([self.prompt, pexpect.EOF, pexpect.TIMEOUT], timeout=0)  # noqa

        output = ""
        self.session.send(command + command_linesep)  # Отправляем команду

        if expect_command:
            # Считываем введенную команду с поправкой по длине символов
            self.session.expect(command[-num_of_expect:], timeout=2)

        if before_catch:
            # После ввода команды можем перехватить еще последовательность
            self.session.expect(before_catch)

        if space_prompt:  # Если необходимо постранично считать данные, то создаем цикл
            while pages_limit is None or pages_limit > 0:
                match = self.session.expect(
                    [  # noqa
                        prompt,  # 0 - конец
                        space_prompt,  # 1 - далее
                        pexpect.TIMEOUT,  # 2
                    ],
                    timeout=timeout,
                )

                output += remove_ansi_escape_codes(self.session.before)

                if match == 0:
                    break
                if match == 1:
                    # Отправляем символ пробела, для дальнейшего вывода
                    self.session.send(" ")
                    output += "\n"
                else:
                    print(f'{self.ip} - timeout во время выполнения команды "{command}"')
                    break

                # Если задано кол-во страниц
                if pages_limit:
                    pages_limit -= 1

        else:  # Если вывод команды выдается полностью, то пропускаем цикл
            # with contextlib.suppress(pexpect.TIMEOUT):
            self.session.expect(prompt, timeout=timeout)  # noqa
            # Убираем управляющие последовательности ANSI
            output += remove_ansi_escape_codes(self.session.before)
        return output

    @lock_session
    def execute_command(self, cmd: str) -> str:
        return self.send_command(cmd.strip())

    @lock_session
    def execute_commands_list(self, commands: list[RemoteCommand]) -> list[str]:
        """
        Отправляет список команд на оборудование и считывает их вывод.

        :param commands: Список команд, которые необходимо выполнить на оборудовании.
        :return: Список строк с результатами команд.
        """
        cmd_outputs = []
        self.session.expect([self.prompt, pexpect.EOF, pexpect.TIMEOUT], timeout=0.1)
        for line in commands:
            if line["conditions"]:
                self.session.sendline(line["command"])
                output = ""
                for condition in line["conditions"]:
                    ex_match = self.session.expect([self.prompt, condition["expect"]], timeout=20)
                    if ex_match == 1:
                        self.session.sendline(condition["command"])
                    output += remove_ansi_escape_codes(self.session.before)

                cmd_outputs.append(output)
                self.session.expect([self.prompt, pexpect.EOF, pexpect.TIMEOUT], timeout=0.2)

            else:
                cmd_outputs.append(self.send_command(line["command"].strip(), expect_command=False))
                self.session.expect([self.prompt, pexpect.EOF, pexpect.TIMEOUT], timeout=0.1)

        self.session.expect([self.prompt, pexpect.EOF, pexpect.TIMEOUT], timeout=0.2)
        return cmd_outputs

    @lock_session
    def get_mac_table(self) -> MACTableType:
        return []

    @lock_session
    def get_vlan_table(self) -> VlanTableType:
        return []
