import re
import time
from typing import Literal

from devicemanager.vendors import BaseDevice
from devicemanager.vendors.base.factory import AbstractDeviceFactory
from devicemanager.vendors.base.types import (
    DeviceAuthDict,
    InterfaceListType,
    InterfaceType,
    InterfaceVLANListType,
    MACListType,
    PortInfoType,
)
from devicemanager.vendors.base.validators import validate_and_format_port


def validate_port(if_invalid_return=None):

    def validator(port: str) -> str:
        if port.strip().isdigit():
            return port
        if re.match(r"enet\d+", port) is not None:
            return port
        return ""

    return validate_and_format_port(if_invalid_return=if_invalid_return, validator=validator)


class Zyxel(BaseDevice):

    vendor = "Zyxel"
    prompt = r">\s*$"
    space_prompt = "Press any key to continue"
    mac_format = r"\S\S:" * 5 + r"\S\S"

    def __init__(
        self,
        session,
        ip: str,
        auth: DeviceAuthDict,
        model: str = "",
        snmp_community: str = "",
    ):
        super().__init__(session, ip, auth, model, snmp_community)
        info = self.send_command("sys info show", expect_command=False)
        self.model = self.find_or_empty(r"Model: (\S+)", info)
        self.mac = self.find_or_empty(r"MAC address: (\S+)", info)
        self.serialno = self.find_or_empty(r"Serial number: (\S+)", info)
        self.os = "ZyNOS"
        self.os_version = self.find_or_empty(r"Bootbase version: (.+)", info)
        self.port_type_map: dict[str, str] = {}

    @BaseDevice.lock_session
    def get_interfaces(self) -> InterfaceListType:
        interfaces: InterfaceListType = []
        interfaces_info = {}

        adsl_stats = self.send_command("statistics adsl show", expect_command=False)
        adsl_parsed = re.findall(r"\s+(\d+)\s+(\S+)\s+(.+?)\s+(?:\d+|-)/\s+(?:\d+|-)\s+", adsl_stats)
        for port, status, *_ in adsl_parsed:
            interfaces_info[port] = {"status": status}

        adsl_detail_info = self.send_command("adsl show", expect_command=False)
        admin_status_info, description_info = adsl_detail_info.split("Subscriber Info:", 1)

        adsl_admin_down_parsed = re.findall(r"\s+(\d+)\s+([V\-])\s+\S+\s+", admin_status_info)
        for port, enabled in adsl_admin_down_parsed:
            interfaces_info.setdefault(port, {})["enabled"] = enabled
        adsl_desc_parsed = re.findall(r"\s+(\d+)\s+(\S+)\s+\S+", description_info)
        for port, desc in adsl_desc_parsed:
            interfaces_info.setdefault(port, {})["description"] = desc

        ether_stats = self.send_command("statistics enet show", expect_command=False)
        ether_parsed = re.findall(r"(\S+\d+)\s+(link up|link down|disabled)\s+(\S+)\s+", ether_stats)
        for port, status, port_type in ether_parsed:
            interfaces_info[port] = {"status": status}
            self.port_type_map[port] = port_type  # Добавляем тип порта (cooper, fiber)

        ether_desc = self.send_command("switch enet show", expect_command=False)
        ether_desc_parsed = re.findall(r"^(\S+\d+)\s+\S+ +(.*)", ether_desc, flags=re.MULTILINE)
        for port, desc in ether_desc_parsed:
            interfaces_info.setdefault(port, {})["description"] = desc

        for name, values in interfaces_info.items():
            if values.get("enabled") == "-" or values.get("status") == "disabled":
                s: InterfaceType = "admin down"
            elif values.get("status") == "V" or values.get("status") == "link up":
                s = "up"
            else:
                s = "down"

            desc = values.get("description", "").strip()
            if desc == "-":
                desc = ""
            interfaces.append((name, s, desc))

        return interfaces

    @BaseDevice.lock_session
    def get_vlans(self) -> InterfaceVLANListType:
        self.lock = False
        interfaces = self.get_interfaces()
        self.lock = True

        result: InterfaceVLANListType = []
        vlans: dict[int, list[str]] = {}

        output = self.send_command("statistics vlan", expect_command=False)
        vlans_parts = re.split(r"(?=\s\d+\s-\s+static)", output)

        for part in vlans_parts:
            vlan_match = re.match(r" \d+", part)
            if not vlan_match:
                continue

            vlan = int(vlan_match.group())

            fixed_line = self.find_or_empty(r"\d+ \d+\s+([FXNUTE-]+ [FXNUTE-]+)", part)

            index = 1
            port_prefix = ""
            for value in fixed_line:
                if value == " ":
                    index = 1
                    port_prefix = "enet"
                    continue

                if value != "X":
                    vlans.setdefault(vlan, []).append(f"{port_prefix}{index}")
                index += 1

        for name, status, desc in interfaces:
            port_vlans = []
            for vlan, ports in vlans.items():
                if name in ports:
                    port_vlans.append(vlan)

            result.append((name, status, desc, port_vlans))

        return result

    @BaseDevice.lock_session
    @validate_port()
    def get_mac(self, port: str) -> MACListType:
        mac_list: MACListType = []
        output = self.send_command(f"statistics mac {port}", expect_command=False)
        parsed = re.findall(rf"\d+\s+(\d+)\s+({self.mac_format})", output)
        for vid, mac in parsed:
            mac_list.append((int(vid), mac))
        return mac_list

    @BaseDevice.lock_session
    @validate_port()
    def reload_port(self, port: str, save_config=True) -> str:
        if port.startswith("enet"):
            self.send_command(f"switch enet disable {port}", expect_command=False)
            time.sleep(1)
            self.send_command(f"switch enet enable {port}", expect_command=False)

        else:
            self.send_command(f"adsl disable {port}", expect_command=False)
            time.sleep(1)
            self.send_command(f"adsl enable {port}", expect_command=False)

        result = f"reloaded port {port}"
        if save_config:
            self.lock = False
            saved = self.save_config()
            result += f" {saved}"
        return result

    @BaseDevice.lock_session
    @validate_port()
    def set_port(self, port: str, status: Literal["up", "down"], save_config=True) -> str:
        new_status = "enable" if status == "up" else "disable"

        if port.startswith("enet"):
            self.send_command(f"switch enet {new_status} {port}", expect_command=False)
        else:
            self.send_command(f"adsl {new_status} {port}", expect_command=False)

        self.lock = False
        result = f"port {port} set {status}"
        if save_config:
            self.lock = False
            saved = self.save_config()
            result += f" {saved}"
        return result

    @BaseDevice.lock_session
    def save_config(self) -> str:
        output = self.send_command("config save", expect_command=False)
        if "saving configuration to flash" in output:
            return self.SAVED_OK
        return self.SAVED_ERR

    @BaseDevice.lock_session
    @validate_port(if_invalid_return={"error": "Неверный порт", "status": "fail"})
    def set_description(self, port: str, desc: str) -> dict:
        desc = self.clear_description(desc)  # Очищаем описание

        if len(desc) > 31:
            return {
                "max_length": 31,
                "error": "Too long",
                "port": port,
                "status": "fail",
            }

        if port.isdigit():
            self.send_command(f'adsl name {port} "{desc}"', expect_command=False)
        else:
            self.send_command(f'switch enet name {port} "{desc}"', expect_command=False)

        self.lock = False
        return {
            "description": desc,
            "port": port,
            "status": "changed" if desc else "cleared",
            "saved": self.save_config(),
        }

    @BaseDevice.lock_session
    @validate_port(if_invalid_return={"type": "error", "data": "Неверный порт"})
    def get_port_info(self, port: str) -> PortInfoType:
        if not port.isdigit():
            return {
                "type": "text",
                "data": "",
            }

        def color(val: int | float, s: str) -> str:
            """Определяем цвета в зависимости от числовых значений показателя"""
            if "margin" in s:
                gradient = [5, 7, 10, 20]
            elif "attenuation" in s:
                gradient = [-60, -50, -40, -20]
                val = -val
            else:
                return ""
            # проверяем значения по градиенту
            if val <= gradient[0]:
                return "#e55d22"
            if val <= gradient[1]:
                return "#e5a522"
            if val <= gradient[2]:
                return "#dde522"
            if val <= gradient[3]:
                return "#95e522"

            return "#22e536"  # зеленый

        port_info = self.send_command(f"adsl show {port}", expect_command=False)
        output = self.send_command(f"statistics adsl linerate {port}", expect_command=False)

        # Rate (kbps)
        downstream_rate = int(self.find_or_empty(r"downstream\s+rate\s+\(kbps\):\s+(\d+)", output) or 0)
        upstream_rate = int(self.find_or_empty(r"upstream\s+rate\s+\(kbps\):\s+(\d+)", output) or 0)
        rate_element = {
            "name": "Rate (kbps)",
            "down": {"color": color(downstream_rate, "rate"), "value": downstream_rate},
            "up": {"color": color(upstream_rate, "rate"), "value": upstream_rate},
        }

        # Attainable stream rate (kbps)
        downstream_attainable = int(
            self.find_or_empty(r"attainable\s+down\/up\s+stream\s+rate\s+\(kbps\):\s+(\d+)\/\s+\d+", output)
            or 0
        )
        upstream_attainable = int(
            self.find_or_empty(r"attainable\s+down\/up\s+stream\s+rate\s+\(kbps\):\s+\d+\/\s+(\d+)", output)
            or 0
        )
        attainable_element = {
            "name": "Attainable stream rate (kbps)",
            "down": {"color": color(downstream_attainable, "attainable"), "value": downstream_attainable},
            "up": {"color": color(upstream_attainable, "attainable"), "value": upstream_attainable},
        }

        # Stream margin (db)
        downstream_margin = float(
            self.find_or_empty(r"down\/up\s+stream\s+margin\s+\(db\):\s+(\d+\.\d+)\/\s*\d+\.\d+", output) or 0
        )
        upstream_margin = float(
            self.find_or_empty(r"down\/up\s+stream\s+margin\s+\(db\):\s+\d+\.\d+\/\s*(\d+\.\d+)", output) or 0
        )
        stream_margin_element = {
            "name": "Stream margin (db)",
            "down": {"color": color(downstream_margin, "margin"), "value": downstream_margin},
            "up": {"color": color(upstream_margin, "margin"), "value": upstream_margin},
        }

        # Stream attenuation (db)
        downstream_attenuation = float(
            self.find_or_empty(r"down\/up\s+stream\s+attenuation\s+\(db\):\s+(\d+\.\d+)\/\s*\d+\.\d+", output)
            or 0
        )
        upstream_attenuation = float(
            self.find_or_empty(r"down\/up\s+stream\s+attenuation\s+\(db\):\s+\d+\.\d+\/\s*(\d+\.\d+)", output)
            or 0
        )
        stream_attenuation_element = {
            "name": "Stream attenuation (db)",
            "down": {"color": color(downstream_attenuation, "attenuation"), "value": downstream_attenuation},
            "up": {"color": color(upstream_attenuation, "attenuation"), "value": upstream_attenuation},
        }
        table_dict = [rate_element, attainable_element, stream_margin_element, stream_attenuation_element]

        profiles_output = self.send_command("adsl profile show", expect_command=False)
        all_profiles = re.findall(r"(\d+)\.\s+(\S+)", profiles_output)

        profile_name = self.find_or_empty(r"\d+\s+\S+\s+\S+\s+\d+/\s*\d+\s+(\S+)", port_info)

        return {
            "type": "adsl",
            "data": {
                "profile_name": profile_name,
                "port": port,
                "first_col": port_info.splitlines(),
                "streams": table_dict,
                "profiles": all_profiles,
            },
        }

    @validate_port(if_invalid_return="?")
    def get_port_type(self, port: str) -> str:
        if port.isdigit():  # Для ADSL портов
            return "COPPER"

        if "copper" in self.port_type_map.get(port, ""):
            return "COPPER"
        return "?"

    def get_port_config(self, port: str) -> str:
        return ""

    def get_port_errors(self, port: str) -> str:
        return ""

    def get_device_info(self) -> dict:
        return {}


class ZyxelFactory(AbstractDeviceFactory):
    @staticmethod
    def is_can_use_this_factory(session=None, version_output=None) -> bool:
        check_sentences = ["invalid command, valid commands are", "adsl", "switch"]
        output = str(version_output)
        return version_output and all(map(lambda s: s in output, check_sentences))

    @classmethod
    def get_device(
        cls,
        session,
        ip: str,
        snmp_community: str,
        auth: DeviceAuthDict,
        version_output: str = "",
    ) -> BaseDevice:
        return Zyxel(session, ip, auth, snmp_community=snmp_community)
