import re
import pathlib
import string
import time
from functools import wraps
from typing import List, Tuple

import pexpect
from abc import ABC, abstractmethod

# Папка с шаблонами регулярных выражений для парсинга вывода оборудования
TEMPLATE_FOLDER = pathlib.Path(__file__).parent.parent / "templates"

# Аннотации типов
T_InterfaceList: type = List[Tuple[str, str, str]]
T_InterfaceVLANList: type = List[Tuple[str, str, str, list]]
T_MACTable: type = List[Tuple[int, str, str, str]]
T_MACList: type = List[Tuple[str, str]]
T_SplittedPort: type = Tuple[str, Tuple[str]]

# Обозначения медных типов по стандарту IEEE 802.3
COOPER_TYPES = ["T", "TX", "VG", "CX", "CR"]

# Обозначения оптических типов по стандарту IEEE 802.3
FIBER_TYPES = [
    "FOIRL",
    "F",
    "FX",
    "SX",
    "LX",
    "BX",
    "EX",
    "ZX",
    "SR",
    "ER",
    "SW",
    "LW",
    "EW",
    "LRM",
    "PR",
    "LR",
    "ER",
    "FR",
    "LH",
]


def interface_normal_view(interface) -> str:
    """
    Приводит имя интерфейса к виду принятому по умолчанию для коммутаторов

    Например:

    >>> interface_normal_view("Eth 0/1")
    'Ethernet 0/1'

    >>> interface_normal_view("GE1/0/12")
    'GigabitEthernet 1/0/12'
    """

    interface_number = re.findall(r"(\d+([/\\]?\d*)*)", str(interface))
    if re.match(r"^[Ee]t", interface):
        return f"Ethernet {interface_number[0][0]}"
    if re.match(r"^[Ff]a", interface):
        return f"FastEthernet {interface_number[0][0]}"
    if re.match(r"^[Gg][ieE]", interface):
        return f"GigabitEthernet {interface_number[0][0]}"
    if re.match(r"^\d+", interface):
        return re.findall(r"^\d+", interface)[0]
    if re.match(r"^[Tt]e", interface):
        return f"TenGigabitEthernet {interface_number[0][0]}"

    return ""


def range_to_numbers(ports_string: str) -> List[int]:
    """
    Переводит строку с диапазоном чисел в список

    Например:

    >>> range_to_numbers("10 to 14")
    [10, 11, 12, 13, 14]

    >>> range_to_numbers("134-136, 234, 411")
    [134, 135, 136, 234, 411]
    """

    ports_split = set()
    # Проверка наличия слова "to" в файле ports_string.
    if "to" in ports_string:
        # Если имеется формат "1 to 7 10 12 to 44"
        ports_split.update(
            *[
                set(range(int(v[0]), int(v[1]) + 1))
                for v in re.findall(r"(\d+)\s*to\s*(\d+)", ports_string)
            ]
        )

        # Добавляем к диапазону оставшиеся числа
        ports_split.update(
            map(int, filter(lambda x: x.isdigit(), ports_string.split(" ")))
        )

        return sorted(ports_split)

    if "," in ports_string:
        ports_split = ports_string.replace(" ", "").split(",")
    else:
        ports_split = ports_string.split()

    res_ports = []
    for p in ports_split:
        try:
            if "-" in p:
                # создает список портов из диапазона портов.
                port_range = list(range(int(p.split("-")[0]), int(p.split("-")[1]) + 1))
                for pr in port_range:
                    res_ports.append(int(pr))
            else:
                res_ports.append(int(p))
        except:
            pass

    return sorted(res_ports)


class BaseDevice(ABC):
    """
    Абстрактный базовый класс для устройств,
    содержит обязательные методы и начальные параметры для выполнения удаленных команд
    """

    prompt: str  # Регулярное выражение, которое указывает на приглашение для ввода следующей команды
    # Регулярное выражение, которое указывает на ожидание ввода клавиши, для последующего отображения информации
    space_prompt: str

    mac_format = ""  # Регулярное выражение, которое определяет отображение МАС адреса
    SAVED_OK = "Saved OK"  # Конфигурация была сохранена
    SAVED_ERR = "Saved Error"  # Ошибка при сохранении конфигурации
    vendor: str

    # Паттерн для управляющих последовательностей ANSI
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])|\x08")

    def __init__(self, session: pexpect, ip: str, auth: dict, model: str = ""):
        self.session: pexpect.spawn = session
        self.ip = ip
        self.model: str = model
        self.auth: dict = auth
        self.mac: str = ""
        self.serialno: str = ""
        self.os: str = ""
        self.os_version: str = ""
        self.lock = False

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
    def _lock(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # print("Try LOCK", func.__name__)
            while True:
                if not self.lock:
                    self.lock = True
                    # print("LOCK", func.__name__)
                    res = func(self, *args, **kwargs)
                    self.lock = False
                    # print("UNLOCK", func.__name__)
                    return res
                time.sleep(0.02)

        return wrapper

    def send_command(
        self,
        command: str,
        before_catch: str = None,
        expect_command=True,
        num_of_expect=10,
        space_prompt=None,
        prompt=None,
        pages_limit=None,
        command_linesep="\n",
    ) -> str:
        """
        ## Отправляет команду на оборудование и считывает её вывод

        Вывод будет содержать в себе строки от момента ввода команды, до (prompt: str), указанного в классе

        :param command: Команда, которую необходимо выполнить на оборудовании
        :param before_catch: Регулярное выражение, указывающее начало
        :param expect_command: Не вносить текст команды в вывод
        :param num_of_expect: Кол-во символов с конца команды, по которым необходимо её находить
        :param space_prompt: Регулярное выражение, которое указывает на ожидание ввода клавиши,
                             для последующего отображения информации
        :param prompt: Регулярное выражение, которое указывает на приглашение для ввода следующей команды
        :param pages_limit: Кол-во страниц, если надо, которые будут выведены при постраничном отображении
        :param command_linesep: Символ отправки команды (по умолчанию ```\\n```)
        :return: Строка с результатом команды
        """

        if space_prompt is None:
            space_prompt = self.space_prompt
        if prompt is None:
            prompt = self.prompt

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
                    [
                        prompt,  # 0 - конец
                        space_prompt,  # 1 - далее
                        pexpect.TIMEOUT,  # 2
                    ],
                    timeout=20,
                )

                # Убираем управляющие последовательности ANSI
                output += self.ansi_escape.sub(
                    "", self.session.before.decode(errors="ignore")
                )

                if match == 0:
                    break
                if match == 1:
                    # Отправляем символ пробела, для дальнейшего вывода
                    self.session.send(" ")
                    output += "\n"
                else:
                    print(
                        f'{self.ip} - timeout во время выполнения команды "{command}"'
                    )
                    break

                # Если задано кол-во страниц
                if pages_limit:
                    pages_limit -= 1

        else:  # Если вывод команды выдается полностью, то пропускаем цикл
            try:
                self.session.expect(prompt, timeout=20)
            except pexpect.TIMEOUT:
                pass
            # Убираем управляющие последовательности ANSI
            output += self.ansi_escape.sub(
                "", self.session.before.decode(errors="ignore")
            )
        return output

    @abstractmethod
    def get_interfaces(self) -> T_InterfaceList:
        """
        Интерфейсы на оборудовании

        :return: ```[ ('name', 'status', 'desc'), ... ]```
        """

    @abstractmethod
    def get_vlans(self) -> T_InterfaceVLANList:
        """
        Интерфейсы и VLAN на оборудовании

        :return: ```[ ('name', 'status', 'desc', ['vlans', ...]), ... ]```
        """

    @abstractmethod
    def get_mac(self, port: str) -> T_MACList:
        """
        Поиск маков на порту

        :return: ```[ ('vid', 'mac'), ... ]```
        """

    @abstractmethod
    def reload_port(self, port: str, save_config=True) -> str:
        """Перезагрузка порта"""

    @abstractmethod
    def set_port(self, port: str, status: str, save_config=True) -> str:
        """Изменение состояния порта"""

    @abstractmethod
    def save_config(self):
        """Сохраняем конфигурацию оборудования"""

    @abstractmethod
    def set_description(self, port: str, desc: str) -> str:
        """Изменяем описание порта"""

    @abstractmethod
    def get_port_info(self, port: str) -> dict:
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
