import re
from typing import List

import pexpect
import textfsm
from .base import BaseDevice, TEMPLATE_FOLDER, T_InterfaceList


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

    @BaseDevice._lock
    def get_interfaces(self) -> T_InterfaceList:
        result = []
        raw_intf_status = self.send_command(
            "show interfaces brief", expect_command=False
        )
        with open(
            f"{TEMPLATE_FOLDER}/interfaces/procurve_status.template", encoding="utf-8"
        ) as template_file:
            int_des_ = textfsm.TextFSM(template_file)
        intf_status: List[str, str, str] = int_des_.ParseText(raw_intf_status)  # Ищем интерфейсы

        for line in intf_status:
            port = self.find_or_empty(r"[ABCD]*\d+", line[0])
            port_output = self.send_command(
                f"show interfaces ethernet {port}", expect_command=False
            )
            desc = re.findall(r"Name\s*(:\s*\S*)\W+Link", port_output)
            result.append(
                (
                    line[0],
                    line[2].lower() if line[1] == "Yes" else "admin down",
                    desc[0][1:] if desc else "",
                )
            )
        return result

    def get_vlans(self) -> list:
        pass

    def get_mac(self, port: str) -> list:
        pass

    def reload_port(self, port: str, save_config=True) -> str:
        pass

    def set_port(self, port: str, status: str, save_config=True) -> str:
        pass

    def save_config(self):
        pass

    def set_description(self, port: str, desc: str) -> str:
        pass

    def get_port_info(self, port: str) -> str:
        pass

    def get_port_type(self, port: str) -> str:
        pass

    def get_port_config(self, port: str) -> str:
        pass

    def get_port_errors(self, port: str) -> str:
        pass

    def get_device_info(self) -> dict:
        pass
