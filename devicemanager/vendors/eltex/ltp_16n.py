import io
import re
from functools import wraps

from packaging.version import Version

from ..base.device import AbstractConfigDevice, BaseDevice
from ..base.types import (
    DeviceAuthDict,
    InterfaceListType,
    InterfaceVLANListType,
    MACListType,
    MACTableType,
)
from .extra import reformat_ltp_interfaces_list
from .ltp_4x_8x import _EltexLTPPortTypes


def _validate_port(if_invalid_return=None):
    """
    ## Декоратор для проверки правильности порта Eltex LTP

    :param if_invalid_return: что нужно вернуть, если порт неверный
    """

    if if_invalid_return is None:
        if_invalid_return = "Неверный порт"

    def validate(func):
        @wraps(func)
        def wrapper(deco_self: "EltexLTP16N", port, *args, **kwargs):
            port_types: dict[int, _EltexLTPPortTypes] = {
                0: {
                    "name": "front-port",
                    "max_number": 8,
                },
                1: {
                    "name": "pon-port",
                    "max_number": 16,
                },
            }

            # Регулярное выражения для поиска типов портов на Eltex LTP 16N
            port_match: list[tuple[str]] = re.findall(
                r"^front[-port]*\s*(\d+)$|"  # `0` - front-port
                r"^[gp]*on[-port]*\s*(\d+(?:[/\\]?\d*)?)$",  # `1` - ont-port | gpon-port
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


class EltexLTP16N(BaseDevice, AbstractConfigDevice):
    """
    # Для станционных терминалов GPON OLT - LTP-16N, LTP-16NT

    OLT серии LTP – станционные терминалы, предназначенные для связи с вышестоящим оборудованием
     и организации широкополосного доступа по пассивным оптическим сетям.

    Серия представлена терминалами LTP-16N и LTP-16NT.

    Связь с сетями Ethernet реализуется посредством 10G Base-X интерфейсов,
    для выхода в оптические сети служат интерфейсы GPON.

    Каждый интерфейс PON позволяет подключить до 128 абонентских оптических терминалов по одному волокну,
     динамическое распределение полосы DBA (dynamic bandwidth allocation).
    """

    # Регулярное выражение, соответствующее началу для ввода следующей команды.
    prompt = r"\S+#\s*$"
    # Строка, которая отображается, когда вывод команды слишком длинный и не помещается на экране.
    space_prompt = r"--More--\(\d+%\)"
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
        model="LTP-16N",
        snmp_community: str = "",
    ):
        super().__init__(session, ip, auth, model, snmp_community)
        version_output = self.send_command("show version")

        self.software_version: Version = Version("0.0.0")
        if match := re.search(r"software version (\S+) build", version_output):
            self.software_version = Version(match.group(1))

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
        """
        Интерфейсы на оборудовании

        :return: ```[ ('name', 'status', 'desc'), ... ]```
        """

        interfaces: list[tuple[str, str, str]] = []

        # Смотрим состояние front портов.
        # Front-port             Status                 Speed                  Media
        # --------------------   --------------------   --------------------   --------------------
        # 1                      up                     10G                    fiber
        # 2                      up                     10G                    copper
        interfaces_front_output = self.send_command("show interface front-port 1-8 state")

        # Далее смотрим текущую конфигурацию front портов, чтобы найти description.
        interfaces_running_config_output: str = self.send_command(
            "show running-config interface front-port 1-8", expect_command=False
        )

        # Преобразовываем данные конфигурации разбивая её на части по строчке `exit`.
        interfaces_running_config_list: list[str] = re.split("exit", interfaces_running_config_output)
        for line in re.findall(r"(\d)\s+(\S+)", interfaces_front_output):
            description = ""
            for config in interfaces_running_config_list:
                # Ищем блок конфигурации текущего порта и его описание.
                if match := re.search(rf'front-port {line[0]}.*description "(.*?)"', config, flags=re.DOTALL):
                    # Если имеется описание.
                    description = match.group(1)

            interfaces.append((f"front-port {line[0]}", line[1], description))

        # Смотрим состояние PON портов.
        interfaces_pon_output = self.send_command("show interface pon-port 1-16 state")
        interfaces += [
            (f"pon-port {line[0]}", line[1], "")
            for line in re.findall(r"(\d+)\s+(\S+).+[\r\n]", interfaces_pon_output)
        ]

        return reformat_ltp_interfaces_list(interfaces)

    @BaseDevice.lock_session
    def get_vlans(self) -> InterfaceVLANListType:
        result: InterfaceVLANListType = []

        self.lock = False
        interfaces = self.get_interfaces()
        self.lock = True

        # Далее смотрим текущую конфигурацию front портов, чтобы найти VLAN.
        interfaces_running_config_output: str = self.send_command(
            "show running-config interface front-port 1-8", expect_command=False
        )

        # Преобразовываем данные конфигурации разбивая её на части по строчке `exit`.
        interfaces_running_config_list: list[str] = re.split("exit", interfaces_running_config_output)
        for name, status, desc in interfaces:
            vlans: list[str] = []
            for config in interfaces_running_config_list:
                # Ищем блок конфигурации текущего порта и его VLAN.
                if match := re.search(rf"{name}.*vlan allow (\S+)", config, flags=re.DOTALL):
                    vlans = match.group(1).split(",")
            result.append((name, status, desc, vlans))

        return result

    @BaseDevice.lock_session
    def get_mac_table(self) -> MACTableType:
        """
        ## Возвращаем список из VLAN, MAC-адреса, MAC-type и порта для данного оборудования.

        Команда на оборудовании:

            # show mac verbose

        :return: ```[ ({int:vid}, '{mac}', 'dynamic', '{port}'), ... ]```
        """

        output = self.send_command("show mac verbose", expect_command=False)
        parsed = re.findall(
            rf"({self.mac_format})\s+(\S+\s\d+)\s+(\d+)\s+(\d*/?\d*)\s+(\d*)\s+(\S+).*\n",
            output,
        )

        def format_interface(port, indexes):
            if indexes:
                return f"{port}; ont {indexes}"
            return port

        return [
            (int(vid), mac, type_, format_interface(port, index))
            for mac, port, vid, index, _, type_ in parsed
        ]

    @BaseDevice.lock_session
    @_validate_port(if_invalid_return=[])
    def get_mac(self, port: str) -> MACListType:
        """
        Команда для version 1.8.0 и выше:

            # show mac interface {port_type} {port}

        Команда для старых версий:

            # show mac verbose include interface {port_type} {port}
        """
        port_type, port_number = port.split()

        if not port_number.isdigit():
            port_type = "ont"

        if self.software_version >= Version("1.8.0"):
            command = f"show mac interface {port_type} {port_number}"
        else:
            command = f"show mac verbose include interface {port_type} {port_number}"

        macs_output = self.send_command(command)

        macs = []
        for line in re.findall(rf"({self.mac_format})\s+\S+\s\d+\s+(\d+)", macs_output):
            macs.append((line[1], line[0]))

        return macs

    @BaseDevice.lock_session
    @_validate_port({"type": "error", "data": "Неверный порт"})
    def get_port_info(self, port: str):
        # Получаем тип порта и его номер
        port_type, port_number = port.split()

        if port_type == "front-port":
            info = self.send_command(f"show interface front-port {port_number} sfp")
            info += self.send_command(f"show interface front-port {port_number} state")
            info = info.strip()
            info = re.sub(r"\n", "<br>", info)
            info = re.sub(r"\s", "&nbsp;", info)
            return {
                "type": "html",
                "data": f'<div style="white-space: pre-wrap;font-family: monospace;font-size: 13px;">{info}</div>',
            }

        if port_type == "pon-port":
            # Данные для шаблона
            data: dict[str, int | list] = {}

            # Смотрим ONLINE ONT
            ont_online_info = self.send_command(f"show interface ont {port_number} online")
            # Парсим данные
            onts_lines = [
                # 0       1        2         3       4        5     6
                # ONT ID, Status,  Equip ID, RSSI,   Serial,  Desc, MacList
                [line[0], line[2], line[4], line[3], line[1], "", []]
                for line in re.findall(
                    r"\s+\d+\s+\d+\s+(\d+)\s+(\S+)\s+(\S+)\s+(-?\d+\.?\d*)\s+(\S+)",
                    ont_online_info,
                )
            ]

            data["online_count"] = len(onts_lines)

            # Смотрим OFFLINE ONT
            ont_offline_info = self.send_command(f"show interface ont {port_number} offline")
            # Парсим данные
            onts_lines += [
                # 0       1        2         3       4        5     6
                # ONT ID, Status,  Equip ID, RSSI,   Serial,  Desc, MacList
                [line[0], line[2], "", "", line[1], "", []]
                for line in re.findall(
                    r"\s+\d+\s+\d+\s+(\d+)\s+(\S+)\s+(\S+)",
                    ont_offline_info,
                )
            ]
            # Сортируем
            onts_lines = sorted(onts_lines, key=lambda x: int(x[0]))

            # Добавляем в итоговый словарь список из отсортированных по возрастанию ONT ID записей
            data["onts_lines"] = onts_lines
            # Общее кол-во сконфигурированных ONT на данном порту
            data["total_count"] = len(onts_lines)

            # В зависимости от версии прошивки будут разные команды.
            if self.software_version >= Version("1.8.0"):
                command = f"show mac interface pon-port {port_number}"
            else:
                command = f"show mac verbose include interface pon-port {port_number}"

            # Смотрим MAC на pon порту
            if port_number.isdigit():
                macs_list = re.findall(
                    rf"({self.mac_format})\s+\S+\s\d+\s+(\d+)\s+\d+/(\d+)", self.send_command(command)
                )
            else:
                macs_list = []

            # Перебираем список macs_list и назначаем каждому ONT ID свой VLAN/MAC
            for mac, vlan_id, ont_id in macs_list:
                # Выбираем запись ONT по индексу ONT ID - int(mac_line[0])
                for ont in onts_lines:
                    if ont[0] == ont_id:
                        # Затем обращаемся к 6 элементу, в котором находится список VLAN/MAC
                        # и добавляем VLAN, MAC и описание VLAN
                        ont[6].append([vlan_id, mac, ""])

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

        :param port:
        :param save_config:
        :return:
        """
        port_type, port_number = port.split()
        if port_type == "pon-port" and re.match(r"^\d+/\d+$", port_number):
            # Для порта ONT вида - `0/1`
            res = self.send_command(f"send omci reboot interface ont {port_number}")
            return res + "Without saving"

        return "Этот порт нельзя перезагружать"

    @BaseDevice.lock_session
    @_validate_port()
    def set_port(self, port: str, status: str, save_config=True) -> str:
        return ""

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
                "info": self.save_config(),
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

        if port_type == "front-port":
            return self.send_command(f"show running-config interface front-port {port_number}")

        return ""

    @_validate_port(if_invalid_return="?")
    def get_port_type(self, port: str) -> str:
        return "SFP"

    @_validate_port()
    def get_port_errors(self, port: str) -> str:
        return ""

    def get_device_info(self) -> dict:
        return {}

    @BaseDevice.lock_session
    def get_current_configuration(self) -> io.BytesIO:
        config = self.send_command("show running-config", expect_command=True)
        return io.BytesIO(config.encode())
