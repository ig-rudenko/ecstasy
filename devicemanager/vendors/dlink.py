import io
import re
from functools import partial
from time import sleep
from typing import Literal, Any

import textfsm

from .base.device import BaseDevice, AbstractConfigDevice, AbstractCableTestDevice
from .base.factory import AbstractDeviceFactory
from .base.helpers import range_to_numbers, parse_by_template
from .base.types import (
    TEMPLATE_FOLDER,
    InterfaceVLANListType,
    InterfaceListType,
    MACListType,
    MACTableType,
    MACType,
    VlanTableType,
    DeviceAuthDict,
    InterfaceType,
    PortInfoType,
)
from .base.validators import validate_and_format_port


def validate_port(port: str) -> str | None:
    """
    Проверяем порт на валидность для D-Link.

    >>> validate_port("1/2")
    '2'
    >>> validate_port("23")
    '23'
    >>> validate_port("26(C)")
    '26'
    >>> validate_port("уфы(C)")
    None

    :return Отформатированный порт или None, если был передан неверный.
    """

    port = port.strip()
    if re.findall(r"^\d/\d+$", port):
        # Если порт представлен в виде "1/2"
        port = re.sub(r"^\d/", "", port)  # Оставляем только "2"
    elif re.findall(r"^\d+$|^\d+\s*\([FC]\)$", port):
        port = re.sub(r"\D", "", port)
    else:
        port = ""
    if port.isdigit():
        return port

    return None


# Создаем свой декоратор для проверки портов
dlink_validate_and_format_port = partial(validate_and_format_port, validator=validate_port)


class Dlink(BaseDevice, AbstractConfigDevice, AbstractCableTestDevice):
    """
    Для оборудования от производителя D-Link

    Проверено для:
     - DES-1228
     - DES-3028
     - DES-3200
     - DES-3526
     - DGS-1210
     - DGS-3420

    """

    prompt = r"\S+#"
    space_prompt = None
    mac_format = r"\S\S-" * 5 + r"\S\S"
    vendor = "D-Link"

    def __init__(
        self,
        session,
        ip: str,
        auth: DeviceAuthDict,
        model: str = "",
        snmp_community: str = "",
    ):
        """
        При инициализации повышаем уровень привилегий до уровня администратора командой:

            # enable admin

        Отключаем постраничный вывод командой:

            # disable clipaging

        Дополнительно смотрим характеристики устройства:

            # show switch

          - MAC
          - модель
          - серийный номер

        :param session: Это объект сеанса pexpect c установленной сессией оборудования
        :param ip: IP-адрес устройства, к которому вы подключаетесь
        :param auth: словарь, содержащий имя пользователя и пароль для устройства
        :param model: Модель коммутатора
        """
        super().__init__(session, ip, auth, model, snmp_community)

        status = True
        # Повышает уровень привилегий до уровня администратора
        self.session.sendline("enable admin")

        if not session.expect(["[Pp]ass", r"You already have"]):
            # 0 - ввод пароля  # 1 - уже администратор
            # Вводим пароль администратора
            self.session.sendline(self.auth["privilege_mode_password"])

        # Проверка prompt или строки "Fail!"
        while self.session.expect([self.prompt, "Fail!"]):
            self.session.sendline("\n")
            print(self.ip, "privilege_mode_password wrong!")
            status = False
        if status:
            # отключение режима постраничного вывода
            self.session.sendline("disable clipaging")
            self.session.expect(self.prompt)

        # Уровень администратора
        self._admin_status: bool = status

        # Смотрим характеристики устройства
        version = self.send_command("show switch")
        self.mac = self.find_or_empty(r"MAC Address\s+:\s+(\S+-\S+-\S+-\S+-\S+-\S+)", version)
        self.model = self.model or self.find_or_empty(r"Device Type\s+:\s+(\S+)\s", version)
        self.serialno = self.find_or_empty(r"Serial Number\s+:\s+(\S+)", version)

    @BaseDevice.lock_session
    def save_config(self):
        """
        Сохраняем конфигурацию оборудования командой:

            # save

        Ожидаем ответа от оборудования **Success** или **Done**,
        если нет, то ошибка сохранения
        """
        self.session.sendline("save")
        if self.session.expect([self.prompt, r"[Ss]uccess|[Dd]one"]):
            self.session.expect(self.prompt)
            return self.SAVED_OK
        return self.SAVED_ERR

    def send_command(
        self,
        command: str,
        before_catch: str | None = None,
        expect_command=False,
        num_of_expect=10,
        space_prompt=None,
        prompt=None,
        pages_limit=None,
        command_linesep="\n",
    ):
        return super().send_command(
            command,
            before_catch=before_catch or command,
            expect_command=expect_command,
            num_of_expect=num_of_expect,
            space_prompt=space_prompt,
            prompt=prompt,
            pages_limit=pages_limit,
            command_linesep=command_linesep,
        )

    @BaseDevice.lock_session
    def get_interfaces(self) -> InterfaceListType:
        """
        Эта функция возвращает список всех интерфейсов на устройстве

        Команда на оборудовании:

            # show ports description

        :return: ```[ ('name', 'status', 'desc'), ... ]```
        """

        output = self.send_command("show ports des")

        result: list[list[str]] = parse_by_template("interfaces/d-link.template", output)

        interfaces = []
        for port_name, admin_status, link_status, desc in result:
            status: InterfaceType = "up"
            if admin_status != "Enabled":
                status = "admin down"
            elif "Down" in link_status:
                status = "down"

            interfaces.append((port_name, status, desc))

        return interfaces

    @BaseDevice.lock_session
    def get_vlan_table(self) -> VlanTableType:
        """
        ## Возвращаем список  VLAN, описание и порт для данного оборудования.

        Команда на оборудовании:

            # show vlan

         :return: ```[ ('vid', 'vlan name', 'port,port,port',), ... ]```
        """

        vlan_str = self.send_command("show vlan", expect_command=False)
        # Regex pattern to capture VLAN details including VID, VLAN Name, and Member Ports
        vlan_table: list[tuple[int, str, str]] = re.findall(
            r"VID\s+:\s+(\d+)\s+VLAN Name\s+:\s+([\w\-]+)\s+.*?Member Ports\s+:\s+([^\n]*)",  # Capture VID, VLAN Name, and Member Ports
            vlan_str,
            flags=re.DOTALL,
        )

        # Format the result as (VLAN ID, Ports, Description)
        result = []
        for vid, name, ports in vlan_table:
            # Clean the ports, removing extra spaces and handling ranges
            ports = ports.strip()
            if ports:
                # Replace ranges with comma-separated values (e.g., 1-13 -> 1,2,3,...,13)
                port_ranges = []
                for part in ports.split(","):
                    if "-" in part:
                        start, end = map(int, part.split("-"))
                        port_ranges.extend(map(str, range(start, end + 1)))
                    else:
                        port_ranges.append(part)
                ports = ", ".join(port_ranges)
            else:
                ports = ""

            result.append((int(vid), ports, name))

        return result

    @BaseDevice.lock_session
    def get_vlans(self) -> InterfaceVLANListType:
        """
        Эта функция возвращает список всех интерфейсов и его VLAN на коммутаторе.

        Смотрим список всех VLAN командой:

            # show vlan

        Вывод каждого VLAN представляет собой следующее
        Парсим полученные данные и находим соответствие между VLAN и портами

        |                             |                             |
        |:----------------------------|:----------------------------|
        | VID             : 21        |  VLAN Name       : 21       |
        | VLAN Type       : Static    |  Advertisement   : Disabled |
        | Member Ports    : 21,25-28  |                             |
        | Static Ports    : 21,25-28  |                             |

        :return: ```[ ('name', 'status', 'desc', [vid:int, vid:int, ...]), ... ]```
        """
        self.lock = False
        interfaces = self.get_interfaces()
        self.lock = True

        output = self.send_command("show vlan")
        with open(
            f"{TEMPLATE_FOLDER}/vlans_templates/d-link.template", "r", encoding="utf-8"
        ) as template_file:
            vlan_templ = textfsm.TextFSM(template_file)
            result_vlan = vlan_templ.ParseText(output)
        # сортируем и выбираем уникальные номера портов из списка интерфейсов
        port_num = set(sorted([int(re.findall(r"\d+", p[0])[0]) for p in interfaces]))

        # Создаем словарь, где ключи это кол-во портов, а значениями будут вланы на них
        ports_vlan: dict[str, list] = {str(num): [] for num in range(1, len(port_num) + 1)}

        for vlan in result_vlan:
            # Преобразуем диапазон VLAN в список чисел.
            for port in range_to_numbers(vlan[2]):
                # Добавляем вланы на порты
                ports_vlan[str(port)].append(vlan[0])
        interfaces_vlan = []  # итоговый список (интерфейсы и вланы)
        for line in interfaces:
            interfaces_vlan.append(
                (
                    line[0],
                    line[1],
                    line[2],
                    ports_vlan.get(re.sub(r"\D", "", line[0]), []),
                )
            )
        return interfaces_vlan

    @staticmethod
    def normalize_interface_name(intf: str) -> str:
        """
        ## Интерфейс должен быть числом, поэтому удаляем все остальные символы
        """
        return re.sub(r"\D", "", intf)

    @BaseDevice.lock_session
    def get_mac_table(self) -> MACTableType:
        """
        ## Возвращаем список из VLAN, MAC-адреса, тип и порт для данного оборудования.

        Команда на оборудовании:

            # show fdb

        :return: ```[ ({int:vid}, '{mac}', {'static'|'dynamic'|'security'}, '{port}'), ... ]```
        """

        def format_type(type_: str) -> MACType:
            if type_ == "DeleteOnTimeout":
                return "security"
            if type_ == "Dynamic":
                return "dynamic"
            return "static"

        mac_str = self.send_command("show fdb", expect_command=False)
        mac_table: list[tuple[str, str, str, str]] = re.findall(
            rf"(\d+)\s+\S+\s+({self.mac_format})\s+(\d+)\s+(\S+).*\n",
            mac_str,
            flags=re.IGNORECASE,
        )
        return [(int(vid), mac, format_type(type_), port) for vid, mac, port, type_ in mac_table]

    @BaseDevice.lock_session
    @dlink_validate_and_format_port(if_invalid_return=[])
    def get_mac(self, port) -> MACListType:
        """
        Эта функция возвращает список из VLAN и MAC-адреса для данного порта.

        Команда на оборудовании:

            # show fdb port {port}

        :param port: Номер порта коммутатора
        :return: ```[ ('vid', 'mac'), ... ]```
        """

        mac_str = self.send_command(f"show fdb port {port}", expect_command=False)
        # Используем регулярное выражение для поиска всех MAC-адресов и VLAN в mac_str.
        mac_lines: list[tuple[str, str]] = re.findall(
            rf"(\d+)\s+\S+\s+({self.mac_format})\s+\d+\s+\S+", mac_str
        )
        return [(int(vid), mac) for vid, mac in mac_lines]

    @dlink_validate_and_format_port(if_invalid_return="?")
    def get_port_type(self, port: str) -> str:
        """
        ## Возвращает тип порта

        :param port: Порт для проверки
        :return: "SFP", "COPPER", или "?"
        """
        res = self.send_command(f"show ports {port} media_type", expect_command=False)

        # Определяем тип порта по выводу команды
        media_type = self.find_or_empty(r"\d+\s+([A-Za-z0-9\-]+)\s+", res)

        if media_type:
            media_type = media_type.strip().upper()

            if "SFP" in media_type or "LC" in media_type or "FIBER" in media_type:
                return "SFP"

            if "BASE-T" in media_type or "COPPER" in media_type:
                return "COPPER"

        return "?"

    @BaseDevice.lock_session
    def reload_port(self, port, save_config=True) -> str:
        """
        Перезагружает порт

        Если порт передается с пометкой **C** или **F**
        Например ```25(F)```, ```26(C)```, то перезагружаем указанный medium_type

        Для порта с номером больше 23, если не был передан medium_type,
        то перезагружаем и **copper**, и **fiber**

            # config ports {port} medium_type {copper|fiber} state disable
            # config ports {port} medium_type {copper|fiber} state enable

        Для других портов не используется medium_type

            # config ports {port} state disable
            # config ports {port} state enable


        :param port: Порт для перезагрузки
        :param save_config: Если True, конфигурация будет сохранена на устройстве, defaults to True (optional)
        :return: Результат введенных команд и, если было указано, то статус сохранения конфигурации
        """

        if "F" in port:
            media_type = " medium_type fiber"
        elif "C" in port:
            media_type = " medium_type copper"
        else:
            media_type = ""

        port = validate_port(port)
        if port is None:
            return "Неверный порт"

        # Отключение порта.
        r1 = self.send_command(f"config ports {port}{media_type} state disable")
        # Проверка, не установлен ли тип порта и порт больше 23
        if not media_type and int(port) > 23:
            r1 += self.send_command(f"config ports {port} medium_type fiber state disable")

        # Задержка, позволяющая коммутатору обработать команду.
        sleep(4)

        # Включение порта.
        r2 = self.send_command(f"config ports {port}{media_type} state enable")
        # Проверка, не установлен ли тип порта и порт больше 23
        if not media_type and int(port) > 23:
            r2 += self.send_command(f"config ports {port} medium_type fiber state enable")

        self.lock = False
        # Сохранение конфигурации, если для параметра `save_config` установлено значение `True`.
        s = self.save_config() if save_config else "Without saving"
        return r1 + r2 + s

    @BaseDevice.lock_session
    def set_port(self, port, status: Literal["up", "down"], save_config=True) -> str:
        """
        Устанавливает статус порта на коммутаторе **up** или **down**

        Если порт передается с пометкой **C** или **F**
        Например ```25(F)```, ```26(C)```, то используем указанный medium_type

        Для порта с номером больше 23, если не был передан medium_type,
        то используем и **copper**, и **fiber**

            # config ports {port} medium_type {copper|fiber} state {disable|enable}

        Для других портов не используется medium_type

            # config ports {port} state {disable|enable}

        :param port: Порт
        :param status: "up" или "down"
        :param save_config: Если True, конфигурация будет сохранена на устройстве, defaults to True (optional)
        """

        if "F" in port:
            media_type = " medium_type fiber"
        elif "C" in port:
            media_type = " medium_type copper"
        else:
            media_type = ""

        # Проверка правильности порта.
        port = validate_port(port)

        if port is None:
            return "Неверный порт"

        if status == "up":
            state = "enable"
        elif status == "down":
            state = "disable"
        else:
            state = ""

        # Установка порта в заданное состояние.
        r = self.send_command(f"config ports {port}{media_type} state {state}")

        # Проверка, не установлен ли тип порта и порт больше 23
        if not media_type and int(port) > 23:
            # Проверка, является ли порт оптоволоконным портом, и если это так,
            # он установит порт в состояние, которое было передано.
            r += self.send_command(f"config ports {port} medium_type fiber state {state}")

        self.lock = False
        s = self.save_config() if save_config else "Without saving"

        # Возврат результата команды и результата функции save_config().
        return r + s

    @BaseDevice.lock_session
    @dlink_validate_and_format_port()
    def get_port_errors(self, port: str) -> str:
        """
        Получаем ошибки на порту через команду:

            # show error ports {port}

        :param port: Порт для проверки на наличие ошибок
        """

        self.session.sendline(f"show error ports {port}")

        # Если не удалось отключить clipaging
        if self.session.expect([self.prompt, "Previous Page"]):
            self.session.sendline("q")

        return (self.session.before or b"").decode()

    @BaseDevice.lock_session
    def set_description(self, port: str, desc: str) -> dict:
        """
        Устанавливаем описание для порта предварительно очистив его от лишних символов

        Если была передана пустая строка для описания, то очищаем с помощью команды:

            # config ports {port} clear_description

        Если **desc** содержит описание, то используем команду для изменения

            # config ports {port} description {desc}

        Если длина описания больше чем разрешено на оборудовании, то выводим ```"Max length:{number}"```

        :param port: Порт, для которого вы хотите установить описание
        :param desc: Описание, которое вы хотите установить для порта
        :return: Вывод команды смены описания
        """

        if "F" in port:
            media_type = " medium_type fiber"
        elif "C" in port:
            media_type = " medium_type copper"
        else:
            media_type = ""

        valid_port = validate_port(port)
        if valid_port is None:
            return {"error": "Неверный порт", "status": "fail", "port": port}

        desc = self.clear_description(desc)  # Очищаем описание от лишних символов

        if desc == "":
            # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            status = self.send_command(
                f"config ports {valid_port}{media_type} clear_description",
                expect_command=False,
                before_catch="desc",
            )

        else:  # В другом случае, меняем описание на оборудовании
            status = self.send_command(
                f"config ports {valid_port}{media_type} description {desc}",
                expect_command=False,
                before_catch="desc",
            )

        if "Next possible completions" in status:
            # Если длина описания больше чем разрешено на оборудовании
            max_length = int(self.find_or_empty(r"<desc (\d+)>", status) or "0")
            return {
                "max_length": max_length,
                "error": "Too long",
                "port": port,
                "status": "fail",
            }

        self.lock = False
        if "Success" in status:  # Успешно поменяли описание
            # Возвращаем строку с результатом работы и сохраняем конфигурацию
            return {
                "description": desc,
                "port": port,
                "status": "changed" if desc else "cleared",
                "saved": self.save_config(),
            }

        # Уникальный случай
        return {
            "description": desc,
            "port": port,
            "status": "fail",
            "error": status,
        }

    @BaseDevice.lock_session
    @dlink_validate_and_format_port(if_invalid_return={})
    def virtual_cable_test(self, port: str) -> dict:
        """
        Эта функция запускает диагностику состояния линии на порту оборудования через команду:

            # cable_diag ports {port}

        Функция возвращает данные в виде словаря.
        В зависимости от результата диагностики некоторые ключи могут отсутствовать за ненадобностью.

        ```python
        {
            "len": "-",         # Длина кабеля в метрах, либо "-", когда не определено
            "status": "",       # Состояние на порту (Up, Down, Empty)
            "pair1": {
                "status": "",   # Статус первой пары (Open, Short)
                "len": "",      # Длина первой пары в метрах
            },
            "pair2": {
                "status": "",   # Статус второй пары (Open, Short)
                "len": "",      # Длина второй пары в метрах
            },
            "sfp": {},  # Статус SFP
        }
        ```

        :param port: Порт для тестирования
        :return: Словарь с данными тестирования
        """
        port_type = self.get_port_type(port)

        if port_type in ["COPPER"]:
            diag_output = self.send_command(f"cable_diag ports {port}", expect_command=False)

            if "Available commands" in diag_output:
                return {}

            result: dict[str, Any] = {
                "len": "-",  # Длина кабеля в метрах, либо "-", когда не определено
                "status": "",  # Состояние на порту (Up, Down, Empty)
            }

            if "can't support" in diag_output or "Unknown" in diag_output:
                result["status"] = "Don't support Cable Diagnostic"
                return result

            if "No Cable" in diag_output:
                # Нет кабеля
                result["status"] = "Empty"
                return result

            if re.findall(r"Link (Up|Down)\s+OK", diag_output):
                # Если статус OK
                match = self.find_or_empty(r"\s+\d+\s+\S+\s+Link (Up|Down)\s+OK\s+(\S+)", diag_output)
                if len(match) == 2:
                    result["len"] = match[1]  # Длина
                    result["status"] = match[0]  # Up или Down
            else:
                # C ошибкой
                result["status"] = self.find_or_empty(r"\s+\d+\s+\S+\s+Link (Up|Down)", diag_output) or "None"
                # Смотрим по очереди 4 пары
                for i in range(1, 5):
                    # Нахождение пары по номеру `i`.
                    pair_n = self.find_or_empty(rf"Pair\s*{i} (\S+)\s+at\s+(\d+)", diag_output)
                    # Проверка, не является ли пара пустой.
                    if pair_n:
                        # Создаем пустой словарь для пары
                        result["pair" + str(i)] = {
                            "status": pair_n[0].lower(),  # Open, Short
                            "len": pair_n[1],  # Длина
                        }

            return result
        elif port_type in ["SFP"]:
            sfp_parameter_data = self.send_command(f"show ddm ports {port} status", expect_command=False)
            return {"sfp": self.__parse_sfp_diagnostics(sfp_parameter_data)}

        return {"len": "-", "status": "None"}

    @staticmethod
    def __parse_sfp_diagnostics(output) -> dict:
        """
        Parses SFP transceiver diagnostic information using regex.

        :param output: String containing the transceiver diagnostic data.
        :return: Dictionary with parsed values.
        example:
        {
            "TxPower": {
                "Current": -5.2,
                "Low Warning": None
                "High Warning": None
            },
            "RxPower": {
                "Current": -7.1,
                "Low Warning": None
                "High Warning": None
            },
            "Temperature": {
                "Current": 45.0,
                "Low Warning": None
                "High Warning": None
            },
            "Current": {
                "Current": 100.0,
                "Low Warning": None
                "High Warning": None
            },
            "Voltage": {
                "Current": 3.3,
                "Low Warning":  None
                "High Warning": None
            }
        }

        """
        pattern = re.compile(
            r"(?P<port>\d+)\s+"  # Match port number
            r"(?P<temperature>-?\d*\.\d+|-)\s+"  # Match Temperature (can be a dash if not present)
            r"(?P<voltage>-?\d*\.\d+|-)\s+"  # Match Voltage (can be a dash if not present)
            r"(?P<bias_current>-?\d*\.\d+|-)\s+"  # Match Bias Current (can be a dash if not present)
            r"(?P<tx_power>-?\d*\.\d+|-)\s+"  # Match TX Power (can be a dash if not present)
            r"(?P<rx_power>-?\d*\.\d+|-)"  # Match RX Power (can be a dash if not present)
        )

        results = {}
        for match in pattern.finditer(output):
            temperature = match.group("temperature") if match.group("temperature") != "-" else None
            voltage = match.group("voltage") if match.group("voltage") != "-" else None
            bias_current = match.group("bias_current") if match.group("bias_current") != "-" else None
            tx_power = match.group("tx_power") if match.group("tx_power") != "-" else None
            rx_power = match.group("rx_power") if match.group("rx_power") != "-" else None

            results = {
                "TxPower": {
                    "Current": float(tx_power) if tx_power else None,
                    "Low Warning": None,  # No placeholder, directly parsed
                    "High Warning": None,  # No placeholder, directly parsed
                },
                "RxPower": {
                    "Current": float(rx_power) if rx_power else None,
                    "Low Warning": None,  # No placeholder, directly parsed
                    "High Warning": None,  # No placeholder, directly parsed
                },
                "Temperature": {
                    "Current": float(temperature) if temperature else None,
                    "Low Warning": None,  # No placeholder, directly parsed
                    "High Warning": None,  # No placeholder, directly parsed
                },
                "Current": {
                    "Current": float(bias_current) if bias_current else None,
                    "Low Warning": None,  # No placeholder, directly parsed
                    "High Warning": None,  # No placeholder, directly parsed
                },
                "Voltage": {
                    "Current": float(voltage) if voltage else None,
                    "Low Warning": None,  # No placeholder, directly parsed
                    "High Warning": None,  # No placeholder, directly parsed
                },
            }

        return results

    @BaseDevice.lock_session
    def get_device_info(self) -> dict:
        stats = ["cpu", "ram", "flash"]
        data = {}

        for key in stats:
            value = getattr(self, f"get_{key}_utilization")()
            if isinstance(value, tuple) and all(value) or value > 0:
                data[key] = {"util": value}

        return data

    def _get_utilization(self, type_: str, expect: str):
        self.session.sendline("show utilization " + type_)
        self.session.sendcontrol("c")
        self.session.expect(self.prompt)
        output = (self.session.before or b"").decode("utf-8", errors="ignore")

        cpu_percent = self.find_or_empty(
            expect,
            output,
            flags=re.IGNORECASE,
        )
        return int(cpu_percent) if cpu_percent else -1

    def get_cpu_utilization(self) -> tuple:
        """
        ## Возвращает загрузку ЦП хоста
        """
        return (self._get_utilization("cpu", r"one minute -\s+(\d+)\s*%"),)

    def get_flash_utilization(self) -> int:
        """
        ## Возвращает использование флэш-памяти устройства
        """
        return self._get_utilization("flash", r"Utilization\s+: (\d+)\s*%")

    def get_ram_utilization(self) -> int:
        """
        ## Возвращает использование DRAM в процентах
        """
        return self._get_utilization("dram", r"Utilization\s+: (\d+)\s*%")

    def get_port_info(self, port: str) -> PortInfoType:
        return {"type": "text", "data": ""}

    def get_port_config(self, port: str) -> str:
        return ""

    @BaseDevice.lock_session
    def get_current_configuration(self) -> io.BytesIO:
        config = self.send_command(
            "show config current_config",
            expect_command=False,
            before_catch="Command: show config current_config",
        )
        config = re.sub("[\r\n]{3}", "\n", config.strip())
        return io.BytesIO(config.encode())


class DlinkFactory(AbstractDeviceFactory):
    @staticmethod
    def is_can_use_this_factory(session=None, version_output=None) -> bool:
        return version_output and "Next possible completions:" in str(version_output)

    @classmethod
    def get_device(
        cls,
        session,
        ip: str,
        snmp_community: str,
        auth: DeviceAuthDict,
        version_output: str = "",
    ) -> BaseDevice:
        return Dlink(session, ip, auth, snmp_community=snmp_community)
