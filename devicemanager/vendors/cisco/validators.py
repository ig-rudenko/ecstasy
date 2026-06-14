import re

from devicemanager.vendors.base.helpers import interface_normal_view
from devicemanager.vendors.base.validators import validate_and_format_port


def cisco_interface_normal_view(interface: str) -> str:
    """
    Приводит имя интерфейса к виду принятому по умолчанию для коммутаторов Cisco виду.

    >>> cisco_interface_normal_view("Po21")
    'port-channel 21'

    >>> cisco_interface_normal_view("port-channel21")
    'port-channel 21'

    >>> cisco_interface_normal_view("port-channel 21")
    'port-channel 21'

    >>> cisco_interface_normal_view("Eth 0/1")
    'Ethernet 0/1'

    >>> cisco_interface_normal_view("GE1/0/12")
    'GigabitEthernet 1/0/12'

    >>> cisco_interface_normal_view("gi1")
    'GigabitEthernet 1'

    >>> cisco_interface_normal_view("Gi 1/0/1 (10G)")
    'GigabitEthernet 1/0/1'

    >>> cisco_interface_normal_view("GigabitEthernet")
    'GigabitEthernet'

    >>> cisco_interface_normal_view("21")
    '21'
    """
    interface = interface.strip()
    if intf_match := re.search(r"^(?:[Pp]o|port-channel\s*)(?P<number>\d+)$", interface):
        return f"port-channel {intf_match.group('number')}"
    return interface_normal_view(interface)


def validate_and_format_port_for_cisco(if_invalid_return=None):
    """
    Декоратор для проверки правильности порта и форматирования его
    на основе функции `cisco_interface_normal_view`

    Valid:
        "eth12" -> "Ethernet 12"

        "gi 1/0/1" -> "GigabitEthernet 1/0/1"

        "Po21" -> "port-channel 21

        "port-channel21" -> "port-channel 21

    :param if_invalid_return: Что нужно вернуть, если порт неверный.
    """
    return validate_and_format_port(
        if_invalid_return=if_invalid_return, validator=cisco_interface_normal_view
    )
