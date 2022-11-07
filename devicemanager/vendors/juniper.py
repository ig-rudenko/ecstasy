import textfsm
from .base import BaseDevice, TEMPLATE_FOLDER


class Juniper(BaseDevice):
    prompt = r"> $"
    space_prompt = r"-+\(more.*?\)-+"
    vendor = "juniper"
    mac_format = r"\S\S:" * 5 + r"\S\S"

    def search_mac(self, mac_address: str) -> list:

        formatted_mac = "{}{}:{}{}:{}{}:{}{}:{}{}:{}{}".format(*mac_address)

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
            return formatted_result[0]

        return []

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
