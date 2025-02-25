import io
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from time import sleep
from typing import Literal, Dict, Optional

from ..base.device import BaseDevice, AbstractConfigDevice, AbstractCableTestDevice
from ..base.helpers import interface_normal_view, parse_by_template
from ..base.types import (
    COOPER_TYPES,
    FIBER_TYPES,
    InterfaceListType,
    InterfaceVLANListType,
    MACListType,
    MACTableType,
    MACType,
    VlanTableType,
    DeviceAuthDict,
    InterfaceType,
    PortInfoType,
)
from ..base.validators import validate_and_format_port_as_normal


@dataclass
class _PortInfo:
    info: str
    exp: datetime


class Huawei(BaseDevice, AbstractConfigDevice, AbstractCableTestDevice):
    """
    # Для оборудования от производителя Huawei

    Проверено для:
     - S2403TP
     - S2326TP
    """

    prompt = r"<\S+>$|\[\S+\]$|Unrecognized command"
    space_prompt = r"---- More ----"
    mac_format = r"[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}"
    vendor = "Huawei"

    def __init__(
        self,
        session,
        ip: str,
        auth: DeviceAuthDict,
        model="",
        snmp_community: str = "",
    ):
        """
        ## При инициализации заходим в привилегированный режим, но остаемся на уровне просмотра

        prompt = ```>```

        Определяем:

         - Модель
         - MAC
         - Серийный номер

        :param session: Это объект сеанса pexpect c установленной сессией оборудования
        :param ip: IP-адрес устройства, к которому вы подключаетесь
        :param auth: словарь, содержащий имя пользователя и пароль для устройства
        :param model: Модель коммутатора. Это используется для определения подсказки
        """

        super().__init__(session, ip, auth, model, snmp_community)
        # Заходим в привилегированный режим
        self.session.sendline("super")
        v = session.expect(
            [
                "Unrecognized command|Now user privilege is 3 level",  # 0 - huawei-2326
                "[Pp]ass",  # 1 - huawei-2403 повышение уровня привилегий
                "User privilege level is",  # 2 - huawei-2403 уже привилегированный
            ]
        )
        if v == 1:
            # Отправляем пароль от привилегированного режима
            self.session.sendline(self.auth["privilege_mode_password"])

        if self.session.expect(
            [
                r"<\S+>",  # 0 - режим просмотра
                r"\[\S+\]",  # 1 - режим редактирования
            ]
        ):
            # Если находимся в режиме редактирования, то понижаем до режима просмотра
            self.session.sendline("quit")
            self.session.expect(r"<\S+>$")

        version = self.send_command("display version")
        # Нахождение модели устройства.
        self.model = self.find_or_empty(r"Quidway (\S+) [Routing Switch]*uptime", version)

        if "S2403" in self.model:
            manuinfo = self.send_command("display device manuinfo")
            # Нахождение MAC-адреса устройства.
            self.mac = self.find_or_empty(r"MAC ADDRESS\s+:\s+(\S+)", manuinfo)
            # Нахождение серийного номера устройства.
            self.serialno = self.find_or_empty(r"DEVICE SERIAL NUMBER\s+:\s+(\S+)", manuinfo)

        elif "S2326" in self.model:
            mac = self.send_command("display bridge mac-address")
            # Нахождение mac адреса устройства.
            self.mac = self.find_or_empty(r"System Bridge Mac Address\s+:\s+(\S+)\.", mac)

            elabel = self.send_command("display elabel")
            # Нахождение серийного номера устройства.
            self.serialno = self.find_or_empty(r"BarCode=(\S+)", elabel)

        elif "S3328" in self.model or "S3352" in self.model:
            # Нахождение mac адреса устройства Проверено для S3328 S3352.
            arp_output = self.send_command("display arp | include Vlanif")
            mac_pattern = re.compile(
                r"(?P<MAC_Address>[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4})(?P<vlan>\s+I\s-\s+Vlanif\d+)"
            ).search(arp_output)
            self.mac = mac_pattern.group("MAC_Address") if mac_pattern else ""

            elabel = self.send_command("display elabel")
            self.serialno = self.find_or_empty(r"BarCode=(\S+)", elabel)

        self.__ports_info: Dict[str, _PortInfo] = {}

    @BaseDevice.lock_session
    def save_config(self):
        """
        ## Сохраняем конфигурацию оборудования командой:

            > save
              Are you sure [Y/N] Y

        Если конфигурация уже сохраняется, то будет выведено ```System is busy```,
        в таком случае ожидаем 2 секунды

        Ожидаем ответа от оборудования **successfully**,
        если нет, то пробуем еще 2 раза, в противном случае ошибка сохранения
        """

        n = 1
        while n <= 3:
            self.session.sendline("save")
            self.session.expect(r"[Aa]re you sure.*\[Y\/N\]")
            self.session.sendline("Y")
            self.session.sendline("\n")
            match = self.session.expect([self.prompt, r"successfully", "busy in saving"], timeout=30)
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

        Команда на оборудовании S2403:

            > display brief interface

        Команда на оборудовании S2326:

            > display interface description

        :return: ```[ ('name', 'status', 'desc'), ... ]```
        """

        output = ""
        if "S2403" in self.model:
            ht = "huawei-2403"
            output = self.send_command("display brief interface")
        elif "S2326" in self.model:
            ht = "huawei-2326"
            output = self.send_command("display interface description")
        else:
            ht = "huawei"

        result = parse_by_template(f"interfaces/{ht}.template", output)

        interfaces = []
        for port_name, link_status, desc in result:
            if re.match("^(NULL|A|V)", port_name):
                continue

            status: InterfaceType = "up"
            if "*" in link_status.lower() or "adm" in link_status.lower() or "admin" in link_status.lower():
                status = "admin down"
            elif "down" in link_status.lower():
                status = "down"

            interfaces.append((port_name, status, desc))

        return interfaces

    @BaseDevice.lock_session
    def get_vlan_table(self) -> VlanTableType:
        """
        ## Возвращаем список  VLAN, описание и порт для данного оборудования.

        Команда на оборудовании:

            # display vlan

         :return: ```[ ('vid', 'port,port,port','vlan name',), ... ]```
        """
        vlan_str = self.send_command("show vlan", expect_command=False)
        # Regex pattern to capture VLAN details including VID, VLAN Name, and Member Ports
        vlan_lines = vlan_str.splitlines()
        # Split into ports and description sections
        second_header_index = 7
        for i, line in enumerate(vlan_lines):
            if line.startswith("VID  Status"):
                second_header_index = i
                break

        ports_lines = vlan_lines[7:second_header_index]  # Skip the header lines
        desc_lines = vlan_lines[second_header_index + 1 :]  # Skip header and separator

        # Process ports section
        port_vlans = []
        current_vlan: dict = {}
        for line in ports_lines:
            if line.startswith("VID  Type") or line.startswith("----"):
                continue
            match = re.match(r"^(\d+)\s+(\w+)\s+(.*)", line)
            if match:
                if current_vlan:
                    port_vlans.append(current_vlan)
                vid = int(match.group(1))
                ports: list[str] = match.group(3).split()
                current_vlan = {"vid": vid, "ports": ports}
            else:
                # Continuation line
                if current_vlan:
                    ports = line.strip().split()
                    current_vlan["ports"].extend(ports)
        if current_vlan:
            port_vlans.append(current_vlan)

        # Process description section
        desc_vlans = {}
        for line in desc_lines:
            if line.startswith("----"):
                continue
            parts = re.split(r"\s{2,}", line.strip())
            if len(parts) >= 6:
                vid = int(parts[0])
                desc = parts[-1]
                desc_vlans[vid] = desc

        # Merge the data
        result = []
        for vlan in port_vlans:
            vid = vlan["vid"]
            ports = vlan["ports"]
            # Clean ports
            cleaned_ports = []
            for port in ports:
                # Split on colon to remove prefixes like UT: or TG:
                port_part = port.split(":")[-1]
                # Remove (U) or (D) at the end
                port_clean = re.sub(r"\([UD]\)$", "", port_part)
                cleaned_ports.append(port_clean)
            ports_str = ", ".join(cleaned_ports)
            description = desc_vlans.get(vid, "")
            result.append((vid, ports_str, description))

        return result

    @BaseDevice.lock_session
    def get_vlans(self) -> InterfaceVLANListType:
        """
        ## Возвращаем список всех интерфейсов и его VLAN на коммутаторе.

        Для начала получаем список всех интерфейсов через метод **get_interfaces()**

        Затем для каждого интерфейса смотрим конфигурацию

            > display current-configuration interface {port}

        Выбираем строчки, в которых указаны VLAN:

         - ```vlan {vid}...```

        кроме:

         - ```undo vlan {vid}...```

        :return: ```[ ('name', 'status', 'desc', ['{vid}', '{vid},{vid},...{vid}', ...] ), ... ]```
        """
        self.lock = False
        interfaces: InterfaceListType = self.get_interfaces()
        self.lock = True

        result: InterfaceVLANListType = []
        for intf, status, desc in interfaces:
            if re.match("^(V|NU|A)", intf):
                continue

            output = self.send_command(
                f"display current-configuration interface {interface_normal_view(intf)}",
                expect_command=False,
            )

            # Use the extract_vlans method to parse VLANs for the interface is work for S2326 tested
            vlans = self._extract_vlans(output)

            # Check if there are any VLANs before appending
            if vlans:  # This ensures you don't append empty VLAN lists
                result.append((intf, status, desc, vlans))
            else:
                result.append((intf, status, desc, []))  # Or append an empty list if no VLANs found

        return result

    def _extract_vlans(self, interface_output: str) -> list:
        """
        Extract VLANs from the interface configuration.

        :param interface_output: Output of the command `display current-configuration interface {port}`
        :return: A sorted list of extracted VLANs
        """
        # Remove lines with "undo" to avoid conflicts
        cleaned_output = re.sub(r"^ undo .+", "", interface_output, flags=re.MULTILINE)

        # Extract tagged VLANs if present
        tagged_vlans = re.findall(r"port hybrid tagged vlan ([\d\s,to]+)", cleaned_output)
        # If a single string is returned, convert it to a list of one element
        if isinstance(tagged_vlans, str):
            tagged_vlans = [tagged_vlans]
        tagged_vlans = self._expand_vlan_ranges(tagged_vlans)

        # Extract trunk VLANs if present
        trunk_vlans = re.findall(r"port trunk allow-pass vlan ([\d\s,to]+)", cleaned_output)
        if isinstance(trunk_vlans, str):
            trunk_vlans = [trunk_vlans]
        trunk_vlans = self._expand_vlan_ranges(trunk_vlans)

        # Extract untagged VLANs if present
        untagged_vlans = re.findall(r"port hybrid untagged vlan ([\d\s]+)", cleaned_output)
        untagged_vlans = [int(vlan) for vlan in " ".join(untagged_vlans).split()]

        # Extract PVID VLAN if present
        pvid_vlan = re.findall(r"port hybrid pvid vlan (\d+)", cleaned_output)
        pvid_vlan = [int(vlan) for vlan in pvid_vlan]

        # Combine all VLANs and remove duplicates
        all_vlans = set(tagged_vlans + untagged_vlans + trunk_vlans + pvid_vlan)
        return sorted(all_vlans)

    @staticmethod
    def _expand_vlan_ranges(vlan_ranges: list) -> list:
        """
        Expand VLAN ranges into individual VLANs.

        :param vlan_ranges: List of VLAN ranges as strings, e.g., ["10 to 14", "3456"]
        :return: List of individual VLANs
        """
        vlans: list = []
        # print(f"Raw vlan_ranges: {vlan_ranges}")  # Debug print to check input

        for part in vlan_ranges:
            # print(f"Processing: {part}")  # Debug print to see what's being processed
            part = part.strip(",")  # Remove trailing commas or delimiters
            parts = part.split()  # Split by spaces for individual VLANs and ranges

            # Process each part in the string
            for i, subpart in enumerate(parts):
                if "to" in subpart:  # Handle VLAN ranges
                    if i > 0 and i + 1 < len(parts):
                        try:
                            start = int(parts[i - 1])  # Get the start of the range
                            end = int(parts[i + 1])  # Get the end of the range
                            vlans.extend(
                                range(start, end + 1)
                            )  # Add all VLANs between start and end inclusive
                        except ValueError:
                            pass
                            # print(f"Invalid range: {parts[i - 1]} to {parts[i + 1]}. Skipping.")  # Log invalid range

                elif subpart.isdigit():  # Handle single VLAN numbers
                    vlans.append(int(subpart))

        return vlans

    @staticmethod
    def normalize_interface_name(intf: str) -> str:
        return interface_normal_view(intf)

    @BaseDevice.lock_session
    def get_mac_table(self) -> MACTableType:
        """
        ## Возвращаем список из VLAN, MAC-адреса, тип и порт для данного оборудования.

        Команда на оборудовании:

            # display mac-address

        С помощью регулярного выражения находим необходимые данные в выводе команды.

        Пример для S2403TP:

            0100-5e00-01bb  711       Learned        Ethernet1/0/8            NOAGED
            309c-2307-69c3  711       Learned        GigabitEthernet1/1/2     AGING

        Пример для S2326TP:

            88c3-9711-2aff 713/-                             Eth0/0/4            security
            90f6-52a9-ca13 713/-                             GE0/0/1             dynamic

        :return: ```[ ({int:vid}, '{mac}', '{type:static|dynamic|security}', '{port}'), ... ]```
        """

        def format_type(type_: str) -> MACType:
            if type_.lower() == "noaged":
                return "static"
            if type_.lower() == "aging":
                return "dynamic"
            return "security"

        mac_str = self.send_command("display mac-address", expect_command=False)
        mac_table = re.findall(
            rf"({self.mac_format})\s+(\d+)\S*\s+\S*\s+([GEF]\S+)\s+([sdAN]\S+).*\n",
            mac_str,
            flags=re.IGNORECASE,
        )
        return [(int(vid), mac, format_type(type_), port) for mac, vid, port, type_ in mac_table]

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal(if_invalid_return=[])
    def get_mac(self, port) -> MACListType:
        """
        ## Возвращаем список из VLAN и MAC-адреса для данного порта.

        Команда на оборудовании S2403:

            > display mac-address interface {port}

        Команда на оборудовании S2326:

            > display mac-address {port}

        В случае неудачи:

            > display mac-address dynamic {port}
            > display mac-address secure-dynamic {port}

        :param port: Номер порта коммутатора
        :return: ```[ ('vid', 'mac'), ... ]```
        """

        mac_list = []

        if "2403" in self.model:
            mac_str = self.send_command(f"display mac-address interface {port}")
            for i in re.findall(rf"({self.mac_format})\s+(\d+)\s+\S+\s+\S+\s+\S+", mac_str):
                mac_list.append(i[::-1])

        elif "2326" in self.model:
            mac_str = self.send_command(f"display mac-address {port}")

            if "Wrong parameter" in mac_str:
                # Если необходимо ввести тип
                mac_str1 = self.send_command(f"display mac-address dynamic {port}", expect_command=False)
                mac_str2 = self.send_command(
                    f"display mac-address secure-dynamic {port}", expect_command=False
                )
                mac_str = mac_str1 + mac_str2

            for i in re.findall(r"(" + self.mac_format + r")\s+(\d+)", mac_str):
                mac_list.append(i[::-1])

        return mac_list

    @validate_and_format_port_as_normal()
    def __get_port_info(self, port: str):
        """
        ## Возвращаем полную информацию о порте.

        Через команду:

            > display interface {port}

        :param port: Номер порта, для которого требуется получить информацию
        """

        port_info: Optional[_PortInfo] = self.__ports_info.get(port, None)
        now = datetime.now()
        if port_info is None or port_info.exp < now:
            new_port_info = _PortInfo(
                info=self.send_command(f"display interface {port}"),
                exp=now + timedelta(seconds=5),
            )
            self.__ports_info[port] = new_port_info

        return self.__ports_info[port].info

    def get_port_type(self, port) -> str:
        """
        ## Возвращает тип порта

        :param port: Порт для проверки
        :return: "SFP", "COPPER", "COMBO-FIBER", "COMBO-COPPER" или "?"
        """

        res = self.__get_port_info(port)

        # Определение аппаратного типа порта.
        type_ = self.find_or_empty(r"Port hardware type is (\S+)|Port Mode: (.*)", res)

        if type_:
            # Тип порта
            type_ = type_[0] if type_[0] else type_[1]

            if "COMBO" in type_:
                # Определяем какой режим комбо порта задействован
                return "COMBO-" + self.find_or_empty(r"Current Work Mode: (\S+)", res)

            if "FIBER" in type_ or "SFP" in type_:
                return "SFP"

            if "COPPER" in type_:
                return "COPPER"

            sub_type = self.find_or_empty(r"\d+_BASE_(\S+)", type_)
            if sub_type in COOPER_TYPES:
                return "COPPER"
            if sub_type in FIBER_TYPES:
                return "FIBER"

        return "?"

    def get_port_errors(self, port):
        """
        ## Выводим ошибки на порту

        :param port: Порт для проверки на наличие ошибок
        """

        errors = self.__get_port_info(port).split("\n")
        return "\n".join([line.strip() for line in errors if "error" in line.lower() or "CRC" in line])

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal()
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

        self.session.sendline("system-view")
        self.session.sendline(f"interface {port}")
        self.session.sendline("shutdown")
        sleep(1)
        self.session.sendline("undo shutdown")
        self.session.sendline("quit")
        self.session.expect(self.prompt)
        self.session.sendline("quit")
        self.session.expect(self.prompt)
        r = (self.session.before or b"").decode(errors="ignore")

        self.lock = False
        s = self.save_config() if save_config else "Without saving"
        return r + s

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal()
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

        self.session.sendline("system-view")
        self.session.sendline(f"interface {port}")
        if status == "up":
            self.session.sendline("undo shutdown")
        elif status == "down":
            self.session.sendline("shutdown")
        self.session.expect(r"\[\S+\]")
        self.session.sendline("quit")
        self.session.expect(self.prompt)
        self.session.sendline("quit")
        self.session.expect(self.prompt)
        r = (self.session.before or b"").decode(errors="ignore")

        self.lock = False
        s = self.save_config() if save_config else "Without saving"
        return r + s

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal()
    def get_port_config(self, port):
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
    @validate_and_format_port_as_normal(if_invalid_return={"error": "Неверный порт", "status": "fail"})
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

        self.session.sendline("system-view")
        self.session.sendline(f"interface {port}")

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

        self.session.sendline("quit")
        self.session.expect(self.prompt)
        self.session.sendline("quit")
        self.session.expect(self.prompt)
        self.lock = False
        return {
            "description": desc,
            "port": port,
            "status": "changed" if desc else "cleared",
            "saved": self.save_config(),
        }

    def __parse_virtual_cable_test_data(self, data: str) -> dict:
        """
        ## Эта функция анализирует данные виртуального теста кабеля и возвращает словарь проанализированных данных.

        :param data: Данные для разбора
        """
        parse_data: dict[str, str | dict[str, str]] = {"status": "Don't support Cable Diagnostic"}

        if "not support" in data:
            return parse_data

        if "2326" in self.model:
            # Для Huawei 2326
            pair1_status = self.find_or_empty(r"Pair A state: (\S+)", data).lower()
            pair2_status = self.find_or_empty(r"Pair B state: (\S+)", data).lower()
            pair1_len = self.find_or_empty(r"Pair A length: (\d+)meter", data)
            pair2_len = self.find_or_empty(r"Pair B length: (\d+)meter", data)
            parse_data = {
                "len": "-",
                "status": "",
                "pair1": {"status": pair1_status, "len": pair1_len},
                "pair2": {"status": pair2_status, "len": pair2_len},
            }

            if pair1_status == pair2_status == "ok":
                # Вычисляем среднюю длину
                parse_data = {"len": str((int(pair1_len) + int(pair2_len)) / 2), "status": "Up"}

            else:
                # Порт выключен
                parse_data["status"] = "Down"

        elif "2403" in self.model:
            # Для Huawei 2403
            status = self.find_or_empty(r"Cable status: (normal)", data) or self.find_or_empty(
                r"Cable status: abnormal\((\S+)\),", data
            )
            parse_data = {
                "len": self.find_or_empty(r"(\d+) meter", data),
                "status": "Up" if status == "normal" else status.capitalize(),
            }

        return parse_data

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal(if_invalid_return={"len": "-", "status": "Неверный порт"})
    def virtual_cable_test(self, port: str):
        """
        Эта функция запускает диагностику состояния линии на порту оборудования

        Переходим в режим конфигурирования:

            > system-view

        Переходим к интерфейсу:

            [sys-view] interface {port}

        Запускаем тест:

            [sys-view-port] virtual-cable-test

        Функция возвращает данные в виде словаря.
        В зависимости от результата диагностики некоторые ключи могут отсутствовать за ненадобностью.

        ```python
        {
            "len": "-",         # Длина кабеля в метрах, либо "-", когда не определено
            "status": "",       # Состояние на порту (Up, Down, Open, Short)
            "pair1": {
                "status": "",   # Статус первой пары (Open, Short)
                "len": "",      # Длина первой пары в метрах
            },
            "pair2": {
                "status": "",   # Статус второй пары (Open, Short)
                "len": "",      # Длина второй пары в метрах
            }
        }
        ```

        :param port: Порт для тестирования
        :return: Словарь с данными тестирования
        """
        port_type = self.get_port_type(port)
        if port_type in ["COPPER", "COMBO-COPPER"]:
            self.session.sendline("system-view")
            self.session.sendline(f"interface {port}")
            self.session.expect(self.prompt)
            self.session.sendline("virtual-cable-test")
            self.session.expect("virtual-cable-test")
            if self.session.expect([self.prompt, "continue"]):  # Требуется подтверждение?
                self.session.sendline("Y")
                self.session.expect(self.prompt)
            cable_test_data = (self.session.before or b"").decode("utf-8")

            self.session.sendline("quit")
            self.session.expect(self.prompt)
            self.session.sendline("quit")
            self.session.expect(self.prompt)
            return self.__parse_virtual_cable_test_data(cable_test_data)  # Парсим полученные данные
        elif port_type in ["SFP", "COMBO-FIBER"]:
            sfp_parameter_data = self.send_command(
                f"display transceiver diagnosis interface {port}", expect_command=True
            )
            return {"sfp": self.__parse_sfp_diagnostics(sfp_parameter_data)}

        return {"len": "-", "status": "Unknown"}

    @staticmethod
    def __parse_sfp_diagnostics(output: str) -> dict:
        """
            Parses SFP transceiver diagnostic information using regex.

            :param output: String containing the transceiver diagnostic data.
            :return: Dictionary with parsed values.
            example:
             {
            "TxPower": {
                "Current": -5.2,
                "Low Warning": -10.0,
                "High Warning": 0.0,
                "Status": "normal"
            },
            "RxPower": {
                "Current": -7.1,
                "Low Warning": -15.0,
                "High Warning": 0.0,
                "Status": "normal"
            },
            "Temperature": {
                "Current": 45.0,
                "Low Warning": 30.0,
                "High Warning": 70.0,
                "Status": "normal"
            },
            "Current": {
                "Current": 100.0,
                "Low Warning": 50.0,
                "High Warning": 200.0,
                "Status": "normal"
            },
            "Voltage": {
                "Current": 3.3,
                "Low Warning": 2.8,
                "High Warning": 3.6,
                "Status": "normal"
            }
        }

        """
        pattern = re.compile(
            r"(?P<parameter>[\w.()]+)\s+"
            r"(?P<current_value>-?\d+\.\d+)\s+"
            r"(?P<low_warning>-?\d+\.\d+)\s+"
            r"(?P<high_warning>-?\d+\.\d+)\s+"
            r"(?P<status>\w+)"
        )

        results = {}
        for match in pattern.finditer(output):
            parameter = match.group("parameter").strip()
            results[parameter] = {
                "Current": float(match.group("current_value")),
                "Low Warning": float(match.group("low_warning")),
                "High Warning": float(match.group("high_warning")),
                "Status": match.group("status"),
            }

        return results

    def get_port_info(self, port: str) -> PortInfoType:
        return {"type": "text", "data": self.__get_port_info(port)}

    @BaseDevice.lock_session
    def get_device_info(self) -> dict:
        return {}

    @BaseDevice.lock_session
    def get_current_configuration(self) -> io.BytesIO:
        config = self.send_command("display current-configuration", expect_command=True)
        config = re.sub(r"[ ]+\n[ ]+(?=\S)", "", config.strip())
        return io.BytesIO(config.encode())
