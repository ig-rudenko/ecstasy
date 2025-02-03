import pathlib
from typing import Literal, TypedDict, NamedTuple, Any

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
MACListType = list[tuple[VID, MAC]]

InterfaceType = Literal["up", "down", "admin down", "notPresent", "dormant"]

InterfaceListType = list[tuple[PORT, InterfaceType, DESCRIPTION]]
InterfaceVLANListType = list[tuple[PORT, InterfaceType, DESCRIPTION, VLAN_LIST]]
MACTableType = list[tuple[VID, MAC, MACType, PORT]]

SplittedPortType = tuple[str, tuple[str, ...]]


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
    "X",
]


class DeviceAuthDict(TypedDict):
    login: str
    password: str
    privilege_mode_password: str


class PortInfoType(TypedDict):
    type: str
    data: Any


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
    info: str = ""
    max_length: int = 0


class ArpInfoResult(NamedTuple):
    ip: str
    mac: str
    vlan: str
    device_name: str = ""
    port: str = ""
