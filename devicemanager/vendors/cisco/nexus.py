import io
import re

import pexpect

from .. import BaseDevice
from ..base.types import (
    COOPER_TYPES,
    FIBER_TYPES,
    ArpInfoResult,
    DeviceAuthDict,
    InterfaceListType,
    InterfaceType,
    VlanTableType,
)
from ..base.validators import validate_and_format_port_as_normal
from .basic import Cisco
from .helpers import parse_nexus_cpu_utilization, parse_nexus_flash_usage_percent, parse_nexus_ram_utilization


class CiscoNexus(Cisco):
    prompt = r"\S+# $"
    space_prompt = "--More--"

    def __init__(
        self,
        session,
        ip: str,
        auth: DeviceAuthDict,
        model: str = "",
        snmp_community: str = "",
    ):
        super().__init__(session, ip, auth, model, snmp_community)

        inventory = self.send_command("show inventory", expect_command=False)
        inventory_match = re.search(
            r"Nexus.+?PID:\s+(?P<model>\S+).+?SN:\s+(?P<sn>\S+)", inventory, re.DOTALL
        )
        if inventory_match:
            self.serialno = inventory_match.group("sn")
            self.model = inventory_match.group("model")

    @BaseDevice.lock_session
    def save_config(self):
        """
        ## Сохраняем конфигурацию оборудования командой:

            # copy running-config startup-config

        Ожидаем ответа от оборудования **complete**,
        если нет, то пробуем еще 2 раза, в противном случае ошибка сохранения
        """

        for _ in range(3):  # Пробуем 3 раза, если ошибка
            self.session.sendline("copy running-config startup-config")
            if self.session.expect([self.prompt, "complete", pexpect.TIMEOUT], timeout=10):
                self.session.expect(self.prompt)
                return self.SAVED_OK
        return self.SAVED_ERR

    @BaseDevice.lock_session
    def get_interfaces(self) -> InterfaceListType:
        """
        ## Возвращаем список всех интерфейсов на устройстве

        Команда на оборудовании:

            # show interfaces description

        :return: ```[ ('name', 'status', 'desc'), ... ]```
        """

        output = self.send_command("show interface description", expect_command=False)
        # { "Eth1/0/1": "description" }
        interfaces_desc: dict[str, str] = {
            line[0]: line[1] for line in re.findall(r"(\S+\d)\s+\S+\s+\d\S+\s+(\S*)", output)
        }

        output = self.send_command("show interface brief", expect_command=False)
        interfaces_status: list[tuple[str, str, str]] = re.findall(
            r"(\S+\d)\s+\S+\s+\S+\s+\S+\s+(up|down)\s+(.+?)\s+\S+\(\S+\s+\S+", output
        )

        interfaces = []
        for port_name, link_status, admin_status in interfaces_status:
            status: InterfaceType = "up"
            if admin_status.lower() == "administratively down":
                status = "admin down"
            elif "down" in link_status.lower():
                status = "down"

            interfaces.append((port_name, status, interfaces_desc.get(port_name, "")))

        return interfaces

    def _get_interfaces_config(self) -> dict[str, str]:
        output = self.send_command("show running-config", expect_command=False)
        interfaces_config: dict[str, str] = {}
        for line in re.findall(r"interface\s+\S+\d.+?(?=\n\S)", output, flags=re.DOTALL):
            if interface_name := re.match(r"^interface\s+(\S+)", line):
                interfaces_config[self.normalize_interface_name(interface_name.group(1))] = line
        return interfaces_config

    @BaseDevice.lock_session
    def get_vlan_table(self) -> VlanTableType:
        output = self.send_command("show vlan brief", expect_command=False)
        parsed: list[tuple[str, str, str]] = re.findall(
            r"^\s*(?P<vid>\d+)\s+(?P<name>\S+)\s+\S+(?P<ports>\n|\s+.*?(?=\n\r?\S|\n\r?\n\r?))",
            output,
            flags=re.DOTALL | re.MULTILINE,
        )

        result: VlanTableType = []
        for vid, name, ports in parsed:
            result.append((int(vid), re.sub(r",?\s+", ",", ports.strip()).split(","), name))

        return result

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal()
    def get_port_type(self, port: str) -> str:
        """
        Возвращает тип порта.
        Тип порта определяется по стандарту IEE 802.3.

        Обозначения медных типов:
            - T, TX, VG, CX, CR

        Обозначения оптоволоконных типов:
            - FOIRL, F, FX, SX, LX, BX, EX, ZX, SR, ER, SW, LW, EW, LRM, PR, LR, ER, FR, LH

        Не определено:
            - media type is unsupported
            - media type is Not Present
            - media type is unknown media type

        :param port: Порт для проверки
        :return: "SFP", "COPPER" или "?"
        """

        # Получаем информацию о порте.
        port_capabilities = self.send_command(f"show interface {port} capabilities", expect_command=False)
        # Ищем тип порта.
        parsed = re.search(
            r"^\s+Type(?:\s\((?P<extra>.+?)\))?:\s+(?P<full_type>\S*BASE-?(?P<base>\S+)|.+)",
            port_capabilities,
            flags=re.MULTILINE | re.IGNORECASE,
        )
        if parsed is None:
            return "?"

        base = str(parsed.group("base"))
        if base in FIBER_TYPES + self.EXTRA_FIBER_TYPES:
            return "SFP"
        if base in COOPER_TYPES:
            return "COPPER"

        new_base_match = re.search(r"\d+(\w+)", parsed.group("full_type"))
        if new_base_match and new_base_match.group(1) in FIBER_TYPES + self.EXTRA_FIBER_TYPES:
            return "SFP"
        if new_base_match and new_base_match.group(1) in COOPER_TYPES:
            return "COPPER"

        if "No XCVR" in str(parsed.group("full_type")) or "SFP" in str(parsed.group("extra")):
            return "SFP"

        return "?"

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal()
    def get_port_config(self, port: str) -> str:
        """
        Выводим конфигурацию порта

        Используем команду:

            # show running-config interface {port}
        """

        output = self.send_command(
            f"show running-config interface {port}",
            expect_command=False,
            before_catch="!Time:",
        ).strip()

        if parsed := re.search(r"interface\s+\S+\d.+", output, flags=re.DOTALL):
            return parsed.group(0).strip()
        return output

    def _search_in_arp(self, address: str) -> list[ArpInfoResult]:
        output = self.send_command(f"show ip arp vrf all | include {address}", expect_command=False)
        parsed = re.findall(rf"(?P<ip>\d+\.\d+\.\d+\.\d+)s+\S+\s+(?P<mac>{self.mac_format})\s+\S+", output)

        result: list[ArpInfoResult] = []
        for ip, mac in parsed:
            vlan = "0"

            # В выводе нет VLAN информации, поэтому ищем отдельно
            if vlan_match := re.search(
                rf"(?P<vlan>\d+)\s+{mac}",
                self.send_command(f"show mac address-table {mac}", expect_command=False),
            ):
                vlan = vlan_match.group("vlan")

            result.append(ArpInfoResult(ip=ip, mac=mac, vlan=vlan))

        return result

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal(if_invalid_return={"error": "Неверный порт", "status": "fail"})
    def set_description(self, port: str, desc: str) -> dict:
        """
        ## Устанавливаем описание для порта предварительно очистив его от лишних символов

        Переходим в режим конфигурирования:

            # configure terminal

        Переходим к интерфейсу:

            (config)# interface {port}

        Если была передана пустая строка для описания, то очищаем с помощью команды:

            (config-if)# no description

        Если **desc** содержит описание, то используем команду для изменения:

            (config-if)# description {desc}

        Выходим из режима конфигурирования:

            (config-if)# end

        :param port: Порт, для которого вы хотите установить описание
        :param desc: Описание, которое вы хотите установить для порта
        :return: Вывод команды смены описания
        """

        desc = self.clear_description(desc)  # Очищаем описание от запрещённых символов.

        # Переходим к редактированию порта
        self.session.sendline("configure terminal")
        self.session.expect(self.prompt)
        self.session.sendline(f"interface {port}")
        self.session.expect(self.prompt)

        if desc == "":  # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            status = self.send_command("no description", expect_command=False)

        else:  # В другом случае, меняем описание на оборудовании
            status = self.send_command(f"description {desc}", expect_command=False)

        self.session.sendline("end")  # Выходим из режима редактирования
        self.session.expect(self.prompt)

        if "too long" in status:
            # Если длина описания больше чем доступно на оборудовании
            max_length = int(self.find_or_empty(r"max size allowed is (\d+)", status) or "32")
            return {
                "max_length": max_length,
                "error": "Too long",
                "port": port,
                "status": "fail",
            }

        self.lock = False

        if "error" in status:
            return {
                "status": "fail",
                "port": port,
                "error": "Invalid input detected",
            }

        return {
            "description": desc,
            "port": port,
            "status": "changed" if desc else "cleared",
            "saved": self.save_config(),
        }

    @BaseDevice.lock_session
    def get_device_info(self) -> dict:
        # Load average:   1 minute: 0.10   5 minutes: 0.17   15 minutes: 0.17
        # Processes   :   371 total, 1 running
        # CPU states  :   1.50% user,   5.00% kernel,   93.50% idle
        #         CPU0 states  :   1.00% user,   2.00% kernel,   97.00% idle
        #         CPU1 states  :   2.00% user,   8.00% kernel,   90.00% idle
        # Memory usage:   8253792K total,   1714476K used,   6539316K free
        resources_output = self.send_command("show system resources", expect_command=False)

        #        4096    Oct 27 18:48:12 2009  .patch/
        #                       ...
        #        4096    Oct 27 18:48:15 2009  virtual-instance/
        #
        # Usage for bootflash://sup-local
        #   858103808 bytes used
        #   792801280 bytes free
        #  1650905088 bytes total
        bootflash_output = self.send_command("dir bootflash:", expect_command=False)

        return {
            "cpu": {
                "util": parse_nexus_cpu_utilization(resources_output),
            },
            "ram": {
                "util": parse_nexus_ram_utilization(resources_output),
            },
            "flash": {
                "util": parse_nexus_flash_usage_percent(bootflash_output),
            },
            "temp": self._get_temp(),
        }

    def _get_temp(self) -> dict:
        # Temperature
        # -----------------------------------------------------------------
        # Module   Sensor     MajorThresh   MinorThres   CurTemp     Status
        #                     (Celsius)     (Celsius)    (Celsius)
        # -----------------------------------------------------------------
        # 1        Fan side   100           90           27          ok
        # 1        Outlet-1   100           90           67          ok
        # 1        Intake-0   100           90           54          ok
        # 1        Intake-1   100           90           60          ok
        # 1        Sunnyvale  125           100          48          ok
        # 1        Carmel-0   125           100          52          ok
        # 1        Carmel-1   125           100          42          ok
        # 1        Carmel-2   125           100          37          ok
        # 1        Port side  100           90           51          ok
        # 1        Control    58            53           27          ok
        output = self.send_command("show env temp", expect_command=False)
        parsed = re.search(r"Control\s+(?P<max>\d+)\s+(?P<min>\d+)\s+(?P<value>\d+)", output)
        if not parsed:
            return {}

        current_temp = int(parsed.group("value"))
        high_temp = int(parsed.group("max"))
        medium_temp = int(parsed.group("min"))
        low_temp = 0

        status = "normal"
        if current_temp >= high_temp:
            status = "high"
        elif current_temp >= medium_temp:
            status = "medium"
        elif current_temp <= low_temp:
            status = "low"

        return {"value": current_temp, "status": status}

    def _get_transceiver_diag(self, port: str) -> dict:
        output = self.send_command(f"show interface {port} transceiver detail", expect_command=False)
        parsed = re.search(
            r"Temperature\s+(?P<temp_value>\S+)\s.+\s(?P<temp_h_warn>-?\d+\.\d+)\s+C\s.+\s(?P<temp_l_warn>-?\d+\.\d+)\s+C.+?"
            r"Voltage\s+(?P<voltage_value>\S+)\s.+\s(?P<voltage_h_warn>-?\d+\.\d+)\s+V\s.+\s(?P<voltage_l_warn>-?\d+\.\d+)\s+V.+?"
            r"Current\s+(?P<curr_value>\S+)\s.+\s(?P<curr_h_warn>-?\d+\.\d+)\s+mA\s.+\s(?P<curr_l_warn>-?\d+\.\d+)\s+mA.+?"
            r"Tx Power\s+(?P<tx_value>\S+)\s.+\s(?P<tx_h_warn>-?\d+\.\d+)\s+dBm\s.+\s(?P<tx_l_warn>-?\d+\.\d+)\s+dBm.+?"
            r"Rx Power\s+(?P<rx_value>\S+)\s.+\s(?P<rx_h_warn>-?\d+\.\d+)\s+dBm\s.+\s(?P<rx_l_warn>-?\d+\.\d+)\s+dBm.+?",
            output,
            flags=re.DOTALL,
        )
        if not parsed:
            return {"len": "-", "status": "not supported"}

        return {
            "sfp": {
                "Temperature": {
                    "Current": parsed.group("temp_value"),
                    "High Warning": parsed.group("temp_h_warn"),
                    "Low Warning": parsed.group("temp_l_warn"),
                },
                "Voltage": {
                    "Current": parsed.group("voltage_value"),
                    "High Warning": parsed.group("voltage_h_warn"),
                    "Low Warning": parsed.group("voltage_l_warn"),
                },
                "Current": {
                    "Current": parsed.group("curr_value"),
                    "High Warning": parsed.group("curr_h_warn"),
                    "Low Warning": parsed.group("curr_l_warn"),
                },
                "RxPower": {
                    "Current": parsed.group("rx_value"),
                    "High Warning": parsed.group("rx_h_warn"),
                    "Low Warning": parsed.group("rx_l_warn"),
                },
                "TxPower": {
                    "Current": parsed.group("tx_value"),
                    "High Warning": parsed.group("tx_h_warn"),
                    "Low Warning": parsed.group("tx_l_warn"),
                },
            }
        }

    @BaseDevice.lock_session
    def get_current_configuration(self) -> io.BytesIO:
        data = self.send_command(
            "show running-config",
            expect_command=False,
            before_catch=r"!Time: .+",
        ).strip()
        return io.BytesIO(data.encode())
