import pathlib
from typing import List, Tuple, Literal, TypedDict

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
T_InterfaceList = List[Tuple[PORT, STATUS, DESCRIPTION]]
T_InterfaceVLANList = List[Tuple[PORT, STATUS, DESCRIPTION, VLAN_LIST]]
T_MACTable = List[Tuple[VID, MAC, MACType, PORT]]
T_MACList = List[Tuple[VID, MAC]]
T_SplittedPort = Tuple[str, Tuple[str, ...]]

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