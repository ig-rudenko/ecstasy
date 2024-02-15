from devicemanager.vendors.base.types import T_InterfaceList, T_Interface


def reformat_ltp_interfaces_list(interfaces: list[tuple[str, str]]) -> T_InterfaceList:
    valid_interfaces: T_InterfaceList = []
    for port_name, link_status in interfaces:
        status: T_Interface = "up"
        if link_status.lower() == "admin down":
            status = "admin down"
        elif link_status.lower() == "down":
            status = "down"
        valid_interfaces.append((port_name, status, ""))
    return valid_interfaces
