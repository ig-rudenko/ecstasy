import re
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from ipaddress import IPv4Address
from re import findall
from typing import Literal, NamedTuple

from apps.check.models import Devices
from apps.check.services.filters import filter_devices_qs_by_user
from devicemanager.exceptions import BaseDeviceException
from devicemanager.vendors.base.types import ArpInfoResult

from ..models import DevicesForMacSearch


class MacIpFindResult(NamedTuple):
    device: Devices
    results: list[ArpInfoResult]


class MacIpFindQuery(NamedTuple):
    find_type: Literal["ip", "mac"]
    address: str


def find_mac_or_ip(ip_or_mac: str) -> list[MacIpFindResult]:
    """
    Ищет IP или MAC на устройствах, выбранных для WTF-поиска.
    """
    query = _parse_find_query(ip_or_mac)
    if query is None:
        return []

    devices_for_search = list(DevicesForMacSearch.objects.select_related("device", "device__auth_group"))

    with ThreadPoolExecutor() as executor:
        results = executor.map(
            lambda dev: get_ip_or_mac_from(dev.device, query.address, query.find_type),
            devices_for_search,
        )

    return [result for result in results if result is not None]


def _parse_find_query(ip_or_mac: str) -> MacIpFindQuery | None:
    """
    Возвращает нормализованный IP или MAC для поиска.
    """
    value = ip_or_mac.strip()
    find_address_match = findall(r"\d{1,3}(?:\.\d{1,3}){3}", value)
    if find_address_match:
        try:
            return MacIpFindQuery(find_type="ip", address=str(IPv4Address(find_address_match[0])))
        except ValueError:
            return None

    find_address = "".join(findall(r"[a-fA-F\d]", value)).lower()
    if not find_address or len(find_address) < 6 or len(find_address) > 12:
        return None

    return MacIpFindQuery(find_type="mac", address=find_address)


def get_ip_or_mac_from(
    model_dev: Devices,
    find_address: str,
    find_type: Literal["ip", "mac"],
) -> MacIpFindResult | None:
    """
    ## Подключается к оборудованию и ищет IP или MAC в таблице ARP

    :param model_dev: Оборудование, на котором надо искать.
    :param find_address: Адрес, который надо искать (IP или MAC).
    :param find_type: Тип поиска `ip` или `mac`.
    """

    try:
        session = model_dev.connect()
        if find_type == "ip":
            info = session.search_ip(find_address)
        else:
            info = session.search_mac(find_address)
    except BaseDeviceException:
        return None

    if info:
        return MacIpFindResult(device=model_dev, results=info)

    return None


def collect_ip_mac_info_ips(ip_or_mac: str, arp_info) -> set[str]:
    """
    Собирает IP-адреса из запроса и результатов ARP-поиска.
    """
    ips = {line.ip for info in arp_info for line in info.results if line.ip}
    request_ip = _normalize_ipv4(ip_or_mac)
    if request_ip:
        ips.add(request_ip)
    return ips


def _normalize_ipv4(value: str) -> str:
    """
    Возвращает IPv4 в каноническом виде или пустую строку.
    """
    value = value.strip()
    if not re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", value):
        return ""
    try:
        return str(IPv4Address(value))
    except ValueError:
        return ""


def get_ecstasy_devices_by_ip(ips: Iterable[str], user) -> list[dict]:
    """
    Возвращает оборудование Ecstasy, доступное пользователю, по списку IP-адресов.
    """
    devices_qs = Devices.objects.filter(ip__in=ips).select_related("group").order_by("name")
    devices_qs = filter_devices_qs_by_user(devices_qs, user)
    return [
        {
            "id": device.id,
            "name": device.name,
            "ip": device.ip,
            "url": device.get_absolute_url(),
            "group": device.group.name,
            "vendor": device.vendor or "",
            "model": device.model or "",
            "active": device.active,
        }
        for device in devices_qs
    ]
