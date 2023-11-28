from concurrent.futures import ThreadPoolExecutor
from re import findall
from typing import List, NamedTuple

from check.models import Devices
from devicemanager.exceptions import BaseDeviceException
from devicemanager.vendors.base.types import ArpInfoResult
from net_tools.models import DevicesForMacSearch


class MacIpFindResult(NamedTuple):
    device: Devices
    results: List[ArpInfoResult]


def find_mac_or_ip(ip_or_mac: str) -> List[MacIpFindResult]:
    # Получение устройств из базы данных, которые используются в поиске MAC/IP адресов
    devices_for_search = DevicesForMacSearch.objects.all()

    # Поиск IP-адреса в строке.
    find_address = findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", ip_or_mac)
    if find_address:
        # Нашли IP адрес
        find_type: str = "ip"
        find_address = find_address[0]

    else:
        # Поиск всех шестнадцатеричных символов из входной строки.
        find_address = "".join(findall(r"[a-fA-F\d]", ip_or_mac)).lower()
        # Нашли MAC адрес
        find_type: str = "mac"
        # Проверка правильности MAC-адреса.
        if not find_address or len(find_address) < 6 or len(find_address) > 12:
            return []

    match: List[MacIpFindResult] = []

    # Менеджер контекста, который создает пул потоков и выполняет код внутри блока with.
    with ThreadPoolExecutor() as execute:
        # Проходит через каждое устройство в списке устройств.
        for dev in devices_for_search:
            # Отправка задачи в пул потоков.
            execute.submit(
                get_ip_or_mac_from, dev.device, find_address, match, find_type
            )

    return match


def get_ip_or_mac_from(
    model_dev: Devices,
    find_address: str,
    result: List[MacIpFindResult],
    find_type: str,
) -> None:
    """
    ## Подключается к оборудованию, смотрит MAC адрес в таблице arp и записывает результат в список result

    :param model_dev: Оборудование, на котором надо искать.
    :param find_address: Адрес, который надо искать (IP или MAC).
    :param result: Список, в который будет добавлен результат.
    :param find_type: Тип поиска `ip` или `mac`.
    """

    session = model_dev.connect()
    info: List[ArpInfoResult] = []

    try:
        # Проверка, является ли find_type IP-адресом и имеет ли сеанс атрибут search_ip.
        if find_type == "ip":
            info = session.search_ip(find_address)
        # Проверка того, является ли find_type MAC-адресом и имеет ли сеанс атрибут search_mac.
        elif find_type == "mac":
            info = session.search_mac(find_address)

    except BaseDeviceException:
        pass

    if info:
        result.append(MacIpFindResult(device=model_dev, results=info))
