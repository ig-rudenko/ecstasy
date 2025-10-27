import io
import re
import time
from pathlib import Path

from .base.device import AbstractConfigDevice, BaseDevice
from .base.factory import AbstractDeviceFactory
from .base.helpers import parse_by_template
from .base.types import (
    COOPER_TYPES,
    FIBER_TYPES,
    DeviceAuthDict,
    InterfaceListType,
    InterfaceType,
    InterfaceVLANListType,
    MACListType,
    PortInfoType,
)
from .base.validators import validate_and_format_port


def procurve_port_formatter(port: str) -> str:
    if not re.match(r"[ABCD]?\d+(-Trk\d+)?", port, flags=re.IGNORECASE):
        return ""

    return port.lower()


def validate_port(if_invalid_return=None):
    """
    ## Декоратор для проверки правильности порта и форматирования его
    на основе функции `interface_normal_view`.

    Valid:
        "A2" -> "a2"

        "A2-Trk2" -> "trk2"

    :param if_invalid_return: Что нужно вернуть, если порт неверный.
    """
    return validate_and_format_port(if_invalid_return=if_invalid_return, validator=procurve_port_formatter)


class ProCurve(BaseDevice, AbstractConfigDevice):
    prompt = r"\S+[#>] "
    space_prompt = r"-- MORE --, next page: Space, next line: Enter, quit: Control-C"
    vendor = "ProCurve"
    mac_format = r"\b[0-9a-f]{6}-[0-9a-f]{6}\b"

    def __init__(
        self,
        session,
        ip: str,
        auth: DeviceAuthDict,
        model="",
        snmp_community: str = "",
    ):
        super().__init__(session, ip, auth, model, snmp_community)
        sys_info = self.send_command("show system-information", before_catch="General System Information")
        self.mac = self.find_or_empty(r"Base MAC Addr\s+: (\S+)", sys_info)
        self.model = ""
        self.serialno = self.find_or_empty(r"Serial Number\s+: (\S+)", sys_info)
        self.os_version = self.find_or_empty(r"Software revision\s+: (\S+)", sys_info)
        self._grant_privileges()
        self._ports_info: dict[str, str] = {}

    def _grant_privileges(self):
        self.session.sendline("enable")
        if self.session.expect([self.prompt, "Login Name:"]):
            self.session.sendline(self.auth["login"])
            self.session.expect("Password:", timeout=1)
            self.session.sendline(self.auth["password"])
            self.session.expect(self.prompt)

    def send_command(
        self,
        command: str,
        before_catch: str | None = None,
        expect_command=True,
        num_of_expect=10,
        space_prompt=None,
        prompt=None,
        pages_limit=None,
        command_linesep="\n",
    ) -> str:
        return super().send_command(
            command=command,
            before_catch=before_catch,
            expect_command=False,
            num_of_expect=num_of_expect,
            space_prompt=space_prompt,
            prompt=prompt,
            pages_limit=pages_limit,
            command_linesep=command_linesep,
        )

    @BaseDevice.lock_session
    def get_interfaces(self) -> InterfaceListType:
        raw_intf_status = self.send_command("show interfaces brief")
        intf_status: list[tuple[str, str, str]] = parse_by_template(
            "interfaces/procurve_status.template", raw_intf_status
        )

        raw_intf_desc = self.send_command("show name")
        intf_desc: list[tuple[str, str]] = parse_by_template(
            "interfaces/procurve_description.template", raw_intf_desc
        )

        int_desc_dict = {row[0]: row[1].strip() for row in intf_desc}

        interfaces: InterfaceListType = []
        for name, _, link_status in intf_status:
            status: InterfaceType = "up"
            if link_status.lower() == "no":
                status = "admin down"
            elif "down" in link_status.lower():
                status = "down"

            no_trk_name = self._get_no_trk(name)
            interfaces.append((name, status, int_desc_dict.get(no_trk_name, "")))

        return interfaces

    @staticmethod
    def _get_no_trk(port: str):
        return re.sub(r"-trk\d+$", "", port.strip(), flags=re.IGNORECASE)

    @staticmethod
    def _get_like_trk(port: str):
        if trk := re.search(r"-(Trk\d+)$", port, flags=re.IGNORECASE):
            return trk.group(1).lower()
        return port

    def get_vlans(self) -> InterfaceVLANListType:
        return []

    @validate_port(if_invalid_return=[])
    @BaseDevice.lock_session
    def get_mac(self, port: str) -> MACListType:
        trk_port = self._get_like_trk(port)

        result: MACListType = []
        output = self.send_command(f"show mac-address ethernet {trk_port}")
        mac_list = re.findall(self.mac_format, output)
        for mac in mac_list:
            result.append((0, mac))
        return result

    def reload_port(self, port: str, save_config=True) -> str:
        self.send_command("configure")
        no_trk_port = self._get_no_trk(port)
        self.send_command(f"interface {no_trk_port}")

        self.send_command("enable")
        time.sleep(1)
        self.send_command("disable")

        self.send_command("exit")
        self.send_command("exit")

        return "Done"

    @validate_port()
    @BaseDevice.lock_session
    def set_port(self, port: str, status: str, save_config=True) -> str:
        self.send_command("configure")
        no_trk_port = self._get_no_trk(port)
        self.send_command(f"interface {no_trk_port}")

        if status == "up":
            self.send_command("enable")
        elif status == "down":
            self.send_command("disable")

        self.send_command("exit")
        self.send_command("exit")

        return "Done"

    @BaseDevice.lock_session
    def save_config(self) -> str:
        self.send_command("write memory")
        return self.SAVED_OK

    @validate_port()
    @BaseDevice.lock_session
    def set_description(self, port: str, desc: str) -> dict:
        self.send_command("configure")
        no_trk_port = self._get_no_trk(port)
        self.send_command(f"interface {no_trk_port}")

        desc = self.clear_description(desc)

        res = self.send_command("no name" if desc == "" else f"name {desc}")

        self.send_command("exit")
        self.send_command("exit")

        if match := re.search(r"Max length allowed = (\d+) characters", res):
            return {
                "max_length": match.group(1),
                "status": "fail",
            }

        self.lock = False
        return {
            "description": desc,
            "port": port,
            "status": "changed" if desc else "cleared",
            "info": self.save_config(),
        }

    @validate_port()
    def _get_port_info(self, port: str) -> str:
        if info := self._ports_info.get(port):
            return info

        no_trk_port = self._get_no_trk(port)

        show_int_brief_cmd = f"show interface brief ethernet {no_trk_port}"
        output = self.send_command(show_int_brief_cmd)
        result = re.sub(show_int_brief_cmd, "", output)

        show_int_cmd = f"show interfaces ethernet {no_trk_port}"
        output = self.send_command(show_int_cmd)
        result += re.sub(show_int_cmd, "", output)

        self._ports_info[port] = result
        return result

    @validate_port(if_invalid_return={"type": "text", "data": ""})
    @BaseDevice.lock_session
    def get_port_info(self, port: str) -> PortInfoType:
        info = self._get_port_info(port)
        return {"type": "text", "data": info}

    @validate_port()
    @BaseDevice.lock_session
    def get_port_type(self, port: str) -> str:
        info = self._get_port_info(port)
        match = re.search(
            rf"{port}\s+\d+/\d+([a-z]+)\s+\|\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+", info, flags=re.IGNORECASE
        )
        if not match:
            return "?"
        port_type = match.group(1)
        if port_type.upper() in COOPER_TYPES:
            return "COPPER"
        if port_type.upper() in FIBER_TYPES:
            return "FIBER"
        return "?"

    def get_port_config(self, port: str) -> str:
        return ""

    @validate_port(if_invalid_return="")
    @BaseDevice.lock_session
    def get_port_errors(self, port: str) -> str:
        info = self._get_port_info(port)
        if errors := re.search(r"Errors \(.+(?=\s+Rates \()", info, flags=re.DOTALL):
            return errors.group()
        return ""

    def get_device_info(self) -> dict:
        return {}

    def get_current_configuration(self) -> io.BytesIO | Path:
        data = self.send_command(
            "show running-config",
            expect_command=False,
            before_catch=r"Running configuration:",
        )
        return io.BytesIO(data.encode())


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
