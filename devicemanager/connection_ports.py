from dataclasses import dataclass
from typing import Any

DEFAULT_TELNET_PORT = 23
DEFAULT_SSH_PORT = 22
DEFAULT_SNMP_PORT = 161
MIN_PORT = 1
MAX_PORT = 65535


@dataclass(frozen=True)
class DeviceConnectionPorts:
    """Connection ports for device protocols."""

    telnet_port: int = DEFAULT_TELNET_PORT
    ssh_port: int = DEFAULT_SSH_PORT
    snmp_port: int = DEFAULT_SNMP_PORT


def normalize_port(value: Any, default: int) -> int:
    """Return a valid TCP/UDP port or the provided default."""

    try:
        port = int(value)
    except (TypeError, ValueError):
        return default

    if MIN_PORT <= port <= MAX_PORT:
        return port
    return default


def normalize_connection_ports(
    telnet_port: Any = None,
    ssh_port: Any = None,
    snmp_port: Any = None,
) -> DeviceConnectionPorts:
    """Normalize optional device protocol ports."""

    return DeviceConnectionPorts(
        telnet_port=normalize_port(telnet_port, DEFAULT_TELNET_PORT),
        ssh_port=normalize_port(ssh_port, DEFAULT_SSH_PORT),
        snmp_port=normalize_port(snmp_port, DEFAULT_SNMP_PORT),
    )
