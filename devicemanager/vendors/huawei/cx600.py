from typing import Literal

import textfsm

from ..base.device import BaseDevice
from ..base.types import (
    TEMPLATE_FOLDER,
    InterfaceListType,
    InterfaceVLANListType,
    MACListType,
    ArpInfoResult,
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
    def search_mac(self, mac_address: str) -> list[ArpInfoResult]:
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
        return self._search_ip_or_mac(address=formatted_mac, address_type="mac")

    @BaseDevice.lock_session
    def search_ip(self, ip_address: str) -> list[ArpInfoResult]:
        """
        ## Ищем абонента по его IP адресу

        Отправляем на оборудование команду:

            # display access-user ip-address {ip_address}

        Возвращаем список всех IP-адресов, VLAN, связанных с этим MAC-адресом.

        :param ip_address: IP-адрес
        :return: ```['IP', 'MAC', 'VLAN', 'Agent-Circuit-Id', 'Agent-Remote-Id']```
        """
        return self._search_ip_or_mac(address=ip_address, address_type="ip")

    def _search_ip_or_mac(self, address: str, address_type: Literal["ip", "mac"]) -> list[ArpInfoResult]:
        match = self.send_command(
            f"display access-user {address_type}-address {address}",
            expect_command=False,
        )

        # Форматируем вывод
        with open(
            f"{TEMPLATE_FOLDER}/arp_format/{self.vendor.lower()}-{self.model.lower()}.template",
            encoding="utf-8",
        ) as template_file:
            template = textfsm.TextFSM(template_file)
        result = template.ParseText(match)

        return list(map(lambda r: ArpInfoResult(*r), result)) if result else []

    def get_interfaces(self) -> InterfaceListType:
        return []

    def get_vlans(self) -> InterfaceVLANListType:
        return []

    def get_mac(self, port: str) -> MACListType:
        return []

    def reload_port(self, port: str, save_config=True) -> str:
        return ""

    def set_port(self, port: str, status: str, save_config=True) -> str:
        return ""

    def save_config(self):
        pass

    def set_description(self, port: str, desc: str) -> dict:
        return {}

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
        bras_output = self.send_command(f"display access-user mac-address {mac}", expect_command=False)
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
