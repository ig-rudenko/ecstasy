import re
from typing import AnyStr

import textfsm

from devicemanager.vendors.base.types import TEMPLATE_FOLDER


def remove_ansi_escape_codes(string: AnyStr | None) -> str:
    """Убираем управляющие последовательности ANSI"""
    if string is not None:
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])|\x08")
        if isinstance(string, bytes):
            clean_string = string.decode("utf-8")
        else:
            clean_string = str(string)

        return ansi_escape.sub("", clean_string)
    return ""


def range_to_numbers(ports_string: str) -> list[int]:
    """
    Переводит строку с диапазоном чисел в список

    Например:

    >>> range_to_numbers("10 to 14")
    [10, 11, 12, 13, 14]

    >>> range_to_numbers("134-136, 234, 411")
    [134, 135, 136, 234, 411]
    """

    ports_split: set = set()

    # Проверка наличия слова "to" в файле ports_string.
    if "to" in ports_string:
        # Если имеется формат "1 to 7 10 12 to 44"
        ports_split.update(
            *[set(range(int(v[0]), int(v[1]) + 1)) for v in re.findall(r"(\d+)\s*to\s*(\d+)", ports_string)]
        )

        # Добавляем к диапазону оставшиеся числа
        ports_split.update(map(int, filter(str.isdigit, ports_string.split())))

        return sorted(ports_split)

    if "," in ports_string:
        ports_split = set(ports_string.replace(" ", "").split(","))
    else:
        ports_split = set(ports_string.split())

    res_ports = []
    for p in ports_split:
        try:
            if "-" in p:
                # Создаем список целых чисел, представляющих диапазон портов. ( 134-136 )
                # Строка `p`, содержит диапазон портов, разделенных дефисом, разбиваем ее на два целых числа,
                # используя дефис в качестве разделителя, а затем создаем список целых чисел,
                # используя функцию `range()`, которая затем преобразуется в список с помощью функции `list()`.
                port_range = list(range(int(p.split("-")[0]), int(p.split("-")[1]) + 1))
                for pr in port_range:
                    res_ports.append(int(pr))
            else:
                res_ports.append(int(p))
        except (ValueError, IndexError):
            pass

    return sorted(res_ports)


def interface_normal_view(interface) -> str:
    """
    Приводит имя интерфейса к виду принятому по умолчанию для коммутаторов

    Например:

    >>> interface_normal_view("Eth 0/1")
    'Ethernet 0/1'

    >>> interface_normal_view("GE1/0/12")
    'GigabitEthernet 1/0/12'

    >>> interface_normal_view("gi1")
    'GigabitEthernet 1'

    >>> interface_normal_view("Gi 1/0/1 (10G)")
    'GigabitEthernet 1/0/1'

    >>> interface_normal_view("GigabitEthernet")
    'GigabitEthernet'

    >>> interface_normal_view("21")
    '21'
    """

    if interface_numbers := re.search(r"(\d+(?:[/\\]?\d*)*)", str(interface)):
        port_number = interface_numbers.group(1)
    else:
        port_number = ""

    if re.match(r"^[Ee]t", interface):
        return f"Ethernet {port_number}".strip()
    if re.match(r"^[Ff]a", interface):
        return f"FastEthernet {port_number}".strip()
    if re.match(r"^[Gg][ieE]", interface):
        return f"GigabitEthernet {port_number}".strip()
    if n := re.match(r"^\d+", interface):
        return n.group()
    if re.match(r"^[Tt]e", interface):
        return f"TenGigabitEthernet {port_number}".strip()

    return ""


def parse_by_template(template_name: str, text: str) -> list:
    """
    Принимает имя шаблона и текст в качестве входных данных, открывает файл шаблона,
    использует библиотеку TextFSM для анализа текста и возвращает проанализированный вывод.

    :param template_name: Параметр `template_name` представляет собой строку, представляющую имя файла шаблона.
     Этот файл содержит структуру шаблона, которая будет использоваться для разбора параметра text.
    :param text: Параметр `text` представляет собой строку, представляющую входной текст, который вы хотите
     проанализировать, используя указанный шаблон
    :return: Возвращает список.
    """

    with open(f"{TEMPLATE_FOLDER}/{template_name}", encoding="utf-8") as template_file:
        # Используем библиотеку TextFSM для анализа.
        int_des_ = textfsm.TextFSM(template_file)
        # Разбираем вывод команды.
        return int_des_.ParseText(text)


def normalize_number_suffix(s_number: str) -> int:
    s = s_number.strip().lower().replace(",", ".")  # удалим пробелы и запятые заменим на точки.

    if s.endswith("k"):
        multiplier = 1_000
        s = s[:-1]
    elif s.endswith("m"):
        multiplier = 10**6
        s = s[:-1]
    elif s.endswith("g"):
        multiplier = 10**9
        s = s[:-1]
    elif s.endswith("t"):
        multiplier = 10**12
        s = s[:-1]
    else:
        multiplier = 1

    try:
        return int(float(s) * multiplier)
    except ValueError:
        return -1
