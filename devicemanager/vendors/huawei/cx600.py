import textfsm

from ..base.device import BaseDevice
from ..base.types import (
    TEMPLATE_FOLDER,
    T_InterfaceList,
    T_InterfaceVLANList,
    T_MACList,
)


class HuaweiCX600(BaseDevice):
    """
    # Для оборудования серии CX600 от производителя Huawei
    """

    prompt = r"<\S+>$|\[\S+\]$|Unrecognized command"
    space_prompt = r"  ---- More ----|Are you sure to display some information"
    # Регулярное выражение, которое соответствует MAC-адресу.
    mac_format = r"\S\S\S\S-\S\S\S\S-\S\S\S\S"
    vendor = "Huawei"

    @BaseDevice.lock_session
    def search_mac(self, mac_address: str) -> list:
        """
        ## Возвращаем данные абонента по его MAC адресу

        **MAC необходимо передавать без разделительных символов** он сам преобразуется к виду, требуемому для CX600

        Отправляем на оборудование команду:

            # display access-user mac-address {mac_address}

        Возвращаем список всех IP-адресов, VLAN, связанных с этим MAC-адресом.

        :param mac_address: MAC-адрес
        :return: ```['IP', 'MAC', 'VLAN', 'Agent-Circuit-Id', 'Agent-Remote-Id']```
        """

        formatted_mac = "{}{}{}{}-{}{}{}{}-{}{}{}{}".format(*mac_address)

        match = self.send_command(
            f"display access-user mac-address {formatted_mac}",
            expect_command=False,
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

    @BaseDevice.lock_session
    def search_ip(self, ip_address: str) -> list:
        """
        ## Ищем абонента по его IP адресу

        Отправляем на оборудование команду:

            # display access-user ip-address {ip_address}

        Возвращаем список всех IP-адресов, VLAN, связанных с этим MAC-адресом.

        :param ip_address: IP-адрес
        :return: ```['IP', 'MAC', 'VLAN', 'Agent-Circuit-Id', 'Agent-Remote-Id']```
        """

        match = self.send_command(
            f"display access-user ip-address {ip_address}",
            expect_command=False,
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

    def get_interfaces(self) -> T_InterfaceList:
        return []

    def get_vlans(self) -> T_InterfaceVLANList:
        return []

    def get_mac(self, port: str) -> T_MACList:
        return []

    def reload_port(self, port: str, save_config=True) -> str:
        return ""

    def set_port(self, port: str, status: str, save_config=True) -> str:
        return ""

    def save_config(self):
        pass

    def set_description(self, port: str, desc: str) -> str:
        return ""

    def get_port_info(self, port: str) -> dict:
        return {}

    def get_port_type(self, port: str) -> str:
        return ""

    def get_port_config(self, port: str) -> str:
        return ""

    def get_port_errors(self, port: str) -> str:
        return ""

    def get_device_info(self) -> dict:
        return {}

    def get_access_user_data(self, mac: str) -> str:
        bras_output = self.send_command(
            f"display access-user mac-address {mac}", expect_command=False
        )
        if "No online user!" not in bras_output:
            user_index = self.find_or_empty(r"User access index\s+:\s+(\d+)", bras_output)

            if user_index:
                bras_output = self.send_command(
                    f"display access-user user-id {user_index} verbose",
                )
        return bras_output

    def cut_access_user_session(self, mac: str) -> str:
        self.send_command("system-view")
        self.send_command("aaa")
        # Срезаем сессию по MAC адресу
        self.send_command(f"cut access-user mac-address {mac}")
        return ""
