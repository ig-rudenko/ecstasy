import binascii
from re import findall, sub

import textfsm
from .base import BaseDevice, TEMPLATE_FOLDER


class Juniper(BaseDevice):
    prompt = r"> $"
    space_prompt = r"-+\(more.*?\)-+"
    vendor = "juniper"
    mac_format = r"\S\S:\S\S:\S\S:\S\S:\S\S:\S\S"

    def search_mac(self, mac_address: str) -> list:
        """Ищем MAC адрес в таблице ARP оборудования"""

        formatted_mac = "{}{}:{}{}:{}{}:{}{}:{}{}:{}{}".format(*mac_address)

        # >> Ищем среди subscribers <<
        subscribers_output = self.send_command(
            f"show subscribers mac-address {formatted_mac} detail", expect_command=False
        )
        formatted_result = self.parse_subscribers(subscribers_output)
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

    def search_ip(self, ip_address: str) -> list:
        """Ищем IP адрес в таблице ARP оборудования"""

        # >> Ищем среди subscribers <<
        subscribers_output = self.send_command(
            f"show subscribers address {ip_address} detail", expect_command=False
        )
        formatted_result = self.parse_subscribers(subscribers_output)
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
    def parse_subscribers(string: str) -> list:
        """
        Парсим данные:

          ...
          IP Address: 10.201.170.140
          ...
          MAC Address: c0:25:e9:46:77:0f
          ...
          VLAN Id: 604
          Agent Circuit ID: port1
          Agent Remote ID: SVSL-122-Kosar27p4-ASW1
          ...

        :returns: ['ip', 'mac' 'vlan_id', 'device_name', 'port']

        """

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
            agent_remote = "".join(agent_remote[0])  # "\n00 04 02 5e 00 03\n"

            # Удаляем лишние символы
            agent_remote_hex = sub(r"\s", "", agent_remote)  # "0004025e0003"

            # Преобразуем из hex в строку с кодировкой ascii
            info.append(binascii.unhexlify(agent_remote_hex).decode("ascii"))

        # Agent Circuit ID
        agent_circuit = findall(
            r"Agent Circuit ID: len \d+([\s\S]*?)(?=Agent Remote ID)|"
            r"Agent Circuit ID: (\S+[\s\S]*?)(?=Agent Remote ID)",
            string,
        )
        if agent_circuit:
            agent_circuit = "".join(agent_circuit[0])  # "\n00 04 02 5e 00 03\n"

            # Удаляем лишние символы
            agent_circuit_hex = sub(r"\s", "", agent_circuit)  # "0004025e0003"

            # Преобразуем из hex в строку с кодировкой ascii
            info.append(binascii.unhexlify(agent_circuit_hex).decode("ascii"))

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
