import binascii
from re import findall, sub
from typing import List

import textfsm
from .base import BaseDevice, TEMPLATE_FOLDER


class Juniper(BaseDevice):
    """
    # Для оборудования от производителя Juniper
    """

    prompt = r"> $"
    space_prompt = r"-+\(more.*?\)-+"
    vendor = "juniper"
    mac_format = r"\S\S:\S\S:\S\S:\S\S:\S\S:\S\S"

    @BaseDevice._lock
    def search_mac(self, mac_address: str) -> list:
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

        formatted_mac = "{}{}:{}{}:{}{}:{}{}:{}{}:{}{}".format(*mac_address)

        # >> Ищем среди subscribers <<
        subscribers_output = self.send_command(
            f"show subscribers mac-address {formatted_mac} detail", expect_command=False
        )
        # Разбор вывода команды `show subscribers mac-address`
        formatted_result = self._parse_subscribers(subscribers_output)
        if formatted_result:
            # Нашли среди subscribers
            return formatted_result

        # >> Ищем в таблице ARP <<
        match = self.send_command(
            f"show arp | match {formatted_mac}", expect_command=False
        )

        # Форматируем вывод
        with open(
            f"{TEMPLATE_FOLDER}/arp_format/{self.vendor.lower()}-{self.model.lower()}.template",
            encoding="utf-8",
        ) as template_file:
            template = textfsm.TextFSM(template_file)
        formatted_result = template.ParseText(match)
        if formatted_result:
            # Нашли в таблице ARP
            return formatted_result[0]

        return []

    @BaseDevice._lock
    def search_ip(self, ip_address: str) -> list:
        """
        ## Ищем IP адрес среди subscribers и в таблице ARP оборудования

        Отправляем на оборудование команды:

            # show subscribers address {ip_address} detail
            # show arp | match {ip_address}

        Возвращаем список всех IP-адресов, VLAN, связанных с этим MAC-адресом.

        :param ip_address: IP-адрес, который вы хотите найти
        :return: ```['ip', 'mac' 'vlan_id', 'device_name', 'port']``` или ```['ip', 'mac' 'vlan_id']```
        """

        # >> Ищем среди subscribers <<
        subscribers_output = self.send_command(
            f"show subscribers address {ip_address} detail", expect_command=False
        )
        formatted_result = self._parse_subscribers(subscribers_output)
        if formatted_result:
            # Нашли среди subscribers
            return formatted_result

        # >> Ищем в таблице ARP <<
        match = self.send_command(
            f"show arp | match {ip_address}", expect_command=False
        )

        # Форматируем вывод
        with open(
            f"{TEMPLATE_FOLDER}/arp_format/{self.vendor.lower()}-{self.model.lower()}.template",
            encoding="utf-8",
        ) as template_file:
            template = textfsm.TextFSM(template_file)

        formatted_result = template.ParseText(match)
        if formatted_result:
            return formatted_result[0]

        return []

    @staticmethod
    def _parse_subscribers(string: str) -> list:
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

        def convert_to_str(list_of_strings: List[list]) -> str:
            """
            `convert_to_str` принимает список строк и возвращает строку

            :param list_of_strings: Это список строк, которые вы хотите преобразовать в одну строку
            :type list_of_strings: List[list]
            """

            # Объединение списка строк в одну строку.
            total_string = "".join(list_of_strings[0])  # "\n00 04 02 5e 00 03\n"
            # Удаление всех пробелов из строки.
            unknown_format_str = sub(r"\s", "", total_string)  # "0004025e0003"

            try:
                # Преобразование шестнадцатеричной строки в ascii.
                return binascii.unhexlify(unknown_format_str).decode(
                    "ascii", errors="replace"
                )

            # Если шестнадцатеричная строка не является допустимой шестнадцатеричной строкой, она выдаст ошибку.
            # Это способ поймать эту ошибку и вернуть исходную шестнадцатеричную строку к списку.
            except binascii.Error:
                return unknown_format_str

        # Форматируем вывод

        info = []

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
            info.append(convert_to_str(agent_remote))

        # Agent Circuit ID
        agent_circuit = findall(
            r"Agent Circuit ID: len \d+([\s\S]*?)(?=Agent Remote ID)|"
            r"Agent Circuit ID: (\S+[\s\S]*?)(?=Agent Remote ID)",
            string,
        )
        if agent_circuit:
            info.append(convert_to_str(agent_circuit))

        return info

    def get_interfaces(self) -> list:
        pass

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
