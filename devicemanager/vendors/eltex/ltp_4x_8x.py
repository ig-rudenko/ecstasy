import io
import re
import time
from functools import wraps
from typing import Any, TypedDict

from .extra import reformat_ltp_interfaces_list, reformat_gpon_ports_state_output
from ..base.device import BaseDevice
from ..base.types import (
    InterfaceListType,
    InterfaceVLANListType,
    MACListType,
    MACTableType,
    MACType,
    DeviceAuthDict,
)


class _EltexLTPPortTypes(TypedDict):
    name: str
    max_number: int


def _validate_port(if_invalid_return: Any = None):
    """
    ## Декоратор для проверки правильности порта Eltex LTP

    :param if_invalid_return: что нужно вернуть, если порт неверный
    """

    if if_invalid_return is None:
        if_invalid_return = "Неверный порт"

    def validate(func):
        @wraps(func)
        def wrapper(deco_self: "EltexLTP", port, *args, **kwargs):
            port_types: dict[int, _EltexLTPPortTypes] = {
                0: {
                    "name": "front-port",
                    "max_number": deco_self.front_ports_count - 1,
                },
                1: {
                    "name": "10G-front-port",
                    "max_number": deco_self.the_10G_ports_count - 1,
                },
                2: {
                    "name": "pon-port",
                    "max_number": deco_self.gpon_ports_count - 1,
                },
            }

            # Регулярное выражения для поиска трёх типов портов на Eltex LTP 4X, 8X
            port_match: list[tuple[str]] = re.findall(
                r"^front[-port]*\s*(\d+)$|"  # `0` - front-port
                r"^10[Gg]-front[-port]*\s*(\d+)$|"  # `1` - 10G-front-port
                r"^[gp]*on[-port]*\s*(\d+(?:[/\\]?\d*)?)$",  # `2` - ont-port | gpon-port
                port,
            )
            if not port_match:
                # Неверный порт
                return if_invalid_return

            for i, port_num in enumerate(port_match[0]):
                if not port_num:
                    # Пропускаем не найденное сравнение в регулярном выражении
                    continue

                # Если порт представлен в виде `2/23`, то берем первую цифру `2` как port_num
                num = int(port_num if port_num.isdigit() else port_num.split("/")[0])

                # Проверка, меньше или равен ли номер порта максимальному количеству портов для этого типа.
                port_max_number = port_types[i]["max_number"]
                if num <= port_max_number:
                    # port_type number
                    port = f"{port_types[i]['name']} {port_num}"
                    # Вызываем метод
                    return func(deco_self, port, *args, **kwargs)

            # Неверный порт
            return if_invalid_return

        return wrapper

    return validate


class EltexLTP(BaseDevice):
    """
    # Для станционных терминалов GPON OLT - LTP-4X, LTP-8X

    Станционные терминалы, предназначенные для связи с вышестоящим оборудованием
    и организации широкополосного доступа по пассивным оптическим сетям.

    Серия представлена терминалами LTP-4X и LTP-8X с внутренним Ethernet-коммутатором с функцией RSSI,
    на четыре и восемь портов GPON соответственно.

    Связь с сетями Ethernet реализуется посредством Gigabit uplink и 10G BASE-X интерфейсов,
    для выхода в оптические сети служат интерфейсы GPON.

    Каждый интерфейс PON позволяет подключить до 128 абонентских оптических терминалов по одному волокну,
    динамическое распределение полосы DBA (dynamic bandwidth allocation).
    """

    # Регулярное выражение, соответствующее началу для ввода следующей команды.
    prompt = r"\S+#\s*$"
    # Строка, которая отображается, когда вывод команды слишком длинный и не помещается на экране.
    space_prompt = r"--More--"
    # Это переменная, которая используется для поиска файла шаблона для анализа вывода команды.
    _template_name = "eltex-ltp"
    # Регулярное выражение, которое будет соответствовать MAC-адресу.
    mac_format = r"\S\S:\S\S:\S\S:\S\S:\S\S:\S\S"  # aa.bb.cc.dd.ee.ff
    vendor = "Eltex"

    def __init__(
        self,
        session,
        ip: str,
        auth: DeviceAuthDict,
        model="LTP",
        snmp_community: str = "",
    ):
        super().__init__(session, ip, auth, model, snmp_community)

        self.model = self.model.replace(":", "-")

        # Проверяем, является ли модель LTP-4X.
        if "LTP-4X" in self.model:
            self.gpon_ports_count = 4
            self.the_10G_ports_count = 2
            self.front_ports_count = 4

        # Проверяем, является ли модель LTP-8X.
        elif "LTP-8X" in self.model:
            self.gpon_ports_count = 8
            self.the_10G_ports_count = 2
            self.front_ports_count = 8
        else:
            self.gpon_ports_count = 0
            self.the_10G_ports_count = 0
            self.front_ports_count = 0

    def send_command(
        self,
        command: str,
        before_catch: str | None = None,
        expect_command=True,
        num_of_expect=10,
        space_prompt=None,
        prompt=None,
        pages_limit=None,
        command_linesep="\r",
    ) -> str:
        return super().send_command(
            command,
            before_catch,
            expect_command,
            num_of_expect,
            space_prompt,
            prompt,
            pages_limit,
            command_linesep,
        )

    @BaseDevice.lock_session
    def save_config(self) -> str:
        """
        ## Сохраняем конфигурацию оборудования

            # commit

        Ожидаем ответа от оборудования **successfully**,
        """

        self.session.send("commit\r")
        if self.session.expect([self.prompt, r"successfully|Nothing to commit"]):
            return self.SAVED_OK
        return self.SAVED_ERR

    @BaseDevice.lock_session
    def get_interfaces(self) -> InterfaceListType:
        self.session.send("switch\r")
        self.session.expect(self.prompt)

        interfaces: list[tuple[str, str]] = []

        interfaces_10gig_output = self.send_command(
            f"show interfaces status 10G-front-port 0 - {self.the_10G_ports_count - 1}",
            expect_command=False,
        )
        interfaces += re.findall(r"(10G\S+ \d+)\s+(\S{2,})\s+", interfaces_10gig_output)

        interfaces_front_output = self.send_command(
            f"show interfaces status front-port 0 - {self.front_ports_count - 1}",
            expect_command=False,
        )
        interfaces += re.findall(r"(front\S+ \d+)\s+(\S{2,})\s+", interfaces_front_output)
        self.session.send("exit\r")
        self.session.expect(self.prompt)

        interfaces_gpon_output = self.send_command(
            f"show interface gpon-port 0-{self.gpon_ports_count - 1} state",
            expect_command=False,
        )
        valid_interfaces = reformat_ltp_interfaces_list(interfaces)
        valid_interfaces += reformat_gpon_ports_state_output(interfaces_gpon_output)
        return valid_interfaces

    @BaseDevice.lock_session
    def get_mac_table(self) -> MACTableType:
        """
        ## Возвращаем список из VLAN, MAC-адреса, dynamic и порта для данного оборудования.

        Команды на оборудовании:

            # switch
            # show mac

            VID    MAC address         Interface               Type
            ----   -----------------   ---------------------   --------
            4094   ea:28:c1:f4:dc:17   pon-port 3              Dynamic
            688    ea:28:c1:f9:dc:19   10G-front-port 1        Dynamic
            ...
            4094   ea:28:c1:f4:dd:1f   pon-port 6              Dynamic

            # exit

        :return: ```[ ({int:vid}, '{mac}', 'dynamic', '{port}'), ... ]```
        """

        self.session.send("switch\r")
        self.session.expect(self.prompt)

        output = self.send_command("show mac", expect_command=False)
        self.session.send("exit\r")
        self.session.expect(self.prompt)

        parsed: list[tuple[str, str, str, str]] = re.findall(
            rf"(\d+)\s+({self.mac_format})\s+(\S+\s\d+)\s+(\S+).*\n", output
        )

        table: MACTableType = []
        mac_type: MACType

        for vid, mac, port, type_ in parsed:
            if type_ == "Dynamic":
                mac_type = "dynamic"
            else:
                mac_type = "static"

            table.append((int(vid), mac, mac_type, port))

        return table

    @BaseDevice.lock_session
    def get_vlans(self) -> InterfaceVLANListType:
        self.lock = False
        return [(line[0], line[1], line[2], []) for line in self.get_interfaces()]

    @BaseDevice.lock_session
    @_validate_port(if_invalid_return=[])
    def get_mac(self, port: str) -> MACListType:
        """
        Команда:

            # show mac include interface {port_type} {port}

        :param port:
        :return: ```[ ('vid', 'mac'), ... ]```
        """
        port_type, port_number = port.split()
        macs_list: list[tuple[str, str]]

        if port_number.isdigit():
            self.session.send("switch\r")
            self.session.expect(self.prompt)
            macs_output = self.send_command(
                f"show mac include interface {port_type} {port_number}",
            )
            self.session.send("exit\r")
            self.session.expect(self.prompt)
            macs_list = re.findall(rf"(\d+)\s+({self.mac_format})\s+\S+", macs_output)
            return [(int(vid), mac) for vid, mac in macs_list]

        # Если указан порт конкретного ONT `0/1`, то используем другую команду
        # И другое регулярное выражение
        elif port_type == "pon-port" and re.match(r"^\d+/\d+$", port_number):
            macs_list = re.findall(
                rf"(\d+)\s+({self.mac_format})",
                self.send_command(f"show mac interface ont {port_number}"),
            )
            return [(int(vid), mac) for vid, mac in macs_list]

        # Если неверный порт
        return []

    @BaseDevice.lock_session
    @_validate_port({"type": "error", "data": "Неверный порт"})
    def get_port_info(self, port: str) -> dict:
        # Получаем тип порта и его номер
        port_type, port_number = port.split()

        if port_type == "pon-port":
            # Данные для шаблона
            data: dict[str, Any] = {}

            # Смотрим сконфигурированные ONT на данном порту
            ont_info = self.send_command(f"show interface ont {port_number} configured")
            # Парсим данные ONT
            onts_lines = sorted(
                [
                    # 0       1        2         3       4        5        6
                    # ONT ID, Status,  Equip ID, RSSI,   Serial,  Desc,    MacList
                    [line[1], line[2], line[5], line[3], line[0], line[6], []]
                    for line in re.findall(
                        r"\s+\d+\s+(\S+)\s+(\d+)\s+\d+\s+(\S+)\s+(\S+)\s+(\S*)\s+(\S+)\s*(\S*)[\r\n]",
                        ont_info,
                    )
                ],
                key=lambda x: int(x[0]),  # сортируем по возрастанию ONT ID
            )

            # Добавляем в итоговый словарь список из отсортированных по возрастанию ONT ID записей
            # сконфигурированных ONT в виде list[List], вместо list[Tuple].
            # Добавляем для каждой записи пустой список, который далее будет использоваться
            # для заполнения VLAN/MAC
            data["onts_lines"] = onts_lines

            # Общее кол-во сконфигурированных ONT на данном порту
            data["total_count"] = len(data["onts_lines"])

            data["online_count"] = 0
            # Считаем кол-во ONT online
            for line in data["onts_lines"]:
                if line[1] == "OK":
                    data["online_count"] += 1

            # Смотрим MAC на pon порту
            if port_number.isdigit():
                macs_list = re.findall(
                    rf"\s+\d+\s+\S+\s+(\d+)\s+\d+\s+\d+\s+.+\s+(\d+)\s+({self.mac_format})",
                    self.send_command(f"show mac interface gpon-port {port_number}"),
                )
            else:
                macs_list = []

            # Перебираем список macs_list и назначаем каждому ONT ID свой VLAN/MAC
            for ont_id, vlan_id, mac in macs_list:
                # Выбираем запись ONT по индексу ONT ID - int(mac_line[0])
                # Затем обращаемся к 6 элементу, в котором находится список VLAN/MAC
                # и добавляем VLAN, MAC и описание VLAN
                data["onts_lines"][int(ont_id)][6].append([vlan_id, mac, ""])

            return {
                "type": "eltex-gpon",
                "data": data,
            }

        return {"type": "text", "data": ""}

    @BaseDevice.lock_session
    @_validate_port()
    def reload_port(self, port: str, save_config=True) -> str:
        """
        ## Перезагрузка порта
        """
        port_type, port_number = port.split()
        if port_type == "pon-port" and re.match(r"^\d+/\d+$", port_number):
            # Для порта ONT вида - `0/1`
            res = self.send_command(f"send omci reset interface ont {port_number}")
            return res + "Without saving"

        if port_type == "pon-port" and re.match(r"^\d+$", port_number):
            # Для порта GPON
            self.session.send("configure terminal\r")
            self.session.expect(self.prompt)
            self.session.send(f"interface gpon-port {port_number}\r")
            self.session.expect(self.prompt)

            self.session.send("shutdown\r")
            self.session.expect(self.prompt)
            self.session.send("do commit\r")
            self.session.expect(self.prompt)

            time.sleep(1)

            self.session.send("no shutdown\r")
            self.session.expect(self.prompt)
            self.session.send("do commit\r")
            self.session.expect(self.prompt)

            self.session.send(f"exit\r")
            self.session.expect(self.prompt)
            self.session.send(f"exit\r")
            self.session.expect(self.prompt)

            self.lock = False
            return self.save_config() if save_config else "Without saving"

        return "Этот порт нельзя перезагружать"

    @BaseDevice.lock_session
    @_validate_port()
    def set_port(self, port: str, status: str, save_config=True) -> str:
        port_type, port_number = port.split()
        if port_type == "pon-port" and re.match(r"^\d+$", port_number):
            # Для порта GPON
            self.session.send("configure terminal\r")
            self.session.expect(self.prompt)
            self.session.send(f"interface gpon-port {port_number}\r")
            self.session.expect(self.prompt)

            if status == "up":
                self.session.send("no shutdown\r")
            elif status == "down":
                self.session.send("shutdown\r")

            self.session.expect(self.prompt)
            self.session.send("do commit\r")
            self.session.expect(self.prompt)
            self.session.send(f"exit\r")
            self.session.expect(self.prompt)
            self.session.send(f"exit\r")
            self.session.expect(self.prompt)

            self.lock = False
            return self.save_config() if save_config else "Without saving"

        return "Этот порт нельзя установить в " + status

    @BaseDevice.lock_session
    @_validate_port(if_invalid_return={"error": "Неверный порт", "status": "fail"})
    def set_description(self, port: str, desc: str) -> dict:
        """
        ## Устанавливаем описание для порта предварительно очистив его от лишних символов

        Переходим в режим конфигурирования:

            # configure terminal

        Переходим к интерфейсу:

            (config)# interface ont {m}/{n}

        Если была передана пустая строка для описания, то очищаем с помощью команды:

            (config-if)# no description

        Если **desc** содержит описание, то используем команду для изменения:

            (config-if)# description {desc}

        Выходим из режима конфигурирования:

            (config-if)# exit
            (config)# exit

        :param port: Порт, для которого вы хотите установить описание.
        :param desc: Описание, которое вы хотите установить для порта
        :return: Вывод команды смены описания
        """

        desc = self.clear_description(desc)

        # Получаем тип порта и его номер
        port_type, port_number = port.split()
        if port_type == "pon-port" and re.match(r"^\d+/\d+$", port_number):
            # Для порта ONT вида - `0/1`
            self.session.send("configure terminal\r")
            self.session.expect(self.prompt)
            self.session.send(f"interfaces ont {port_number}\r")
            self.session.expect(self.prompt)

            if desc == "":
                # Если строка описания пустая, то необходимо очистить описание на порту оборудования
                self.send_command("no description", expect_command=False)

            else:  # В другом случае, меняем описание на оборудовании
                self.send_command(f"description {desc}", expect_command=False)

            self.session.send("exit\r")
            self.session.expect(self.prompt)
            self.session.send("exit\r")
            self.session.expect(self.prompt)

            self.lock = False
            return {
                "description": desc,
                "port": port,
                "status": "changed" if desc else "cleared",
                "saved": self.save_config(),
            }

        return {
            "port": port,
            "status": "fail",
            "error": "Неверный порт",
        }

    @BaseDevice.lock_session
    @_validate_port()
    def get_port_config(self, port: str) -> str:
        # Получаем тип порта и его номер
        port_type, port_number = port.split()
        if port_type == "pon-port" and re.match(r"^\d+/\d+$", port_number):
            # Для порта ONT вида - `0/1`
            return self.send_command(f"show interface ont {port_number} configuration")

        return ""

    @BaseDevice.lock_session
    @_validate_port(if_invalid_return="?")
    def get_port_type(self, port: str) -> str:
        port_type, number = port.split()
        if port_type in ("10G-front-port", "pon-port"):
            return "SFP"

        self.session.send("switch\r")
        self.session.expect(self.prompt)

        media_type = self.find_or_empty(
            r"Media:\s+(\S+)",
            self.send_command(
                f"show interfaces detailed status {port_type} {number}",
                expect_command=False,
            ),
        )

        if media_type == "none":
            media_type = ""

        if "8X" in self.model and int(number) > 3:
            return "COMBO-" + media_type.upper()
        if "8X" in self.model and int(number) <= 3:
            return "COPPER"

        return "SFP"

    @BaseDevice.lock_session
    @_validate_port()
    def get_port_errors(self, port: str) -> str:
        return ""

    def get_device_info(self) -> dict:
        return {}

    @BaseDevice.lock_session
    def get_current_configuration(self, *args, **kwargs) -> io.BytesIO:
        config = self.send_command("show running-config", expect_command=True)
        return io.BytesIO(config.encode())
