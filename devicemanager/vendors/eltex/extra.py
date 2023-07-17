from typing import List

from devicemanager.vendors.base.types import T_InterfaceList, InterfaceStatus


def validate_ltp_interfaces_list(interfaces: List[List[str]]) -> T_InterfaceList:
    valid_interfaces: T_InterfaceList = []
    for port_name, link_status in interfaces:
        if link_status.lower() == "admin down":
            status = InterfaceStatus.admin_down.value
        elif link_status.lower() == "down":
            status = InterfaceStatus.down.value
        else:
            status = InterfaceStatus.up.value

        valid_interfaces.append((port_name, status, ""))
    return valid_interfaces
