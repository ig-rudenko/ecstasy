import re

from devicemanager.vendors.base.types import InterfaceListType, InterfaceType


def reformat_ltp_interfaces_list(interfaces: list[tuple[str, str, str]]) -> InterfaceListType:
    valid_interfaces: InterfaceListType = []
    for port_name, link_status, description in interfaces:
        status: InterfaceType = "up"
        if link_status.lower() == "admin down":
            status = "admin down"
        elif link_status.lower() == "down":
            status = "down"
        valid_interfaces.append((port_name, status, description))
    return valid_interfaces


def reformat_gpon_ports_state_output(output: str) -> InterfaceListType:
    ports: list[str] = []
    states: list[str] = []

    port_match = re.search(r"Gpon-port:([\s\d]+)", output)
    if port_match is not None:
        ports = port_match.group(1).split()

    state_match = re.search(r"State:([\s\S]+)", output)
    if state_match is not None:
        states = state_match.group(1).split()

    interfaces: InterfaceListType = []
    if ports and states:
        for port_number, state in zip(ports, states, strict=False):
            status: InterfaceType = "up"
            if state.upper() == "DISABLED":
                status = "admin down"
            # elif state.lower() == "down":
            #     status = "down"
            interfaces.append((f"pon-port {port_number}", status, ""))

    return interfaces
