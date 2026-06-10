import re

from devicemanager.vendors.base.device import BaseDevice
from devicemanager.vendors.base.types import (
    ArpInfoResult,
    InterfaceListType,
    InterfaceType,
    MACListType,
    MACTableType,
    MACType,
    VlanTableType,
)
from devicemanager.vendors.snr.vlan_parser import VlanInfo

from .snr_s52xx import SNRS52XX


class SNRS29XX(SNRS52XX):
    """
    # Для оборудования от производителя SNR

    - snr s29xx
    """

    prompt = r"\S+#$"
    space_prompt = "--More--"
    mac_format = r"\S\S-\S\S\-\S\S-\S\S\-\S\S-\S\S"
    vendor = "SNR"

    @BaseDevice.lock_session
    def save_config(self):
        """
        Сохраняем конфигурацию оборудования командой:
            # write
        """
        self.session.sendline("write")
        self.session.expect("Y/N")
        self.session.sendline("Y")
        self.session.expect(self.prompt)
        return self.SAVED_OK

    @BaseDevice.lock_session
    def get_interfaces(self) -> InterfaceListType:
        """
        ## Возвращаем список всех интерфейсов на устройстве

        Команда на оборудовании:

            # show interface description

        :return: ```[ ('name', 'status', 'desc'), ... ]```
        """

        output = self.send_command("show interface status", expect_command=False)

        result: list[tuple[str, str, str, str]] = re.findall(
            r"(?P<name>\S+)\s+(?P<admin_status>UP|DOWN|A-DOWN|E-DOWN)/(?P<link_status>UP|DOWN|A-DOWN|E-DOWN)"
            r"\s+\S+\s+\S+\s+\S*\s+\S+(?P<desc>.*)",
            output,
            flags=re.MULTILINE,
        )

        interfaces = []
        for port_name, admin_status, link_status, desc in result:
            status: InterfaceType = "up"
            if admin_status == "A-DOWN":
                status = "admin down"
            elif "down" in link_status.lower():
                status = "down"

            interfaces.append((port_name, status, desc.strip()))

        return interfaces

    @BaseDevice.lock_session
    def get_vlan_table(self) -> VlanTableType:
        vlan_output = self.send_command("show vlan")

        def parse_ports(text: str) -> list[str]:
            return re.findall(r"(\S+\d)", text)

        vlans: list[VlanInfo] = []
        current_vlan: None | VlanInfo = None
        for line in vlan_output.splitlines():

            line_match = re.search(r"(?P<vid>\d+)\s+(?P<name>\S+)\s+\S+\s+\S+\s+(?P<ports>.+)", line)
            if not line_match and not current_vlan:
                continue

            if line_match:
                vlan: VlanInfo = {
                    "vlan_id": int(line_match.group("vid")),
                    "name": line_match.group("name").strip(),
                    "ports": parse_ports(line_match.group("ports")),
                }
                current_vlan = vlan
                vlans.append(vlan)
                continue

            if current_vlan:
                current_vlan["ports"].extend(parse_ports(line))
                continue

        return [(line["vlan_id"], line["ports"], line["name"]) for line in vlans]

    def _get_interfaces_config(self) -> dict[str, str]:
        output = self.send_command("show running-config", expect_command=False)
        interfaces_config: dict[str, str] = {}
        for line in re.findall(r"interface\s+\S+\d.+?!(?=\r?\n)", output, flags=re.DOTALL | re.IGNORECASE):
            if interface_name := re.match(r"^interface\s+(\S+)", line, flags=re.IGNORECASE):
                interfaces_config[self.normalize_interface_name(interface_name.group(1))] = line
        return interfaces_config

    @BaseDevice.lock_session
    def get_mac(self, port) -> MACListType:
        """
        ## Возвращаем список из VLAN и MAC-адреса для данного порта.

        Команда на оборудовании:

            # show mac-address-table interface {port}

        :param port: Номер порта коммутатора
        :return: ```[ ('vid', 'mac'), ... ]```
        """

        mac_str = self.send_command(
            f"show mac-address-table interface {port}",
            expect_command=False,
        )
        macs_list: list[tuple[str, str]] = re.findall(
            rf"(?P<vid>\d+)\s+({self.mac_format})\s+\S+\s+\S+", mac_str
        )
        return [(int(vid), mac) for vid, mac in macs_list]

    @BaseDevice.lock_session
    def get_mac_table(self) -> MACTableType:
        """
        ## Возвращаем список из VLAN, MAC-адреса, dynamic и порта для данного оборудования.

        Команда на оборудовании:

            # show mac-address-table

        :return: ```[ ({int:vid}, '{mac}', 'dynamic', '{port}'), ... ]```
        """

        def mac_type(type_: str) -> MACType:
            type_ = type_.lower()
            if type_ == "dynamic":
                return "dynamic"
            if type_ == "static":
                return "static"
            return "security"

        mac_str = self.send_command("show mac-address-table", expect_command=False)
        mac_table: list[tuple[str, str, str, str]] = re.findall(
            rf"(?P<vid>\d+)\s+({self.mac_format})\s+(dynamic|static)\s+\S+\s+(?P<port>\S+)",
            mac_str,
            flags=re.IGNORECASE,
        )
        return [(int(vid), mac, mac_type(type_), port) for vid, mac, type_, port in mac_table]

    def _search_in_arp(self, address: str) -> list[ArpInfoResult]:
        arp_output = self.send_command(f"show arp | include {address}", expect_command=False)
        parsed: list[tuple[str, str, str, str]] = re.findall(
            rf"(?P<ip>\d\S+\d)\s+({self.mac_format})\s+vlan(?P<vid>\d+)\s+(?P<port>\S+)", arp_output
        )

        return [ArpInfoResult(ip=ip, mac=mac, vlan=vlan, port=port) for ip, mac, vlan, port in parsed]

    @BaseDevice.lock_session
    def get_device_info(self) -> dict:
        return {
            "cpu": {"util": self._get_cpu_utilization()},
            "ram": {},
            "flash": {"util": self._get_flash_utilization()},
            "temp": self._get_temp(),
        }

    def _get_cpu_utilization(self) -> tuple:
        """
        ## Возвращает загрузку ЦП хоста
        """

        cpu_percent = re.findall(
            r"Last\s+5\s+minute\s+CPU\s+usage:\s+(\d+)%",
            self.send_command("show cpu utilization", expect_command=False),
            flags=re.IGNORECASE,
        )

        return tuple(map(int, cpu_percent))

    def _get_flash_utilization(self) -> int:
        """
        ## Возвращает использование флэш-памяти устройства
        """

        flash = self.find_or_empty(
            r"Use:(\d+)%",
            self.send_command("show flash", expect_command=False),
            flags=re.IGNORECASE,
        )

        return int(flash) if flash else -1
