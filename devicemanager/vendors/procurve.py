import re
from typing import List

import pexpect
import textfsm
from .base.device import BaseDevice
from .base.helpers import parse_by_template
from .base.types import (
    TEMPLATE_FOLDER,
    T_InterfaceList,
    T_InterfaceVLANList,
    T_MACList,
    InterfaceStatus,
)


class ProCurve(BaseDevice):
    prompt = r"\S+#"
    space_prompt = r"-- MORE --, next page: Space, next line: Enter, quit: Control-C"
    vendor = "ProCurve"

    def __init__(self, session: pexpect, ip: str, auth: dict, model=""):
        super().__init__(session, ip, auth, model)
        sys_info = self.send_command(
            "show system-information",
            before_catch="General System Information",
            expect_command=False,
        )
        self.model = self.find_or_empty(r"Base MAC Addr\s+: (\S+)", sys_info)
        self.serialno = self.find_or_empty(r"Serial Number\s+: (\S+)", sys_info)
        self.os_version = self.find_or_empty(r"Software revision\s+: (\S+)", sys_info)

    @BaseDevice.lock_session
    def get_interfaces(self) -> T_InterfaceList:
        result = []
        raw_intf_status = self.send_command("show interfaces brief", expect_command=False)

        intf_status: List[str] = parse_by_template(
            "interfaces/procurve_status.template", raw_intf_status
        )

        for line in intf_status:
            port = self.find_or_empty(r"[ABCD]*\d+", line[0])
            port_output = self.send_command(
                f"show interfaces ethernet {port}", expect_command=False
            )
            desc = re.findall(r"Name\s*(:\s*\S*)\W+Link", port_output)

            if line[1].strip() != "Yes":
                status = InterfaceStatus.admin_down.value
            elif line[2].strip().lower() == "up":
                status = InterfaceStatus.down.value
            else:
                status = InterfaceStatus.down.value

            result.append(
                (
                    line[0],
                    status,
                    desc[0][1:] if desc else "",
                )
            )
        return result

    def get_vlans(self) -> T_InterfaceVLANList:
        return []

    def get_mac(self, port: str) -> T_MACList:
        return []

    def reload_port(self, port: str, save_config=True) -> str:
        return ""

    def set_port(self, port: str, status: str, save_config=True) -> str:
        return ""

    def save_config(self):
        pass

    def set_description(self, port: str, desc: str) -> str:
        return ""

    def get_port_info(self, port: str) -> dict:
        return {}

    def get_port_type(self, port: str) -> str:
        return ""

    def get_port_config(self, port: str) -> str:
        return ""

    def get_port_errors(self, port: str) -> str:
        return ""

    def get_device_info(self) -> dict:
        return {}
