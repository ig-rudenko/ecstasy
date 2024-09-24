import io
import re
from time import sleep
from typing import Literal

from ..base.device import BaseDevice, AbstractConfigDevice
from ..base.helpers import parse_by_template, range_to_numbers
from ..base.types import (
    InterfaceListType,
    InterfaceVLANListType,
    MACListType,
    MACTableType,
    MACType,
    InterfaceType,
    PortInfoType,
)
from ..base.validators import validate_and_format_port


def normalize_interface_name(intf: str) -> str:
    interface = str(intf).strip()
    res = re.findall(r"^(25|100)GE(\d+([/\\]?\d*)*(\.(\d{1,4}))?)$", interface)
    if res and (not res[0][-1] or 0 < int(res[0][-1]) < 4096):
        return interface
    return ""


def validate_huawei_ce6865_port(if_invalid_return=None):
    return validate_and_format_port(validator=normalize_interface_name, if_invalid_return=if_invalid_return)


class HuaweiCE6865(BaseDevice, AbstractConfigDevice):
    """
    # Для оборудования от производителя Huawei CE6865
    """

    prompt = r"<\S+>$|\[\S+\]$|Unrecognized command"
    space_prompt = r"---- More ----"
    mac_format = r"[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}"
    vendor = "Huawei"

    @BaseDevice.lock_session
    def save_config(self) -> str:
        """
        ## Сохраняем конфигурацию оборудования командой:

        ```
            > save
            Warning: The current configuration will be written to the device. Continue? [Y/N]:Y
            Now saving the current configuration to the slot 1 .....
            Info: Save the configuration successfully.
        ```

        Если конфигурация уже сохраняется, то будет выведено ```System is busy```,
        в таком случае ожидаем 2 секунды

        Ожидаем ответа от оборудования **successfully**,
        если нет, то пробуем еще 2 раза, в противном случае ошибка сохранения
        """

        n = 1
        while n <= 3:
            self.session.sendline("save")
            self.session.expect(r"The current configuration will be written to the device")
            self.session.sendline("Y")
            match = self.session.expect([self.prompt, r"successfully", r"[Ss]ystem is busy"], timeout=20)
            if match == 1:
                return self.SAVED_OK
            if match == 2:
                sleep(2)
                n += 1
                continue
        return self.SAVED_ERR

    @BaseDevice.lock_session
    def get_interfaces(self) -> InterfaceListType:
        """
        ## Возвращаем список всех интерфейсов на устройстве

        Команда на оборудовании:

            > display interface description

        :return: ```[ ('name', 'status', 'desc'), ... ]```
        """

        output = self.send_command("display interface description")

        result = parse_by_template("interfaces/huawei-ce6865.template", output)

        interfaces = []
        for port_name, phy, protocol, desc in result:
            if port_name.startswith("NULL") or port_name.startswith("V"):
                continue

            status: InterfaceType = "up"
            if phy.lower() == "*down":
                status = "admin down"
            elif "down" in protocol.lower():
                status = "down"
            interfaces.append((port_name, status, desc.strip()))

        return interfaces

    @BaseDevice.lock_session
    def get_vlans(self) -> InterfaceVLANListType:
        """
        ## Возвращаем список всех интерфейсов и его VLAN на коммутаторе.

        Для начала получаем список всех интерфейсов через метод **get_interfaces()**

        Смотрим конфигурацию всех интерфейсов

            > display current-configuration interface

        Выбираем строчки, в которых указаны VLAN, кроме тех, которые начинаются с `undo`

        :return: ```[ ('name', 'status', 'desc', ['{vid}', '{vid},{vid},...{vid}', ...] ), ... ]```
        """
        self.lock = False
        interfaces = self.get_interfaces()
        self.lock = True

        output = self.send_command("display current-configuration interface")
        result = parse_by_template(f"vlans_templates/huawei-ce6865.template", output)

        interfaces_vlans = {line[0]: range_to_numbers(line[1]) for line in result}

        result = []
        for interface, status, description in interfaces:
            result.append(
                (
                    interface,
                    status,
                    description,
                    interfaces_vlans.get(interface, []),
                )
            )

        return result

    @staticmethod
    def normalize_interface_name(intf: str) -> str:
        return normalize_interface_name(intf)

    @BaseDevice.lock_session
    def get_mac_table(self) -> MACTableType:
        """
        ## Возвращаем список из VLAN, MAC-адреса, тип и порт для данного оборудования.

        Команда на оборудовании:

            # display mac-address
            Flags: * - Backup
                   # - forwarding logical interface, operations cannot be performed based
                       on the interface.
            BD   : bridge-domain   Age : dynamic MAC learned time in seconds
            -------------------------------------------------------------------------------
            MAC Address    VLAN/VSI/BD   Learned-From        Type                Age
            -------------------------------------------------------------------------------
            3aad-b223-d191 104/-/-       25GE1/0/2           dynamic                247
            5aa0-b220-729f 104/-/-       25GE1/0/2           dynamic                 51
            8aad-b22b-b194 104/-/-       25GE1/0/1           dynamic                144
            8aad-b22b-b194 300/-/-       25GE1/0/1           dynamic                363
            0aab-b226-0791 3995/-/-      25GE1/0/6           dynamic            1821961
            0aa3-b22b-5f91 3995/-/-      25GE1/0/5           dynamic            1561821
            0aab-b226-0791 -/bbn3991/13991 25GE1/0/6.3991      dynamic            2733593

        :return: ```[ ({int:vid}, '{mac}', '{type:static|dynamic|security}', '{port}'), ... ]```
        """

        output = self.send_command("display mac-address", expect_command=False)
        mac_table = self._parse_mac_address_string(output)
        return [
            (int(vid), mac, mac_type, interface_full_name)
            for mac, vid, interface_full_name, intf_speed_prefix, subinterface, mac_type in mac_table
        ]

    @BaseDevice.lock_session
    @validate_huawei_ce6865_port(if_invalid_return=[])
    def get_mac(self, port) -> MACListType:
        """
        ## Возвращаем список из VLAN и MAC-адреса для данного порта.

        Команда на оборудовании:

            > display mac-address interface {port}

        :return: ```[ (vid, 'mac'), ... ]```
        """

        output = self.send_command(f"display mac-address interface {port}")
        mac_table = self._parse_mac_address_string(output)
        return [(int(vid), mac) for mac, vid, *_ in mac_table]

    def _parse_mac_address_string(self, string: str) -> list[tuple[str, str, str, str, str, MACType]]:
        mac_table = re.findall(
            rf"({self.mac_format})\s+(\d+)/\S+/\S+\s+((25|100)GE\d+/\d+/\d+(\.\d+)?)\s+(dynamic|static|security)",
            string,
        )
        return mac_table

    @validate_huawei_ce6865_port(if_invalid_return={"type": "error", "data": "Неверный порт"})
    def get_port_info(self, port: str) -> PortInfoType:
        return {
            "type": "text",
            "data": self.__port_info(port),
        }

    def get_port_type(self, port) -> str:
        """
        ## Возвращает тип порта
        :return: "SFP"
        """
        return "SFP"

    @validate_huawei_ce6865_port()
    def get_port_errors(self, port) -> str:
        """
        ## Выводим ошибки на порту

        :param port: Порт для проверки на наличие ошибок
        """

        errors = self.__port_info(port).split("\n")
        return "\n".join([line.strip() for line in errors if "error" in line.lower() or "CRC" in line])

    @validate_huawei_ce6865_port()
    @BaseDevice.lock_session
    def __port_info(self, port) -> str:
        """
        ## Возвращаем полную информацию о порте.

        Через команду:

            > display interface {port}

        :param port: Номер порта, для которого требуется получить информацию
        """

        return self.send_command(f"display interface {port}")

    @BaseDevice.lock_session
    @validate_huawei_ce6865_port()
    def reload_port(self, port, save_config=True) -> str:
        """
        ## Перезагружает порт

        Переходим в режим конфигурирования:

            > system-view

        Переходим к интерфейсу:

            [sys-view] interface {port}

        Перезагружаем порт:

            [sys-view-port] shutdown
            [sys-view-port] undo shutdown

        Выходим из режима конфигурирования:

            [sys-view-port] quit
            [sys-view] quit

        :param port: Порт для перезагрузки
        :param save_config: Если True, конфигурация будет сохранена на устройстве, defaults to True (optional)
        """

        self._select_interface(port)

        self.session.sendline("shutdown")
        sleep(1)
        self.session.sendline("undo shutdown")

        self._quit_from_interface_with_commit()

        r = (self.session.before or b"").decode(errors="ignore")

        self.lock = False
        s = self.save_config() if save_config else "Without saving"
        return r + s

    @BaseDevice.lock_session
    @validate_huawei_ce6865_port()
    def set_port(self, port, status: Literal["up", "down"], save_config=True) -> str:
        """
        ## Устанавливает статус порта на коммутаторе **up** или **down**

        Переходим в режим конфигурирования:

            > system-view

        Переходим к интерфейсу:

            [sys-view] interface {port}

        Меняем состояние порта:

            [sys-view-port] {shutdown|undo shutdown}

        Выходим из режима конфигурирования:

            [sys-view-port] quit
            [sys-view] quit

        :param port: Порт
        :param status: "up" или "down"
        :param save_config: Если True, конфигурация будет сохранена на устройстве, defaults to True (optional)
        """

        self._select_interface(port)

        if status == "up":
            self.session.sendline("undo shutdown")
        elif status == "down":
            self.session.sendline("shutdown")
        self.session.expect(r"\[\S+\]")

        self._quit_from_interface_with_commit()

        r = (self.session.before or b"").decode(errors="ignore")

        self.lock = False
        s = self.save_config() if save_config else "Without saving"
        return r + s

    @BaseDevice.lock_session
    @validate_huawei_ce6865_port()
    def get_port_config(self, port) -> str:
        """
        ## Выводим конфигурацию порта

        Используем команду:

            > display current-configuration interface {port}
        """

        config = self.send_command(
            f"display current-configuration interface {port}",
            expect_command=False,
            before_catch=r"#",
        )
        return config

    @BaseDevice.lock_session
    @validate_huawei_ce6865_port(if_invalid_return={"error": "Неверный порт", "status": "fail"})
    def set_description(self, port: str, desc: str) -> dict:
        """
        ## Устанавливаем описание для порта предварительно очистив его от лишних символов

        Переходим в режим конфигурирования:

            > system-view

        Переходим к интерфейсу:

            [sys-view] interface {port}

        Если была передана пустая строка для описания, то очищаем с помощью команды:

            [sys-view-port] undo description

        Если **desc** содержит описание, то используем команду для изменения:

            [sys-view-port] description {desc}

        Если длина описания больше чем допустимо на оборудовании, то отправляем ```"Max length:{number}"```

        Выходим из режима конфигурирования:

            [sys-view-port] quit
            [sys-view] quit

        :param port: Порт, для которого вы хотите установить описание
        :param desc: Описание, которое вы хотите установить для порта
        :return: Вывод команды смены описания
        """

        self._select_interface(port)

        desc = self.clear_description(desc)  # Очищаем описание от лишних символов

        if desc == "":
            # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            status = self.send_command("undo description", expect_command=False)

        else:  # В другом случае, меняем описание на оборудовании
            status = self.send_command(f"description {desc}", expect_command=False)

        if "Wrong parameter found" in status:
            # Если длина описания больше чем доступно на оборудовании
            output = self.send_command("description ?")
            max_length = int(self.find_or_empty(r"no more than (\d+) characters", output) or "0")
            return {
                "max_length": max_length,
                "error": "Too long",
                "port": port,
                "status": "fail",
            }

        self._quit_from_interface_with_commit()

        self.lock = False
        return {
            "description": desc,
            "port": port,
            "status": "changed" if desc else "cleared",
            "saved": self.save_config(),
        }

    @BaseDevice.lock_session
    def get_device_info(self) -> dict:
        return {}

    @BaseDevice.lock_session
    def get_current_configuration(self) -> io.BytesIO:
        config = self.send_command("display current-configuration", expect_command=True)
        config = re.sub(r"[ ]+\n[ ]+(?=\S)", "", config.strip())
        return io.BytesIO(config.encode())

    def _select_interface(self, interface: str) -> None:
        """
        Функция выбирает конкретный интерфейс в режиме системного просмотра.

        :param interface: Параметр «interface» — это строка, представляющая имя сетевого интерфейса
        """
        self.session.sendline("system-view")
        self.session.sendline(f"interface {interface}")
        self.session.expect(rf"{interface}\]$")

    def _quit_from_interface_with_commit(self) -> None:
        """
        Функция выходит из интерфейса и фиксирует все изменения, если есть какие-либо незафиксированные конфигурации.
        """
        self.session.sendline("quit")
        self.session.expect(self.prompt)
        self.session.sendline("quit")
        if self.session.expect([self.prompt, "Uncommitted configurations found"]):
            self.send_command("Y")
