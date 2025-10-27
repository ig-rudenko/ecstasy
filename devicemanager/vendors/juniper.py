import binascii
import io
import re
from pathlib import Path
from re import findall, sub
from typing import Literal

import pexpect
import textfsm

from .. import UnknownDeviceError
from .base.device import AbstractConfigDevice, BaseDevice
from .base.factory import AbstractDeviceFactory
from .base.types import (
    TEMPLATE_FOLDER,
    ArpInfoResult,
    DeviceAuthDict,
    InterfaceListType,
    InterfaceType,
    InterfaceVLANListType,
    PortInfoType,
)


class Juniper(BaseDevice, AbstractConfigDevice):
    """
    # Для оборудования от производителя Juniper
    """

    prompt = r"> $"
    space_prompt = r"-+\(more.*?\)-+"
    vendor = "juniper"
    mac_format = r"\S\S:\S\S:\S\S:\S\S:\S\S:\S\S"

    def __init__(self, session, ip: str, auth: DeviceAuthDict, *args, **kwargs):
        super().__init__(session, ip, auth, *args, **kwargs)
        self.send_command("show version", expect_command=False)
        self.send_command("set cli screen-length 0", expect_command=False)

    @BaseDevice.lock_session
    def search_mac(self, mac_address: str) -> list[ArpInfoResult]:
        """
        ## Ищем MAC адрес среди subscribers и в таблице ARP оборудования

        **MAC необходимо передавать без разделительных символов**
        он сам преобразуется к виду, требуемому для Juniper

        Отправляем на оборудование команды:

            # show subscribers mac-address {mac_address} detail
            # show arp | match {mac_address}

        Возвращаем список всех IP-адресов, VLAN, связанных с этим MAC-адресом.

        :param mac_address: MAC-адрес, который вы хотите найти
        :return: ```['ip', 'mac' 'vlan_id', 'device_name', 'port']``` или ```['ip', 'mac' 'vlan_id']```
        """
        return self._search_ip_or_mac_address(mac_address, "mac")

    @BaseDevice.lock_session
    def search_ip(self, ip_address: str) -> list[ArpInfoResult]:
        """
        ## Ищем IP адрес среди subscribers и в таблице ARP оборудования

        Отправляем на оборудование команды:

            # show subscribers address {ip_address} detail
            # show arp | match {ip_address}

        Возвращаем список всех IP-адресов, VLAN, связанных с этим IP-адресом.

        :param ip_address: IP-адрес, который вы хотите найти
        :return: ```['ip', 'mac' 'vlan_id', 'device_name', 'port']``` или ```['ip', 'mac' 'vlan_id']```
        """
        return self._search_ip_or_mac_address(ip_address, "ip")

    def _search_ip_or_mac_address(
        self, address: str, search_type: Literal["ip", "mac"]
    ) -> list[ArpInfoResult]:
        subscriber_search = "address"
        if search_type == "mac":
            address = "{}{}:{}{}:{}{}:{}{}:{}{}:{}{}".format(*address)
            subscriber_search = "mac-address"

        # >> Ищем среди subscribers <<
        subscribers_output = self.send_command(
            f"show subscribers {subscriber_search} {address} detail",
            expect_command=False,
        )
        # Разбор вывода команды `show subscribers mac-address`
        result = self._parse_subscribers(subscribers_output)
        if result:
            # Нашли среди subscribers
            return [ArpInfoResult(*result)]

        # >> Ищем в таблице ARP <<
        match = self.send_command(f"show arp | match {address}", expect_command=False)

        # Форматируем вывод
        with open(
            f"{TEMPLATE_FOLDER}/arp_format/{self.vendor.lower()}-{self.model.lower()}.template",
            encoding="utf-8",
        ) as template_file:
            template = textfsm.TextFSM(template_file)
        result = template.ParseText(match)
        if result:
            # Нашли в таблице ARP
            return [ArpInfoResult(*r) for r in result]

        return []

    @staticmethod
    def _convert_hex_to_ascii(hex_string: str) -> str:
        """
        ## Принимает строку состоящую из шестнадцатеричных символов и преобразовывает её в строку из ASCII символов
        """

        # Удаление всех пробелов из строки. "\n00 04 02 5e 00 03\n"
        unknown_format_str = sub(r"\s", "", hex_string)  # "0004025e0003"

        try:
            # Преобразование шестнадцатеричной строки в ascii.
            # Используем `binascii.unhexlify()` для преобразования результирующей строки шестнадцатеричных цифр
            # в байтовый объект, затем используем метод `decode()` для преобразования bytes в строку
            # с использованием кодировки ASCII. Аргумент `errors="replace"` указывает, что любые символы,
            # отличные от ASCII, во входной строке должны быть заменены символом замены Unicode (U+FFFD) в строке.
            return binascii.unhexlify(unknown_format_str).decode("ascii", errors="replace")

        # Если шестнадцатеричная строка не является допустимой шестнадцатеричной строкой, она выдаст ошибку.
        # Это способ поймать эту ошибку и вернуть исходную шестнадцатеричную строку к списку.
        except binascii.Error:
            return unknown_format_str

    def _parse_subscribers(self, string: str) -> list:
        """
        ## Парсим данные из вывода команды **subscribers**:

            ...
            IP Address: 10.201.170.140
            ...
            MAC Address: c0:25:e9:46:77:0f
            ...
            VLAN Id: 604
            Agent Circuit ID: port1
            Agent Remote ID: Device_name
            ...

        :returns: ['ip', 'mac' 'vlan_id', 'device_name', 'port']
        """

        # Форматируем вывод

        info: list[str] = []

        # IP / MAC / VLAN
        ip_mac_vlan = findall(
            r"IP Address:\s+(\d+\.\d+\.\d+\.\d+)[\s\S]+"
            r"MAC Address:\s+(\S+)[\s\S]+"
            r"VLAN Id:\s+(\d+)[\s\S]+",
            string,
        )
        if ip_mac_vlan:
            info += list(*ip_mac_vlan)

        # Agent Remote ID
        agent_remote = findall(
            r"Agent Remote ID: len \d+([\s\S]*?(?=Login Time))|"
            r"Agent Remote ID: (\S+[\s\S]*?(?=Login Time))",
            string,
        )
        if agent_remote:
            # Шестнадцатеричная строка получается из переменной `agent_remote`, которая представляет собой список
            # строк, полученных с помощью поиска по регулярному выражению.
            # Часть кода `"".join(agent_remote[0])` объединяет строки в списке `agent_remote`, чтобы
            # сформировать единую строку, которая затем передается в качестве аргумента методу `convert_hex_to_ascii`.
            # Результирующая строка ASCII затем добавляется к списку `info`.
            info.append(self._convert_hex_to_ascii("".join(agent_remote[0])))

        # Agent Circuit ID
        agent_circuit = findall(
            r"Agent Circuit ID: len \d+([\s\S]*?)(?=Agent Remote ID)|"
            r"Agent Circuit ID: (\S+[\s\S]*?)(?=Agent Remote ID)",
            string,
        )
        if agent_circuit:
            # Шестнадцатеричная строка получается из переменной `agent_circuit`, которая представляет собой список
            # строк, полученных с помощью поиска по регулярному выражению.
            # Часть кода `"".join(agent_circuit[0])` объединяет элементы списка `agent_circuit` в единую строку, которая
            # затем передается в качестве аргумента методу `convert_hex_to_ascii`.
            # Результирующая строка ASCII затем добавляется к списку `info`.
            info.append(self._convert_hex_to_ascii("".join(agent_circuit[0])))

        return info

    @BaseDevice.lock_session
    def get_interfaces(self) -> InterfaceListType:
        output = self.send_command("show interfaces description", expect_command=False)
        interfaces_raw = re.findall(r"^\s*(\S+) +(up|down) +(up|down) *(.*)$", output, flags=re.MULTILINE)

        interfaces = []
        for port_name, admin_status, link_status, desc in interfaces_raw:
            status: InterfaceType = "up"
            if admin_status.lower() == "down":
                status = "admin down"
            elif "down" in link_status.lower():
                status = "down"

            interfaces.append((port_name, status, desc))

        return interfaces

    def get_vlans(self) -> InterfaceVLANListType:
        return [(port, status, desc, []) for port, status, desc in self.get_interfaces()]

    def get_mac(self, port: str) -> list:
        return []

    def reload_port(self, port: str, save_config=True) -> str:
        return ""

    def set_port(self, port: str, status: str, save_config=True) -> str:
        return ""

    def save_config(self):
        pass

    def set_description(self, port: str, desc: str) -> dict:
        return {}

    @BaseDevice.lock_session
    def get_port_info(self, port: str) -> PortInfoType:
        output = self.send_command(f"show interfaces {port} detail", expect_command=False)
        return {"type": "text", "data": output}

    def get_port_type(self, port: str) -> str:
        return ""

    @BaseDevice.lock_session
    def get_port_config(self, port: str) -> str:
        return self.send_command(f"show configuration interfaces {port}", expect_command=False)

    def get_port_errors(self, port: str) -> str:
        return ""

    def get_device_info(self) -> dict:
        return {}

    @BaseDevice.lock_session
    def execute_command(self, cmd: str) -> str:
        return self.send_command(cmd.strip(), expect_command=False, before_catch=cmd[1:])

    @BaseDevice.lock_session
    def get_current_configuration(self) -> io.BytesIO | Path:
        data = self.send_command("show configuration", expect_command=False)
        return io.BytesIO(data.encode())


class JuniperFactory(AbstractDeviceFactory):
    @staticmethod
    def is_can_use_this_factory(session=None, version_output=None) -> bool:
        return bool(
            version_output
            and re.search(r"JUNOS|show: invalid command, valid commands are", str(version_output))
        )

    @classmethod
    def get_device(
        cls,
        session,
        ip: str,
        snmp_community: str,
        auth: DeviceAuthDict,
        version_output: str = "",
    ) -> BaseDevice:
        if "show: invalid command, valid commands are" in version_output:
            session.sendline("sys info show")
            while True:
                match = session.expect([r"]$", "---- [Mm]ore", r">\s*$", r"#\s*$", pexpect.TIMEOUT])
                version_output += str(session.before.decode("utf-8"))
                if match == 1:
                    session.sendline(" ")
                if match == 4:
                    session.sendcontrol("C")
                else:
                    break

            if "unknown keyword show" in version_output:
                return Juniper(session, ip, auth, snmp_community=snmp_community)

            raise UnknownDeviceError("JuniperFactory не удалось распознать модель оборудования", ip=ip)

        model = BaseDevice.find_or_empty(r"Model: (\S+)", version_output)
        return Juniper(session, ip, auth, model, snmp_community=snmp_community)
