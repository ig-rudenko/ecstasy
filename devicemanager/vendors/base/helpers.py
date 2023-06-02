import re
from typing import List


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
        ports_split.update(map(int, filter(str.isdigit, ports_string.split())))

        return sorted(ports_split)

    if "," in ports_string:
        ports_split = ports_string.replace(" ", "").split(",")
    else:
        ports_split = ports_string.split()

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
