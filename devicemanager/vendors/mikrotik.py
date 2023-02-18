import re
import time

import pexpect
from functools import wraps
from django.template.loader import render_to_string
from .base import (
    BaseDevice,
    InterfaceList,
    InterfaceVLANList,
    MACList,
)


class MikroTik(BaseDevice):
    prompt = r"\] > $"
    space_prompt = None
    mac_format = r"\S\S:\S\S:\S\S:\S\S:\S\S:\S\S"
    vendor = "MikroTik"

    def __init__(self, session: pexpect, ip: str, auth: dict, model):
        super().__init__(session, ip, auth, model)

        # {"bridge_name": {"vlans": ['10', '20']}}
        self._bridges = {}

        # {"vlan10": '10', "vlan20": '20'}
        self._vlans_interfaces = {}

        # {"ether1": {"bridge": "bridge_name"}, "ether2": {"bridge": "bridge_name"}}
        self._ether_interfaces = {}

        self._get_vlans_bridges()
        self._get_bridges_interfaces()

    def _get_vlans_bridges(self):
        output = self.send_command("interface vlan print detail terse")

        for line in re.split(r"(?<=\S)\s*(?=\d+\s+[RX]*\s+)", output):
            line = re.sub(r"\r\n", "", line)
            match = BaseDevice.find_or_empty(
                r"\d+\s+R*\s+name=(\S+) .+vlan-id=(\d+) interface=(\S+)", line
            )
            if not match:
                continue
            vlan_name, vlan_id, bridge_name = match
            self._vlans_interfaces[vlan_name] = vlan_id
            if not self._bridges.get(bridge_name):
                self._bridges[bridge_name] = {"vlans": [vlan_id]}
            else:
                self._bridges[bridge_name]["vlans"].append(vlan_id)

    def _get_bridges_interfaces(self):
        output = self.send_command("interface bridge port print terse")

        for line in re.split(r"\s*(?=\d+\s+[XIDH]*\s+interface)", output):
            line = re.sub(r"\r\n", "", line)

            match = BaseDevice.find_or_empty(
                r"\d+\s+[XIDH]*\s+interface=(\S+) bridge=(\S+)", line
            )
            if not match:
                continue

            interface_name, bridge_name = match
            if not self._vlans_interfaces.get(interface_name):
                self._ether_interfaces[interface_name] = {"bridge": bridge_name}
                continue

            if not self._bridges.get(bridge_name):
                self._bridges[bridge_name] = {"vlans": []}
            self._bridges.get(bridge_name)["vlans"].append(
                self._vlans_interfaces.get(interface_name)
            )

    def send_command(
        self,
        command: str,
        before_catch: str = None,
        expect_command=True,
        num_of_expect=10,
        space_prompt=None,
        prompt=None,
        pages_limit=None,
        command_linesep="\r",
    ) -> str:
        return super().send_command(
            command,
            before_catch,
            expect_command,
            num_of_expect,
            space_prompt,
            prompt,
            pages_limit,
            command_linesep,
        )

    def _validate_port(self=None, if_invalid_return=None):
        """
        ## Декоратор для проверки правильности порта MikroTik

            Разрешенные:

              ether4
              sfp1
              sfp-sfpplus1

        :param if_invalid_return: что нужно вернуть, если порт неверный
        """

        if if_invalid_return is None:
            if_invalid_return = "Неверный порт"

        def validate(func):
            @wraps(func)
            def __wrapper(self, port, *args, **kwargs):
                if not BaseDevice.find_or_empty(
                    r"^ether\d+|sfp\d+|sfp-sfpplus\d+$", port
                ):
                    # Неверный порт
                    return if_invalid_return

                # Вызываем метод
                return func(self, port, *args, **kwargs)

            return __wrapper

        return validate

    @BaseDevice._lock
    def get_interfaces(self) -> InterfaceList:
        interfaces_output = self.send_command("interface print without-paging terse")

        interfaces = []

        for line in re.split(r"(?=\S)\s*(?=\d+\s+[DRSX]*\s+)", interfaces_output):

            line = re.sub(r"\r\n", "", line)
            match = re.match(r"^\s*(\d+)\s+([DRSX]*)\s+.+type=ether", line)

            if not match:
                continue

            flags = match.group(2)
            if "R" in flags:
                status = "up"
            elif "X" in flags:
                status = "admin down"
            else:
                status = "down"

            description = BaseDevice.find_or_empty(r"comment=(.+)\s+name=", line)

            interface_name = BaseDevice.find_or_empty(r"default-name=(\S+)\s+", line)
            interfaces.append((interface_name, status, description))

        return interfaces

    @BaseDevice._lock
    def get_vlans(self) -> InterfaceVLANList:
        interfaces_with_vlans = []

        self.lock = False
        interfaces = self.get_interfaces()
        self.lock = True

        for line in interfaces:
            bridge_name = self._ether_interfaces[line[0]]["bridge"]
            interfaces_with_vlans.append(
                (
                    line[0],
                    line[1],
                    line[2],
                    self._bridges[bridge_name]["vlans"],
                )
            )
        return interfaces_with_vlans

    @BaseDevice._lock
    @_validate_port(if_invalid_return=[])
    def get_mac(self, port: str) -> MACList:
        """
        ## Возвращаем список из VLAN и MAC-адреса для данного порта.

        Команда на оборудовании:

            # show mac address-table interface {port}

        :param port: Номер порта коммутатора
        :return: ```[ ('vid', 'mac'), ... ]```
        """

        output = self.send_command(
            f"interface bridge host print terse where interface={port} !local"
        )

        macs = []
        for line in re.split(r"(?<=\s)(?=\d+\s+[XIDE]*\s+)", output):
            line = re.sub(r"\r\n", "", line)
            mac_line = BaseDevice.find_or_empty(
                rf"mac-address=({self.mac_format}) .* bridge=(\S+)", line
            )
            if not mac_line:
                continue
            mac_address, bridge = mac_line
            macs.append((self._bridges[bridge]["vlans"][0], mac_address))

        return macs

    @BaseDevice._lock
    @_validate_port()
    def reload_port(self, port: str, save_config=True) -> str:
        self.send_command(f"interface disable {port}")
        time.sleep(2)
        self.send_command(f"interface enable {port}")
        return self.SAVED_OK

    @BaseDevice._lock
    @_validate_port()
    def set_port(self, port: str, status: str, save_config=True) -> str:

        if status == "up":
            self.send_command(f"interface enable {port}")
        elif status == "down":
            self.send_command(f"interface disable {port}")
        return self.SAVED_OK

    def save_config(self):
        """Автоматическое сохранение на Mikrotik"""

    @BaseDevice._lock
    @_validate_port()
    def set_description(self, port: str, desc: str) -> str:

        # Очищаем описание от запрещенных символов
        desc = self.clear_description(desc)

        if desc == "":
            # Очищаем описание
            self.send_command(f'interface comment {port} comment=""')

        else:
            # Устанавливаем описание
            self.send_command(f'interface comment {port} comment="{desc}"')

        return (
            f'Description has been {"changed" if desc else "cleared"}. {self.SAVED_OK}'
        )

    @BaseDevice._lock
    @_validate_port()
    def get_port_info(self, port: str) -> str:
        raw_poe_info = self.send_command(
            f"interface ethernet poe print terse where name={port}"
        )
        raw_poe_info = re.sub(r"\r\n", "", raw_poe_info)
        poe_info = self.find_or_empty("poe-out=(auto-on|forced-on|off)", raw_poe_info)
        return ""

    @BaseDevice._lock
    @_validate_port()
    def set_poe_out(self, port: str, status: str) -> bool:
        output = self.send_command(
            f"interface ethernet poe set {port} poe-out={status}"
        )
        output = re.sub(r"\r\n", "", output)
        return "no such item" not in output and "syntax error" not in output

    def get_port_type(self, port: str) -> str:
        pass

    def get_port_config(self, port: str) -> str:
        pass

    def get_port_errors(self, port: str) -> str:
        pass

    def get_device_info(self) -> dict:
        pass
