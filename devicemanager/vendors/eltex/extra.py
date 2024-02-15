from devicemanager.vendors.base.types import InterfaceListType, InterfaceType


def reformat_ltp_interfaces_list(interfaces: list[tuple[str, str]]) -> InterfaceListType:
    valid_interfaces: InterfaceListType = []
    for port_name, link_status in interfaces:
        status: InterfaceType = "up"
        if link_status.lower() == "admin down":
            status = "admin down"
        elif link_status.lower() == "down":
            status = "down"
        valid_interfaces.append((port_name, status, ""))
    return valid_interfaces
