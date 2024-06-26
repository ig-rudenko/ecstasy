import re
from functools import partial
from time import sleep
from typing import Literal

from .base.device import BaseDevice
from .base.factory import AbstractDeviceFactory
from .base.helpers import parse_by_template
from .base.types import (
    InterfaceListType,
    InterfaceVLANListType,
    MACListType,
    MACTableType,
    MACType,
    DeviceAuthDict,
    InterfaceType,
    PortInfoType,
)
from .base.validators import validate_and_format_port


def validate_port(port: str) -> str | None:
    """
    ## Проверка правильности порта Q-Tech.

    valid ports:
      - "1/2/1"
      - "1/1/21"

    invalid ports:
      - "23"
      - "port12"
    """

    port = port.strip()
    if re.match(r"^\d+/\d+/\d+$", port):
        return port
    return None


# Создаем свой декоратор для проверки портов
qtech_validate_and_format_port = partial(validate_and_format_port, validator=validate_port)


class Qtech(BaseDevice):
    """
    # Для оборудования от производителя Q-Tech

    Проверено для:
     - QSW-8200
    """

    prompt = r"\S+#$"
    space_prompt = "--More--"
    mac_format = r"\S\S-" * 5 + r"\S\S"
    vendor = "Q-Tech"

    def __init__(
        self,
        session,
        ip: str,
        auth: DeviceAuthDict,
        model: str = "",
        snmp_community: str = "",
    ):
        super().__init__(session, ip, auth, model, snmp_community)
        self.__cache_port_info: dict[str, str] = {}

    @BaseDevice.lock_session
    def get_interfaces(self) -> InterfaceListType:
        """
        ## Возвращаем список всех интерфейсов на устройстве

        Команда на оборудовании:

            # show interface ethernet status

        :return: ```[ ('name', 'status', 'desc'), ... ]```
        """

        output = self.send_command(command="show interface ethernet status", expect_command=False)
        output = re.sub(r"[\W\S]+\nInterface", "\nInterface", output)

        result = parse_by_template("interfaces/q-tech.template", output)

        interfaces = []
        for port_name, link_status, desc in result:
            status: InterfaceType = "up"
            if link_status == "A-DOWN":
                status = "admin down"
            elif link_status == "DOWN":
                status = "down"

            interfaces.append((port_name, status, desc))

        return interfaces

    @BaseDevice.lock_session
    def get_vlans(self) -> InterfaceVLANListType:
        """
        ## Возвращаем список всех интерфейсов и его VLAN на коммутаторе.

        Для начала получаем список всех интерфейсов через метод **get_interfaces()**

        Затем для каждого интерфейса смотрим конфигурацию

            # show running-config interface ethernet {port}

        И выбираем строчки, в которых указаны VLAN:

         - ```vlan {vid},{vid},...{vid}```
         - ```vlan add {vid},{vid},...{vid}```

        :return: ```[ ('name', 'status', 'desc', ['{vid}', '{vid},{vid},...{vid}', ...] ), ... ]```
        """

        result = []
        self.lock = False
        interfaces = self.get_interfaces()
        self.lock = True

        for line in interfaces:
            if not line[0].startswith("V"):
                output = self.send_command(command=f"show running-config interface ethernet {line[0]}")
                vlans_group = re.findall(r"vlan [ad ]*(\S*\d)", output)  # Строчки вланов
                vlans = []
                for v in vlans_group:
                    vlans += v.split(";")
                result.append((line[0], line[1], line[2], vlans))

        return result

    @staticmethod
    def normalize_interface_name(intf: str) -> str:
        return BaseDevice.find_or_empty(r"(\d+/\d+/?\d*)", intf)

    @BaseDevice.lock_session
    def get_mac_table(self) -> MACTableType:
        """
        ## Возвращаем список из VLAN, MAC-адреса, dynamic MAC-type и порта для данного оборудования.

        Команда на оборудовании:

            # show mac-address-table

            Vlan Mac Address                 Type    Creator   Ports
            ---- --------------------------- ------- -------------------------------------
            1    d0-c2-82-cd-6d-99           DYNAMIC Hardware Ethernet1/0/27
            118  00-04-96-51-ad-3d           DYNAMIC Hardware Ethernet1/0/27
            ...

        :return: ```[ ({int:vid}, '{mac}', 'dynamic', '{port}'), ... ]```
        """

        output = self.send_command("show mac-address-table")
        parsed: list[tuple[str, str, str]] = re.findall(
            rf"(\d+)\s+({self.mac_format})\s+DYNAMIC\s+\S+\s+(\S+).*\n", output
        )
        mac_type: MACType = "dynamic"
        return [(int(vid), mac, mac_type, port) for vid, mac, port in parsed]

    @BaseDevice.lock_session
    @qtech_validate_and_format_port(if_invalid_return=[])
    def get_mac(self, port: str) -> MACListType:
        """
        ## Возвращаем список из VLAN и MAC-адреса для данного порта.

        Команда на оборудовании:

            # show mac-address-table interface ethernet {port}

        :param port: Номер порта коммутатора
        :return: ```[ ('vid', 'mac'), ... ]```
        """

        output = self.send_command(f"show mac-address-table interface ethernet {port}")
        macs: list[tuple[str, str]] = re.findall(rf"(\d+)\s+({self.mac_format})", output)
        return [(int(vid), mac) for vid, mac in macs]

    @BaseDevice.lock_session
    @qtech_validate_and_format_port()
    def reload_port(self, port: str, save_config=True) -> str:
        """
        ## Перезагружает порт

        Переходим в режим конфигурирования:

            # config terminal

        Переходим к интерфейсу:

            (config)# interface ethernet {port}

        Перезагружаем порт:

            (config-if)# shutdown
            (config-if)# no shutdown

        Выходим из режима конфигурирования:

            (config-if)# end

        :param port: Порт для перезагрузки
        :param save_config: Если True, конфигурация будет сохранена на устройстве, defaults to True (optional)
        """

        self.session.sendline("configure terminal")
        self.session.expect(self.prompt)
        self.session.sendline(f"interface ethernet {port}")
        self.session.expect(self.prompt)
        self.session.sendline("shutdown")
        sleep(1)
        self.session.sendline("no shutdown")
        self.session.expect(self.prompt)
        self.session.sendline("end")

        r = (self.session.before or b"").decode(errors="ignore")
        self.lock = False
        s = self.save_config() if save_config else "Without saving"
        return r + s

    @BaseDevice.lock_session
    @qtech_validate_and_format_port()
    def set_port(self, port: str, status: Literal["up", "down"], save_config: bool = True):
        """
        ## Устанавливает статус порта на коммутаторе **up** или **down**

        Переходим в режим конфигурирования:
            # config terminal

        Переходим к интерфейсу:
            (config)# interface ethernet {port}

        Меняем состояние порта:
            (config-if)# {shutdown|no shutdown}

        Выходим из режима конфигурирования:
            (config-if)# end

        :param port: Порт
        :param status: "up" или "down"
        :param save_config: Если True, конфигурация будет сохранена на устройстве, defaults to True (optional)
        """

        self.session.sendline("config terminal")
        self.session.expect(self.prompt)
        self.session.sendline(f"interface ethernet {port}")
        self.session.expect(self.prompt)
        if status == "up":
            self.session.sendline("no shutdown")
        elif status == "down":
            self.session.sendline("shutdown")
        self.session.sendline("end")
        self.session.expect(self.prompt)

        (self.session.before or b"").decode(errors="ignore")
        self.lock = False
        s = self.save_config() if save_config else "Without saving"
        return s

    @BaseDevice.lock_session
    def save_config(self):
        """
        ## Сохраняем конфигурацию оборудования командой:

            # write
            Y

        Ожидаем ответа от оборудования **successful**,
        если нет, то ошибка сохранения
        """

        self.session.sendline("write")
        self.session.sendline("Y")
        if self.session.expect([self.prompt, "successful"]):
            return self.SAVED_OK
        return self.SAVED_ERR

    @BaseDevice.lock_session
    def __get_port_info(self, port: str) -> str:
        """Общая информация о порте"""

        port_type = self.send_command(f"show interface ethernet{port}")
        return f"<p>{port_type}</p>"

    @qtech_validate_and_format_port({"type": "error", "data": "Неверный порт"})
    def get_port_info(self, port: str) -> PortInfoType:
        """
        ## Возвращаем информацию о порте.

        Через команду:

            # show interface ethernet{port}

        :param port: Номер порта, для которого требуется получить информацию
        :return: Информация о порте или ```"Неверный порт {port}"```
        """

        self.__cache_port_info[port] = self.__get_port_info(port)

        return {
            "type": "html",
            "data": "<br>".join(self.__get_port_info(port).split("\n")[:10]),
        }

    @qtech_validate_and_format_port(if_invalid_return="?")
    def get_port_type(self, port: str) -> str:
        """
        ## Возвращает тип порта

        :param port: Порт для проверки
        :return: "SFP", "COPPER" или "Неверный порт {port}"
        """
        port_info = self.__cache_port_info.get(port) or self.__get_port_info(port)

        port_type = self.find_or_empty(r"Hardware is (\S+)", port_info)
        if "SFP" in port_type:
            return "SFP"

        return "COPPER"

    @qtech_validate_and_format_port()
    def get_port_errors(self, port: str) -> str:
        """
        ## Выводим ошибки на порту

        :param port: Порт для проверки на наличие ошибок
        """

        result = []
        port_info = self.__cache_port_info.get(port) or self.__get_port_info(port)

        for line in port_info.split("\n"):
            if "error" in line:
                result.append(line.strip())

        return "\n".join(result)

    @BaseDevice.lock_session
    @qtech_validate_and_format_port()
    def get_port_config(self, port: str) -> str:
        """
        ## Выводим конфигурацию порта

        Используем команду:

            # show running-config interface ethernet {port}
        """

        return self.send_command(f"show running-config interface ethernet {port}").strip()

    @BaseDevice.lock_session
    @qtech_validate_and_format_port(if_invalid_return={"error": "Неверный порт", "status": "fail"})
    def set_description(self, port: str, desc: str) -> dict:
        """
        ## Устанавливаем описание для порта предварительно очистив его от лишних символов

        Если длина описания больше допустимой, то вернется ```"Max length:{max_length}"```

        Переходим в режим конфигурирования:

            # config terminal

        Переходим к интерфейсу:

            (config)# interface ethernet {port}

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

        desc = self.clear_description(desc)  # Очищаем описание

        # Переходим к редактированию порта
        self.session.sendline("config terminal")
        self.session.expect(self.prompt)
        self.session.sendline(f"interface ethernet {port}")
        self.session.expect(self.prompt)

        if desc == "":
            # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            status = self.send_command("no description", expect_command=False)

        else:  # В другом случае, меняем описание на оборудовании
            status = self.send_command(f"description {desc}", expect_command=False)

        self.session.sendline("end")  # Выходим из режима редактирования

        if "is too large" in status:
            # Если длина описания больше чем доступно на оборудовании
            output = self.send_command("description ?")
            max_length = int(self.find_or_empty(r"<1-(\d+)>", output))
            return {
                "port": port,
                "status": "fail",
                "error": "Too long",
                "max_length": max_length,
            }

        self.lock = False
        # Возвращаем строку с результатом работы и сохраняем конфигурацию
        return {
            "description": desc,
            "port": port,
            "status": "changed" if desc else "cleared",
            "saved": self.save_config(),
        }

    def get_device_info(self) -> dict:
        return {}


class QtechFactory(AbstractDeviceFactory):
    @staticmethod
    def is_can_use_this_factory(session=None, version_output=None) -> bool:
        return version_output and "QTECH" in str(version_output)

    @classmethod
    def get_device(
        cls,
        session,
        ip: str,
        snmp_community: str,
        auth: DeviceAuthDict,
        version_output: str = "",
    ) -> BaseDevice:
        model = BaseDevice.find_or_empty(r"\s+(\S+)\s+Device", version_output)
        return Qtech(session, ip, auth, model=model, snmp_community=snmp_community)
