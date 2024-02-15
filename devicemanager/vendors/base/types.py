import pathlib
from enum import Enum
from typing import Literal, TypedDict, NamedTuple

# Папка с шаблонами регулярных выражений для парсинга вывода оборудования
TEMPLATE_FOLDER = pathlib.Path(__file__).parent.parent.parent / "templates"

# Аннотации типов
MAC = str
MACType = Literal["static", "dynamic", "security"]
PORT = str
STATUS = str
DESCRIPTION = str
VID = int
VLAN_LIST = list
T_MACList = list[tuple[VID, MAC]]


class InterfaceStatus(Enum):
    up = "up"
    down = "down"
    admin_down = "admin down"
    not_present = "notPresent"
    dormant = "dormant"


T_Interface = Literal["up", "down", "admin down", "notPresent", "dormant"]

T_InterfaceList = list[tuple[PORT, T_Interface, DESCRIPTION]]
T_InterfaceVLANList = list[tuple[PORT, T_Interface, DESCRIPTION, VLAN_LIST]]
T_MACTable = list[tuple[VID, MAC, MACType, PORT]]


T_SplittedPort = tuple[str, tuple[str, ...]]


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


class DeviceAuthDict(TypedDict):
    login: str
    password: str
    privilege_mode_password: str


class SystemInfo(TypedDict):
    mac: str
    vendor: str
    model: str
    serialno: str


class SetDescriptionResult(NamedTuple):
    status: Literal["changed", "cleared", "fail"]
    description: str = ""
    saved: str = ""
    port: str = ""
    error: str = ""
    max_length: int = 0


class ArpInfoResult(NamedTuple):
    ip: str
    mac: str
    vlan: str
    device_name: str = ""
    port: str = ""
