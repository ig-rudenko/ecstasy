import io
import re
import time
from typing import Literal

from .base.device import BaseDevice
from .base.factory import AbstractDeviceFactory
from .base.types import (
    MACListType,
    InterfaceVLANListType,
    InterfaceListType,
    DeviceAuthDict,
    InterfaceType,
    MACTableType,
    MACType,
)
from .base.validators import validate_and_format_port_as_normal


class Almatek(BaseDevice):
    prompt = r"\S+# $"
    space_prompt = r"--More--"
    mac_format = r"\S\S:\S\S\:\S\S:\S\S\:\S\S:\S\S"  # 00:11:22:33:44:55
    vendor = "Almatek"

    def __init__(self, session, ip: str, auth: DeviceAuthDict, snmp_community: str = ""):
        super().__init__(session, ip, auth, snmp_community=snmp_community)
        info = self.send_command("show info")
        self.model = self.find_or_empty(r"System Model\s+:(\S+)", info)
        self.mac = self.find_or_empty(r"MAC Address\s+:(\S+)", info)
        self.serialno = self.find_or_empty(r"System SN\s+:(\S+)", info)
        self.__cache_port_info: dict[str, str] = {}

    @BaseDevice.lock_session
    def get_interfaces(self) -> InterfaceListType:
        """
        ## Возвращаем список всех интерфейсов на устройстве

        Команда на оборудовании:

            # show interfaces brief

        :return: ```[ ('name', 'status', 'desc'), ... ]```
        """

        output = self.send_command("show interfaces brief")
        parsed = re.findall(r"(gi\d+)\s+(\S*)\s+(connect|notconnect|disable)\s+\d+", output)

        interfaces: InterfaceListType = []
        for name, desc, status in parsed:
            valid_status: InterfaceType
            if status == "connect":
                valid_status = "up"
            elif status == "notconnect":
                valid_status = "down"
            elif status == "disable":
                valid_status = "admin down"
            else:
                valid_status = "notPresent"

            interfaces.append((name, valid_status, desc))
        return interfaces

    @BaseDevice.lock_session
    def get_vlans(self) -> InterfaceVLANListType:
        """
        Возвращаем список всех интерфейсов и его VLAN на коммутаторе.

        # show vlan

        ```
            VID  VLAN Name        Untagged Ports              Tagged Ports                Type
            1    default          gi8-10,lag1-8                                           Default
            3000 NAME             gi1-7                       gi8-9                       Static
        ```
        """

        vlans_output = self.send_command("show vlan")
        vlans_parsed: list[list[str]] = re.findall(
            r"(\d{1,4})\s+(\S+)\s+(\S*)\s+(\S*)\s+(?=Default|Static)", vlans_output
        )
        interfaces_vlans: dict[str, list[int]] = {}
        for vid, name, untagged, tagged in vlans_parsed:
            untagged_list: list[str] = untagged.split(",")
            tagged_list: list[str] = tagged.split(",")

            for ports in [untagged_list, tagged_list]:
                for port in ports:
                    if "-" in port and port.startswith("gi"):
                        untagged_port_range = port[2:].split("-")
                        for i in range(int(untagged_port_range[0]), int(untagged_port_range[1]) + 1):
                            interfaces_vlans.setdefault(f"gi{i}", []).append(int(vid))
                    else:
                        interfaces_vlans.setdefault(port, []).append(int(vid))

        self.lock = False
        interfaces = self.get_interfaces()
        result: InterfaceVLANListType = []
        for interface in interfaces:
            result.append((interface[0], interface[1], interface[2], interfaces_vlans.get(interface[0], [])))

        return result

    @BaseDevice.lock_session
    def get_mac_table(self) -> MACTableType:
        """
        ## Возвращаем список из VLAN, MAC-адреса, dynamic и порта для данного оборудования.

        Команда на оборудовании:

            # show mac address-table

        :return: ```[ ({int:vid}, '{mac}', 'dynamic', '{port}'), ... ]```
        """

        def mac_type(type_: str) -> MACType:
            type_ = type_.lower()
            if type_ == "dynamic":
                return "dynamic"
            if type_ == "static":
                return "static"
            return "security"

        mac_str = self.send_command("show mac address-table", expect_command=False)
        mac_table: list[tuple[str, str, str, str]] = re.findall(
            rf"(\d+)\s+\|\s+({self.mac_format})\s+\|\s+(\S+)\s+\|\s+(gi\d+)",
            mac_str,
            flags=re.IGNORECASE,
        )
        return [(int(vid), mac, mac_type(type_), port) for vid, mac, type_, port in mac_table]

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal(if_invalid_return=[])
    def get_mac(self, port: str) -> MACListType:
        """
        ## Возвращаем список из VLAN и MAC-адреса для данного порта.

        Команда на оборудовании:

            # show mac address {port}

        :return: ```[ ('vid', 'mac'), ... ]```
        """
        mac_output = self.send_command(f"show mac address-table interface {port}")
        print(mac_output)
        mac_parsed: list[list[str]] = re.findall(
            rf"(\d+)\s+\|\s+({self.mac_format})\s+\|\s+\S+\s+\|\s+gi\d+", mac_output
        )
        print(mac_parsed)
        return [(vid, mac) for vid, mac, *_ in mac_parsed]

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal()
    def reload_port(self, port: str, save_config=True) -> str:
        """
        ## Перезагружает порт

        Переходим в режим конфигурирования:

            # configure

        Переходим к интерфейсу:

            (config)# interface {port}

        Перезагружаем порт:

            (config-if)# shutdown
            (config-if)# no shutdown

        Выходим из режима конфигурирования:

            (config-if)# end

        :param port: Порт для перезагрузки
        :param save_config: Если True, конфигурация будет сохранена на устройстве, defaults to True (optional)
        """

        self.session.sendline("configure")
        self.session.expect(self.prompt)
        self.session.sendline(f"interface {port}")
        self.session.expect(self.prompt)
        self.session.sendline("shutdown")
        time.sleep(1)
        self.session.sendline("no shutdown")
        self.session.expect(self.prompt)
        self.session.sendline("end")

        r = (self.session.before or b"").decode(errors="ignore")
        self.lock = False
        s = self.save_config() if save_config else "Without saving"
        return r + s

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal()
    def set_port(self, port: str, status: Literal["up", "down"], save_config=True) -> str:
        """
        ## Устанавливает статус порта на коммутаторе **up** или **down**

        Переходим в режим конфигурирования:
            # configure

        Переходим к интерфейсу:
            (config)# interface {port}

        Меняем состояние порта:
            (config-if)# {shutdown|no shutdown}

        Выходим из режима конфигурирования:
            (config-if)# end

        :param port: Порт
        :param status: "up" или "down"
        :param save_config: Если True, конфигурация будет сохранена на устройстве, defaults to True (optional)
        """

        self.session.sendline("configure")
        self.session.expect(self.prompt)
        self.session.sendline(f"interface {port}")
        self.session.expect(self.prompt)
        if status == "up":
            self.session.sendline("no shutdown")
        elif status == "down":
            self.session.sendline("shutdown")
        self.session.sendline("end")
        self.session.expect(self.prompt)

        r = (self.session.before or b"").decode(errors="ignore")
        self.lock = False
        s = self.save_config() if save_config else "Without saving"
        return r + s

    def save_config(self) -> str:
        """
        ## Сохраняем конфигурацию оборудования командой:

            # save

        Ожидаем ответа от оборудования `Success`,
        если нет, то пробуем еще 2 раза, в противном случае ошибка сохранения
        """

        for _ in range(3):  # Пробуем 3 раза, если ошибка
            self.session.sendline("save")
            if self.session.expect([self.prompt, r"Success"]):
                self.session.expect(self.prompt)
                return self.SAVED_OK
        return self.SAVED_ERR

    def set_description(self, port: str, desc: str) -> dict:
        """
        ## Устанавливаем описание для порта предварительно очистив его от лишних символов.

        Переходим в режим конфигурирования:

            # configure

        Переходим к интерфейсу:

            (config)# interface {port}

        Если была передана пустая строка для описания, то очищаем с помощью команды:

            (config-if)# no description

        Если **desc** содержит описание, то используем команду для изменения:

            (config-if)# description {desc}

        Выходим из режима конфигурирования:

            (config-if)# end

        :param port: Порт, для которого вы хотите установить описание.
        :param desc: Описание, которое вы хотите установить для порта.
        :return: Вывод команды смены описания.
        """

        desc = self.clear_description(desc)  # Очищаем описание

        # Переходим к редактированию порта
        self.session.sendline("configure")
        self.session.expect(self.prompt)
        self.session.sendline(f"interface {port}")
        self.session.expect(self.prompt)

        if desc == "":
            # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            res = self.send_command("no description", expect_command=False)

        else:  # В другом случае, меняем описание на оборудовании
            res = self.send_command(f"description {desc}", expect_command=False)

        if "Input Parameter Error" in res:
            # Если длина описания больше чем доступно на оборудовании
            output = self.send_command("description ?")

            self.session.sendline("end")
            self.session.expect(self.prompt)

            return {
                "max_length": int(self.find_or_empty(r" Up to (\d+) characters", output)),
                "status": "fail",
            }

        self.session.sendline("end")
        self.session.expect(self.prompt)

        self.lock = False
        # Возвращаем строку с результатом работы и сохраняем конфигурацию
        return {
            "description": desc,
            "port": port,
            "status": "changed" if desc else "cleared",
            "info": self.save_config(),
        }

    @validate_and_format_port_as_normal()
    @BaseDevice.lock_session
    def get_port_info(self, port: str) -> dict:
        """
        ## Возвращаем информацию о порте.

        Через команду:

            # show interfaces {port}
        """

        port_info = self.send_command(f"show interfaces {port}", expect_command=False)
        # Сохраняем в кэш
        self.__cache_port_info[port] = port_info
        return {"type": "text", "data": port_info}

    @validate_and_format_port_as_normal()
    def get_port_type(self, port: str) -> str:
        """
        ## Возвращает тип порта

        :param port: Порт для проверки
        :return: "SFP", "COPPER" или "?"
        """

        # Получаем информацию о порте.
        port_info = self.__cache_port_info.get(port) or self.get_port_info(port).get("data", "")
        # Ищем тип порта.
        port_type = "".join(self.find_or_empty(r"media type is (\S+)", port_info))
        if port_type == "Fiber":
            return "SFP"
        if port_type == "Copper":
            return "COPPER"
        return "?"

    @validate_and_format_port_as_normal()
    def get_port_errors(self, port: str) -> str:
        """
        ## Выводим ошибки на порту

        :param port: Порт для проверки на наличие ошибок
        """

        # Получаем информацию о порте.
        port_info = self.__cache_port_info.get(port) or self.get_port_info(port).get("data", "")

        media_type = [line.strip() for line in port_info.split("\n") if "errors" in line]
        return "<p>" + "\n".join(media_type) + "</p>"

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal()
    def get_port_config(self, port: str) -> str:
        """
        ## Выводим конфигурацию порта

        Используем команду:

            # show running-config interface {port}
        """
        return self.send_command(f"show running-config interface {port}").strip()

    def get_device_info(self) -> dict:
        return {}

    @BaseDevice.lock_session
    def get_current_configuration(self) -> io.BytesIO:
        data = self.send_command("show running-config", expect_command=True)
        return io.BytesIO(data.encode())


class AlmatekFactory(AbstractDeviceFactory):
    @staticmethod
    def is_can_use_this_factory(session=None, version_output=None) -> bool:
        if version_output:
            return (
                re.search(
                    r"Loader Version\s+:\s+\S+.*?"
                    r"Loader Date\s+:\s+.+?"
                    r"Firmware Version\s+:\s+\S+.*?"
                    r"Firmware Date\s+:\s+\S+",
                    version_output,
                    re.DOTALL,
                )
                is not None
            )
        return False

    @classmethod
    def get_device(
        cls,
        session,
        ip: str,
        snmp_community: str,
        auth: DeviceAuthDict,
        version_output: str = "",
    ) -> BaseDevice:
        return Almatek(session, ip, auth, snmp_community=snmp_community)
