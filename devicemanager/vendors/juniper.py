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
            return formatted_result[0]

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
            return formatted_result[0]

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

    def parse_subscribers(self, string: str) -> list:
        # Форматируем вывод
        with open(
            f"{TEMPLATE_FOLDER}/{self.vendor.lower()}-{self.model.lower()}/subscribers.template",
            encoding="utf-8",
        ) as template_file:
            template = textfsm.TextFSM(template_file)

        return template.ParseText(string)

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
