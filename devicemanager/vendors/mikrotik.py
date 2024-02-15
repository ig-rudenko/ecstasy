import os
import pathlib
import re
import time
from datetime import datetime
from functools import partial
from typing import Literal

import pysftp

from .base.device import BaseDevice
from .base.factory import AbstractDeviceFactory
from .base.types import (
    T_InterfaceList,
    T_InterfaceVLANList,
    T_MACList,
    T_MACTable,
    MACType,
    DeviceAuthDict,
    T_Interface,
)
from .base.validators import validate_and_format_port
from ..exceptions import UnknownDeviceError


def validate_port(port: str) -> str | None:
    """
    ## Проверка правильности порта MikroTik.

    Разрешенные:
     - ether4
     - sfp1
     - sfp-sfpplus1
     - wlan2
     - wlan60-station-1
    """
    port = port.lower()
    if re.match(r"^ether|^sfp|^wlan", port):
        return port
    return None


# Создаем свой декоратор для проверки портов
mikrotik_validate_and_format_port = partial(validate_and_format_port, validator=validate_port)


class MikroTik(BaseDevice):
    prompt = r"\] > $"
    space_prompt = None
    mac_format = r"\S\S:\S\S:\S\S:\S\S:\S\S:\S\S"
    vendor = "MikroTik"

    def __init__(
        self,
        session,
        ip: str,
        auth: DeviceAuthDict,
        model: str = "",
        snmp_community: str = "",
    ):
        super().__init__(session, ip, auth, model, snmp_community)
        routerboard = self.send_command("system routerboard print")
        self.model = self.find_or_empty(r"model: (\S+)", routerboard)

        # {"bridge_name": {"vlans": ['10', '20']}}
        self._bridges: dict[str, dict[str, list[str]]] = {}

        # {"vlan10": '10', "vlan20": '20'}
        self._vlans_interfaces: dict[str, str] = {}

        # {"ether1": {"bridge": "bridge_name"}, "ether2": {"bridge": "bridge_name"}}
        self._ether_interfaces: dict[str, dict[str, str]] = {}

        self._get_vlans_bridges()
        self._get_bridges_interfaces()

    def _get_vlans_bridges(self) -> None:
        output = self.send_command("interface vlan print detail terse")

        for line in re.split(r"(?<=\S)\s*(?=\d+\s+[RX]*\s+)", output):
            line = line.replace("\r\n", "")

            match: list[tuple[str, str, str]] = re.findall(
                r"\d+\s+R*\s+name=(\S+) .+vlan-id=(\d+) interface=(\S+)", line
            )
            if not match:
                continue
            vlan_name, vlan_id, bridge_name = match[0]

            # {"vlan10": '10'}
            self._vlans_interfaces[vlan_name] = vlan_id

            # {"bridge_name": {"vlans": ['10', '20']}}
            if not self._bridges.get(bridge_name):
                self._bridges[bridge_name] = {"vlans": [vlan_id]}
            else:
                self._bridges[bridge_name]["vlans"].append(vlan_id)

    def _get_bridges_interfaces(self) -> None:
        output = self.send_command("interface bridge port print terse")

        for line in re.split(r"\s*(?=\d+\s+[XIDH]*\s+(interface|comment))", output):
            line = line.replace("\r\n", "")

            match: list[tuple[str, str]] = re.findall(
                r"\d+\s+[XIDH]*\s+\S*\s*interface=(\S+) bridge=(\S+)", line
            )
            if not match:
                continue

            interface_name, bridge_name = match[0]

            # {"<interface_name>": '10', "vlan20": '20'}
            if not self._vlans_interfaces.get(interface_name):
                # {"<interface_name>": {"bridge": "bridge_name"} }
                self._ether_interfaces[interface_name] = {"bridge": bridge_name}

            else:
                # {"<bridge_name>": {"vlans": ['10', '20']}}
                if not self._bridges.get(bridge_name):
                    self._bridges[bridge_name] = {"vlans": []}
                self._bridges[bridge_name]["vlans"].append(self._vlans_interfaces[interface_name])

    def send_command(
        self,
        command: str,
        before_catch: str | None = None,
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

    @BaseDevice.lock_session
    def get_interfaces(self) -> T_InterfaceList:
        interfaces_output = self.send_command("interface print without-paging terse")

        interfaces = []

        for line in re.split(r"(?=\S)\s*(?=\d+\s+[DRSX]*\s+)", interfaces_output):
            line = line.replace("\r\n", "")
            match = re.match(r"^\s*(\d+)\s+([DRSX]*)\s+.+type=(ether|wlan)", line)

            if not match:
                continue

            flags = match.group(2)
            status: T_Interface = "down"
            if "R" in flags:
                status = "up"
            elif "X" in flags:
                status = "admin down"

            description = BaseDevice.find_or_empty(r"comment=(.+)\s+name=", line)

            interface_name = BaseDevice.find_or_empty(r" name=(\S+)", line)
            interfaces.append((interface_name, status, description))

        return interfaces

    @BaseDevice.lock_session
    def get_vlans(self) -> T_InterfaceVLANList:
        interfaces_with_vlans = []

        self.lock = False
        interfaces: T_InterfaceList = self.get_interfaces()
        self.lock = True
        for line in interfaces:
            bridge_name = self._ether_interfaces.get(line[0], {}).get("bridge", "")
            bridge = self._bridges.get(bridge_name, {"vlans": []})
            vlans_list = bridge.get("vlans", [])
            interfaces_with_vlans.append(
                (
                    line[0],
                    line[1],
                    line[2],
                    vlans_list,
                )
            )
        return interfaces_with_vlans

    @BaseDevice.lock_session
    def get_mac_table(self) -> T_MACTable:
        """

        ## Возвращаем список из VLAN, MAC-адреса, MAC-type и порта для данного оборудования.

        Команда на оборудовании:

            [@] > interface bridge host print without-paging terse

            339   DL  mac-address=CC:2D:E0:AC:58:DA interface=vlan1051 bridge=bridge1051 on-interface=vlan1051
            166   D   mac-address=F0:23:B9:30:C0:FE interface=ether1 bridge=T_bridge on-interface=ether1 age=6s
            167   DL  mac-address=DE:5A:07:A2:68:72 interface=bridge bridge=bridge on-interface=bridge
            168   D   mac-address=00:04:96:51:E8:CF interface=vlan3738 bridge=bridge3738 on-interface=vlan3738 age=5s

        :return: ```[ ('{vid}', '{mac}', {'dynamic'|'static'}, '{port}'), ... ]```
        """

        output = self.send_command("interface bridge host print without-paging terse", expect_command=False)

        mac_table: T_MACTable = []

        # Разбиваем вывод на строки, начинающиеся с числа и пробела.
        for line in re.split(r"(?<=\s)(?=\d+\s+[XIDE]*\s+)", output):
            # Удаление символов новой строки.
            line = line.replace("\r\n", "")

            # Находим необходимые элементы в строке
            parsed: list[tuple[str, str, str, str]] = re.findall(
                r"\d+\s+(DL?)\s+mac-address=(\S+) .* bridge=(\S+) .*on-interface=(\S+).*",
                line,
            )
            # Если не нашли элементы.
            if not parsed:
                continue

            # Распаковка кортежа, возвращенного `re.findall`.
            type_, mac, bridge, port = parsed[0]

            # Получение идентификатора vlan моста.
            vid = self._bridges.get(bridge, {}).get("vlans", ["0"])[0]

            mac_type: MACType
            if type_ == "D":
                mac_type = "dynamic"
            elif type_ == "DL":
                mac_type = "static"
            else:
                mac_type = "security"

            # Добавление MAC в таблицу
            mac_table.append((int(vid), mac, mac_type, port))

        return mac_table

    @BaseDevice.lock_session
    @mikrotik_validate_and_format_port(if_invalid_return=[])
    def get_mac(self, port: str) -> T_MACList:
        """
        ## Возвращаем список из VLAN и MAC-адреса для данного порта.

        Команда на оборудовании:

            # show mac address-table interface {port}

        :param port: Номер порта коммутатора
        :return: ```[ ('vid', 'mac'), ... ]```
        """

        output = self.send_command(
            f'interface bridge host print terse where interface="{port}" !local',
            expect_command=False,
        )

        macs: T_MACList = []
        # Приведенный выше код разбивает строку `output` на строки на основе шаблона регулярного выражения.
        # Затем для каждой строки он ищет MAC-адрес и соответствующий `bridge`, используя шаблон регулярного выражения.
        # Если MAC-адрес и `bridge` найдены, он добавляет кортеж из VLAN ID и MAC-адреса в список под названием «macs».
        # Идентификатор VLAN получается из словаря под названием «_bridges», используя имя `bridge` в качестве ключа.
        for line in re.split(r"(?<=\s)(?=\d+\s+[XIDE]*\s+)", output):
            line = line.replace("\r\n", "")
            mac_line: tuple[str, str] = BaseDevice.find_or_empty(
                rf"mac-address=({self.mac_format}) .* bridge=(\S+)", line
            )
            if not mac_line:
                continue
            mac_address, bridge_name = mac_line
            bridge = self._bridges.get(bridge_name, {})
            vlan: str = bridge.get("vlans", ["1"])[0]
            macs.append((int(vlan), mac_address))
        return macs

    @BaseDevice.lock_session
    @mikrotik_validate_and_format_port()
    def reload_port(self, port: str, save_config=True) -> str:
        self.send_command(f'interface disable "{port}"')
        time.sleep(2)
        self.send_command(f'interface enable "{port}"')
        return self.SAVED_OK

    @BaseDevice.lock_session
    @mikrotik_validate_and_format_port()
    def set_port(self, port: str, status: Literal["up", "down"], save_config=True) -> str:
        if status == "up":
            self.send_command(f'interface enable "{port}"')
        elif status == "down":
            self.send_command(f'interface disable "{port}"')
        return self.SAVED_OK

    def save_config(self):
        """Автоматическое сохранение на Mikrotik"""

    @BaseDevice.lock_session
    @mikrotik_validate_and_format_port(if_invalid_return={"error": "Неверный порт", "status": "fail"})
    def set_description(self, port: str, desc: str) -> dict:
        # Очищаем описание от запрещенных символов
        desc = self.clear_description(desc)

        if desc == "":
            # Очищаем описание
            self.send_command(f'interface comment "{port}" comment=""')

        else:
            # Устанавливаем описание
            self.send_command(f'interface comment "{port}" comment="{desc}"')

        return {
            "description": desc,
            "port": port,
            "status": "changed" if desc else "cleared",
            "saved": self.SAVED_OK,
        }

    @BaseDevice.lock_session
    @mikrotik_validate_and_format_port()
    def get_port_info(self, port: str) -> dict:
        data = {}

        raw_poe_info = self.send_command(f'interface ethernet poe print terse where name="{port}"')
        raw_poe_info = raw_poe_info.replace("\r\n", "")
        data["poeStatus"] = self.find_or_empty("poe-out=(auto-on|forced-on|off)", raw_poe_info)
        data["poeChoices"] = ["auto-on", "forced-on", "off"]

        return {
            "type": "mikrotik",
            "data": data,
        }

    @BaseDevice.lock_session
    @mikrotik_validate_and_format_port()
    def set_poe_out(self, port: str, status: str) -> tuple:
        output = self.send_command(f'interface ethernet poe set "{port}" poe-out={status}')
        output = output.replace("\r\n", "")
        return status, "no such item" in output or "syntax error" in output

    @mikrotik_validate_and_format_port(if_invalid_return="?")
    def get_port_type(self, port: str) -> str:
        if "sfp" in port.lower():
            return "SFP"
        if "wlan" in port.lower():
            return "WIRELESS"
        return "COPPER"

    def get_port_config(self, port: str) -> str:
        return ""

    def get_port_errors(self, port: str) -> str:
        return ""

    def get_device_info(self) -> dict:
        return {}

    def get_current_configuration(self) -> pathlib.Path:
        local_folder_path = pathlib.Path(os.getenv("CONFIG_FOLDER_PATH", "temp_configs"))

        config_file_name = f"backup_{datetime.now().strftime('%H:%M-%d.%m.%Y')}"

        self.send_command(f"system backup save dont-encrypt=yes name={config_file_name}")

        config_file_name += ".backup"

        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None

        with pysftp.Connection(
            host=self.ip,
            username=self.auth["login"],
            password=self.auth["password"],
            cnopts=cnopts,
        ) as session:
            path = str((local_folder_path / config_file_name).absolute())
            # Приведенный выше код создает резервную копию файла конфигурации.
            session.get(config_file_name, path)

        self.send_command(f"file remove {config_file_name}")

        return local_folder_path / config_file_name


class MikrotikFactory(AbstractDeviceFactory):
    @staticmethod
    def is_can_use_this_factory(session=None, version_output=None) -> bool:
        return version_output and "bad command name show" in str(version_output).lower()

    @classmethod
    def get_device(
        cls,
        session,
        ip: str,
        snmp_community: str,
        auth: DeviceAuthDict,
        version_output: str = "",
    ) -> BaseDevice:
        version_output = cls.send_command(session, "system resource print")
        if "mikrotik" in str(version_output).lower():
            return MikroTik(session, ip, auth, snmp_community=snmp_community)

        raise UnknownDeviceError("MikrotikFactory не удалось распознать модель оборудования", ip=ip)
