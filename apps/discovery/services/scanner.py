import ipaddress
import socket
from collections.abc import Iterable
from time import monotonic

from ping3 import ping

from .dataclasses import DiscoveryAttemptData

MAX_DISCOVERY_PREFIXLEN = 24
TCP_PORTS = {
    "ssh": 22,
    "telnet": 23,
}


def normalize_networks(networks: Iterable[str]) -> list[ipaddress.IPv4Network]:
    """Проверить и нормализовать список IPv4 сетей для discovery."""

    result = []
    for raw_network in networks:
        network = ipaddress.ip_network(str(raw_network).strip(), strict=False)
        if not isinstance(network, ipaddress.IPv4Network):
            raise ValueError("Discovery поддерживает только IPv4 подсети")
        if network.prefixlen < MAX_DISCOVERY_PREFIXLEN:
            raise ValueError("Максимальный размер подсети для discovery: /24")
        if network.is_loopback or network.is_link_local or network.is_multicast or network.is_unspecified:
            raise ValueError(f"Недопустимая подсеть для discovery: {network}")
        result.append(network)
    return result


def normalize_excludes(excludes: Iterable[str]) -> list[ipaddress.IPv4Address | ipaddress.IPv4Network]:
    """Проверить и нормализовать IP/CIDR исключения."""

    result: list[ipaddress.IPv4Address | ipaddress.IPv4Network] = []
    for raw_item in excludes:
        item = str(raw_item).strip()
        if not item:
            continue
        if "/" in item:
            network = ipaddress.ip_network(item, strict=False)
            if not isinstance(network, ipaddress.IPv4Network):
                raise ValueError("Discovery поддерживает только IPv4 исключения")
            result.append(network)
        else:
            address = ipaddress.ip_address(item)
            if not isinstance(address, ipaddress.IPv4Address):
                raise ValueError("Discovery поддерживает только IPv4 исключения")
            result.append(address)
    return result


def address_is_excluded(
    address: ipaddress.IPv4Address,
    excludes: Iterable[ipaddress.IPv4Address | ipaddress.IPv4Network],
) -> bool:
    """Вернуть True, если адрес входит в список исключений."""

    for excluded in excludes:
        if isinstance(excluded, ipaddress.IPv4Network) and address in excluded:
            return True
        if isinstance(excluded, ipaddress.IPv4Address) and address == excluded:
            return True
    return False


def build_scan_hosts(networks: Iterable[str], excludes: Iterable[str] | None = None) -> list[str]:
    """Построить список IP адресов для сканирования из CIDR и исключений."""

    normalized_networks = normalize_networks(networks)
    normalized_excludes = normalize_excludes(excludes or [])
    hosts = []

    for network in normalized_networks:
        for address in network.hosts():
            if address_is_excluded(address, normalized_excludes):
                continue
            hosts.append(str(address))

    return hosts


def ping_host(ip: str, timeout: int) -> bool:
    """Проверить доступность IP через ICMP."""

    return isinstance(ping(ip, timeout=timeout), float)


def tcp_is_open(ip: str, port: int, timeout: int) -> bool:
    """Проверить доступность TCP-порта."""

    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except OSError:
        return False


def preflight_address(
    ip: str, protocols: Iterable[str], timeout: int
) -> tuple[dict[str, bool], list[DiscoveryAttemptData]]:
    """Выполнить быстрые проверки IP перед тяжелым fingerprint."""

    attempts = []
    detected = {}

    started = monotonic()
    ping_ok = ping_host(ip, timeout)
    attempts.append(
        DiscoveryAttemptData(
            ip=ip,
            method="PING",
            status="SUCCESS" if ping_ok else "FAILED",
            duration_ms=int((monotonic() - started) * 1000),
        )
    )
    detected["ping"] = ping_ok

    for protocol in protocols:
        port = TCP_PORTS.get(protocol)
        if port is None:
            continue
        started = monotonic()
        is_open = tcp_is_open(ip, port, timeout)
        detected[protocol] = is_open
        attempts.append(
            DiscoveryAttemptData(
                ip=ip,
                method=f"TCP_{port}",
                status="SUCCESS" if is_open else "FAILED",
                duration_ms=int((monotonic() - started) * 1000),
            )
        )

    return detected, attempts
