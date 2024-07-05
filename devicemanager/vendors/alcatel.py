from typing import Literal

from .base.device import BaseDevice
from .base.types import PortInfoType, MACListType, InterfaceVLANListType, InterfaceListType


class Alcatel(BaseDevice):
    prompt = r"\S+# $"
    space_prompt = r"Press any key to continue (Q to quit)"
    mac_format = r"\S\S\S\S\.\S\S\S\S\.\S\S\S\S"  # 0018.e7d3.1d43
    vendor = "Alcatel"

    def get_interfaces(self) -> InterfaceListType:
        pass

    def get_vlans(self) -> InterfaceVLANListType:
        pass

    def get_mac(self, port: str) -> MACListType:
        pass

    def reload_port(self, port: str, save_config=True) -> str:
        pass

    def set_port(self, port: str, status: Literal["up", "down"], save_config=True) -> str:
        pass

    def save_config(self) -> str:
        pass

    def set_description(self, port: str, desc: str) -> dict:
        pass

    def get_port_info(self, port: str) -> PortInfoType:
        pass

    def get_port_type(self, port: str) -> str:
        pass

    def get_port_config(self, port: str) -> str:
        pass

    def get_port_errors(self, port: str) -> str:
        pass

    def get_device_info(self) -> dict:
        pass
