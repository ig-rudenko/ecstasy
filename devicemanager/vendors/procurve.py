import re

from .base.device import BaseDevice
from .base.factory import AbstractDeviceFactory
from .base.helpers import parse_by_template
from .base.types import (
    InterfaceListType,
    InterfaceVLANListType,
    MACListType,
    DeviceAuthDict,
    InterfaceType,
    PortInfoType,
)


class ProCurve(BaseDevice):
    prompt = r"\S+#"
    space_prompt = r"-- MORE --, next page: Space, next line: Enter, quit: Control-C"
    vendor = "ProCurve"

    def __init__(
        self,
        session,
        ip: str,
        auth: DeviceAuthDict,
        model="",
        snmp_community: str = "",
    ):
        super().__init__(session, ip, auth, model, snmp_community)
        sys_info = self.send_command(
            "show system-information",
            before_catch="General System Information",
            expect_command=False,
        )
        self.model = self.find_or_empty(r"Base MAC Addr\s+: (\S+)", sys_info)
        self.serialno = self.find_or_empty(r"Serial Number\s+: (\S+)", sys_info)
        self.os_version = self.find_or_empty(r"Software revision\s+: (\S+)", sys_info)

    @BaseDevice.lock_session
    def get_interfaces(self) -> InterfaceListType:
        result = []
        raw_intf_status = self.send_command("show interfaces brief", expect_command=False)

        intf_status: list[str] = parse_by_template("interfaces/procurve_status.template", raw_intf_status)

        for line in intf_status:
            port = self.find_or_empty(r"[ABCD]*\d+", line[0])
            port_output = self.send_command(f"show interfaces ethernet {port}", expect_command=False)
            desc = re.findall(r"Name\s*(:\s*\S*)\W+Link", port_output)

            status: InterfaceType = "down"
            if line[1].strip() != "Yes":
                status = "admin down"
            elif line[2].strip().lower() == "up":
                status = "up"

            result.append(
                (
                    line[0],
                    status,
                    desc[0][1:] if desc else "",
                )
            )
        return result

    def get_vlans(self) -> InterfaceVLANListType:
        return []

    def get_mac(self, port: str) -> MACListType:
        return []

    def reload_port(self, port: str, save_config=True) -> str:
        return ""

    def set_port(self, port: str, status: str, save_config=True) -> str:
        return ""

    def save_config(self):
        pass

    def set_description(self, port: str, desc: str) -> dict:
        return {"status": "fail", "error": "Изменение описания недоступно"}

    def get_port_info(self, port: str) -> PortInfoType:
        return {"type": "text", "data": ""}

    def get_port_type(self, port: str) -> str:
        return ""

    def get_port_config(self, port: str) -> str:
        return ""

    def get_port_errors(self, port: str) -> str:
        return ""

    def get_device_info(self) -> dict:
        return {}


class ProCurveFactory(AbstractDeviceFactory):
    @staticmethod
    def is_can_use_this_factory(session=None, version_output=None) -> bool:
        return version_output and "Image stamp:" in str(version_output)

    @classmethod
    def get_device(
        cls,
        session,
        ip: str,
        snmp_community: str,
        auth: DeviceAuthDict,
        version_output: str = "",
    ) -> BaseDevice:
        return ProCurve(session, ip, auth, snmp_community=snmp_community)
