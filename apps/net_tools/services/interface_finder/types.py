import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import TypedDict

from devicemanager.device import Interfaces


@dataclass
class InterfaceComment:
    user: str
    text: str
    created_time: datetime

    def to_dict(self) -> "InterfaceCommentDict":
        return {"user": self.user, "text": self.text, "createdTime": self.created_time}


@dataclass
class DeviceInterfacesComments:
    interfaces: dict[str, list[InterfaceComment]] = field(default_factory=dict)


@dataclass
class Comments:
    devices: dict[str, DeviceInterfacesComments] = field(default_factory=dict)

    def get_interface(self, device_name: str, interface_name: str) -> list[InterfaceComment]:
        device_interfaces = self.devices.get(device_name)
        if device_interfaces is not None:
            return device_interfaces.interfaces.get(interface_name, [])
        return []


class InterfaceCommentDict(TypedDict):
    user: str
    text: str
    createdTime: datetime


class InterfaceInfoDict(TypedDict):
    name: str
    status: str
    description: str
    vlans: str
    savedTime: str
    verboseSavedTime: str
    verboseVlansSavedTime: str
    vlansSavedTime: str


class DescriptionFinderResult(TypedDict):
    device: str
    interface: InterfaceInfoDict
    comments: list[InterfaceCommentDict]


@dataclass
class DeviceInterfacesData:
    interfaces: Interfaces
    interfaces_date: datetime | None
    vlans_date: datetime | None

    def get_interface_vlans(self, interface_name: str) -> str:
        for interface_with_vlans in self.interfaces:
            if interface_with_vlans.name == interface_name:
                return ", ".join(map(str, interface_with_vlans.vlan))
        return ""


@dataclass(kw_only=True, slots=True)
class InterfaceFinderFilter:
    description_pattern: str | re.Pattern[str]
    interface_name: str | re.Pattern[str] | None = None
    device_name: str | re.Pattern[str] | None = None
    has_comment: bool = False
    interface_status: str | None = None
    discovered_datetime_gt: str | None = None
    vlans_superset: set[int] | None = None
    vlans: set[int] | None = None
    vlans_exclude: set[int] | None = None
