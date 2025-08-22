import io
import re
from time import sleep

import textfsm

from .base.device import BaseDevice, AbstractConfigDevice, AbstractSearchDevice
from .base.factory import AbstractDeviceFactory
from .base.helpers import interface_normal_view, parse_by_template
from .base.types import (
    TEMPLATE_FOLDER,
    FIBER_TYPES,
    COOPER_TYPES,
    InterfaceType,
    InterfaceListType,
    InterfaceVLANListType,
    MACListType,
    MACTableType,
    MACType,
    DeviceAuthDict,
    ArpInfoResult,
    PortInfoType,
)
from .base.validators import validate_and_format_port_as_normal


class Cisco(BaseDevice, AbstractConfigDevice, AbstractSearchDevice):
    """
    # Для оборудования от производителя Cisco

    Проверено для:
     - WC-C3550
     - WC-C3560
     - WC-C3750G
     - WC-C4500X
     - ME-3400
     - ME-3600X
     - ME-3800X
     - ME-4924
    """

    prompt = r"\S+#$"
    space_prompt = r" --More-- "
    mac_format = r"\S\S\S\S\.\S\S\S\S\.\S\S\S\S"  # 0018.e7d3.1d43
    vendor = "Cisco"

    def __init__(
        self,
        session,
        ip: str,
        auth: DeviceAuthDict,
        model: str = "",
        snmp_community: str = "",
    ):
        """
        ## При инициализации смотрим характеристики устройства:

            # show version

          - MAC
          - серийный номер

        :param session: Это объект сеанса pexpect c установленной сессией оборудования
        :param ip: IP-адрес устройства, к которому вы подключаетесь
        :param auth: словарь, содержащий имя пользователя и пароль для устройства
        :param model: Модель коммутатора. Это используется для определения подсказки
        """
        super().__init__(session, ip, auth, model, snmp_community)
        version = self.send_command("show version")
        self.serialno = self.find_or_empty(r"System serial number\s+: (\S+)", version)
        self.mac = self.find_or_empty(r"[MACmac] [Aa]ddress\s+: (\S+)", version)
        self.os_version = self.find_or_empty(r"(Version \S+),.+Copyright", version, flags=re.DOTALL)
        self.__cache_port_info: dict[str, str] = {}

    @staticmethod
    def normalize_interface_name(intf: str) -> str:
        return interface_normal_view(intf)

    @BaseDevice.lock_session
    def save_config(self):
        """
        ## Сохраняем конфигурацию оборудования командой:

            # write

        Ожидаем ответа от оборудования **[OK]**,
        если нет, то пробуем еще 2 раза, в противном случае ошибка сохранения
        """

        for _ in range(3):  # Пробуем 3 раза, если ошибка
            self.session.sendline("write")
            # self.session.expect(r'Building configuration')
            if self.session.expect([self.prompt, r"\[OK\]"]):
                self.session.expect(self.prompt)
                return self.SAVED_OK
        return self.SAVED_ERR

    @BaseDevice.lock_session
    def get_interfaces(self) -> InterfaceListType:
        """
        ## Возвращаем список всех интерфейсов на устройстве

        Команда на оборудовании:

            # show interfaces description

        :return: ```[ ('name', 'status', 'desc'), ... ]```
        """

        output = self.send_command("show interfaces description", expect_command=False)
        output = re.sub(".+\nInterface", "Interface", output)

        result: list[list[str]] = parse_by_template("interfaces/cisco.template", output)

        interfaces = []
        for port_name, admin_status, link_status, desc in result:
            status: InterfaceType = "up"
            if admin_status.lower() == "admin down":
                status = "admin down"
            elif "down" in link_status.lower():
                status = "down"

            interfaces.append((port_name, status, desc))

        return interfaces

    @BaseDevice.lock_session
    def get_vlans(self) -> InterfaceVLANListType:
        """
        ## Возвращаем список всех интерфейсов и его VLAN на коммутаторе.

        Для начала получаем список всех интерфейсов через метод **get_interfaces()**

        Затем для каждого интерфейса смотрим конфигурацию и выбираем строчки,
        в которых указаны VLAN:

         - ```access vlan {vid}```
         - ```allowed vlan {vid},{vid},...{vid}```
         - ```allowed vlan add {vid},{vid},...{vid}```

        :return: ```[ ('name', 'status', 'desc', ['{vid}', '{vid},{vid},...{vid}', ...] ), ... ]```
        """

        result: InterfaceVLANListType = []

        self.lock = False
        interfaces: InterfaceListType = self.get_interfaces()
        self.lock = True

        for line in interfaces:
            # Отфильтровываем интерфейсы VLAN.
            if not line[0].startswith("V"):
                output = self.send_command(
                    command=f"show running-config interface {interface_normal_view(line[0])}",
                    before_catch="Building configuration",
                    expect_command=False,
                )
                vlans_group: list[str] = re.findall(r"(?<=access|llowed) vlan [ad\s]*(\S*\d)", output)
                result.append((line[0], line[1], line[2], vlans_group))

        return result

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal(if_invalid_return=[])
    def get_mac(self, port) -> MACListType:
        """
        ## Возвращаем список из VLAN и MAC-адреса для данного порта.

        Команда на оборудовании:

            # show mac address-table interface {port}

        :param port: Номер порта коммутатора
        :return: ```[ ('vid', 'mac'), ... ]```
        """

        mac_str = self.send_command(
            f"show mac address-table interface {port}",
            expect_command=False,
        )
        macs_list: list[tuple[str, str]] = re.findall(rf"(\d+)\s+({self.mac_format})\s+\S+\s+\S+", mac_str)
        return [(int(vid), mac) for vid, mac in macs_list]

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
            rf"(\d+)\s+({self.mac_format})\s+(dynamic|static)\s+.*?(\S+)\s*\n",
            mac_str,
            flags=re.IGNORECASE,
        )
        return [(int(vid), mac, mac_type(type_), port) for vid, mac, type_, port in mac_table]

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal()
    def reload_port(self, port, save_config=True) -> str:
        """
        ## Перезагружает порт

        Переходим в режим конфигурирования:

            # configure terminal

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

        self.session.sendline("configure terminal")
        self.session.expect(self.prompt)
        self.session.sendline(f"interface {port}")
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
    @validate_and_format_port_as_normal()
    def set_port(self, port, status, save_config=True) -> str:
        """
        ## Устанавливает статус порта на коммутаторе **up** или **down**

        Переходим в режим конфигурирования:
            # configure terminal

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

        self.session.sendline("configure terminal")
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

    @validate_and_format_port_as_normal({"type": "error", "data": "Неверный порт"})
    @BaseDevice.lock_session
    def get_port_info(self, port: str) -> PortInfoType:
        """
        ## Возвращаем информацию о порте.

        Через команду:

            # show interfaces {port}

        Выводим строчки в которых указано **media**

        Пример вывода:

        ```Full-duplex, 10Gb/s, link type is auto, media type is 10GBase-LR```

        :param port: Номер порта, для которого требуется получить информацию

        """

        port_info = self.send_command(f"show interfaces {port}", expect_command=False)

        # Сохраняем в кэш
        self.__cache_port_info[port] = port_info

        return {
            "type": "text",
            "data": "\n".join(port_info.splitlines()[1:]),
        }

    @validate_and_format_port_as_normal()
    def get_port_type(self, port: str) -> str:
        """
        ## Возвращает тип порта

        Тип порта определяется по стандарту IEE 802.3

        ### Обозначения медных типов
            T, TX, VG, CX, CR
        ### Обозначения оптоволоконных типов:
            FOIRL, F, FX, SX, LX, BX, EX, ZX, SR, ER, SW, LW, EW, LRM, PR, LR, ER, FR, LH

        Оптоволокно:

            media type is LX
            media type is SFP-LR
            media type is No XCVR
            media type is 10GBase-LR
            media type is 1000BaseBX10-U SFP

        Медь:

            media type is RJ45
            media type is 10/100/1000BaseTX

        Не определено:

            media type is unsupported
            media type is Not Present
            media type is unknown media type

        :param port: Порт для проверки
        :return: "SFP", "COPPER" или "?"
        """

        # Получаем информацию о порте.
        port_info = self.__cache_port_info.get(port) or self.get_port_info(port).get("data", "")
        # Ищем тип порта.
        port_type = "".join(
            self.find_or_empty(r"media type is .+[Bb]ase[-]?(\S{1,2})|media type is (.+)", port_info)
        )
        # Проверка, является ли порт оптоволоконным.
        if "No XCVR" in port_type or "SFP" in port_info or port_type in FIBER_TYPES:
            return "SFP"
        if "RJ45" in port_type or port_type in COOPER_TYPES:
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

        config = self.send_command(
            f"show running-config interface {port}",
            before_catch=r"Current configuration.+?\!",
            expect_command=False,
        ).strip()
        return config

    @BaseDevice.lock_session
    def search_mac(self, mac_address: str) -> list[ArpInfoResult]:
        """
        ## Ищем MAC адрес в таблице ARP оборудования

        **MAC необходимо передавать без разделительных символов**
        он сам преобразуется к виду, требуемому для Cisco

        Отправляем на оборудование команду:

            # show arp | include {mac_address}

        Возвращаем список всех IP-адресов, VLAN, связанных с этим MAC-адресом.

        :param mac_address: MAC-адрес, который вы хотите найти
        :return: ```[['IP', 'MAC', 'VLAN'], ...]```
        """
        if len(mac_address) < 12:
            return []

        formatted_mac = "{}{}{}{}.{}{}{}{}.{}{}{}{}".format(*mac_address.lower())
        return self._search_in_arp(address=formatted_mac)

    @BaseDevice.lock_session
    def search_ip(self, ip_address: str) -> list[ArpInfoResult]:
        """
        ## Ищем IP адрес в таблице ARP оборудования

        Отправляем на оборудование команду:

            # show arp | include {ip_address}

        Возвращаем список всех MAC-адресов, VLAN, связанных с этим IP-адресом.

        :param ip_address: IP-адрес, который вы хотите найти
        :return: ```['IP', 'MAC', 'VLAN']```
        """
        return self._search_in_arp(address=ip_address)

    def _search_in_arp(self, address: str) -> list[ArpInfoResult]:
        match = self.send_command(f"show arp | include {address}", expect_command=False)
        # Форматируем вывод
        with open(
            f"{TEMPLATE_FOLDER}/arp_format/{self.vendor.lower()}.template",
            encoding="utf-8",
        ) as template_file:
            template = textfsm.TextFSM(template_file)
        result = template.ParseText(match)
        return list(map(lambda r: ArpInfoResult(*r), result))

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal(if_invalid_return={"error": "Неверный порт", "status": "fail"})
    def set_description(self, port: str, desc: str) -> dict:
        """
        ## Устанавливаем описание для порта предварительно очистив его от лишних символов

        Переходим в режим конфигурирования:

            # configure terminal

        Переходим к интерфейсу:

            (config)# interface {port}

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
        self.session.sendline("configure terminal")
        self.session.expect(self.prompt)
        self.session.sendline(f"interface {port}")
        self.session.expect(self.prompt)

        if desc == "":  # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            res = self.send_command("no description", expect_command=False)

        else:  # В другом случае, меняем описание на оборудовании
            res = self.send_command(f"description {desc}", expect_command=False)

        self.session.sendline("end")  # Выходим из режима редактирования

        self.lock = False

        if "Invalid input detected" in res:
            return {
                "status": "fail",
                "port": port,
                "error": "Invalid input detected",
            }

        return {
            "description": desc,
            "port": port,
            "status": "changed" if desc else "cleared",
            "saved": self.save_config(),
        }

    @BaseDevice.lock_session
    def get_device_info(self) -> dict:
        data: dict[str, dict] = {"cpu": {}, "ram": {}, "flash": {}}
        for key in data:
            data[key]["util"] = getattr(self, f"get_{key}_utilization")()
        data["temp"] = self.get_temp()
        return data

    def get_cpu_utilization(self) -> tuple:
        """
        ## Возвращает загрузку ЦП хоста
        """

        cpu_percent = re.findall(
            r"one minute: (\d+)%",
            self.send_command("show processes cpu | include minute", expect_command=False),
            flags=re.IGNORECASE,
        )

        return tuple(map(int, cpu_percent))

    def get_flash_utilization(self) -> int:
        """
        ## Возвращает использование флэш-памяти устройства
        """

        flash = self.find_or_empty(
            r"(\d+)\s+(\d+)\s+\S+\s+\S+\s+[boot]*flash",
            self.send_command("show file systems", expect_command=False),
            flags=re.IGNORECASE,
        )

        flash_percent = int((int(flash[0]) - int(flash[1])) / int(flash[0]) * 100) if flash else -1
        return flash_percent

    def get_ram_utilization(self) -> int:
        """
        ## Возвращает использование DRAM в процентах
        """

        output = self.send_command("show memory statistics", expect_command=False)
        pattern = r"Processor\s+\S+\s+(\d+)\s+(\d+)"

        if "Invalid input" in output:
            output = self.send_command("show memory", expect_command=False)
            pattern = r"Process\s+(\d+)\s+(\d+)"

        ram = self.find_or_empty(pattern, output, flags=re.IGNORECASE)
        dram_percent = int(int(ram[1]) / int(ram[0]) * 100) if ram else -1

        return dram_percent

    def get_temp(self) -> dict:
        output = self.send_command("show env temp status", expect_command=False)

        if "Invalid input" in output:
            output = self.send_command("show env temp", expect_command=False)
            pattern = r"CPU\s+([-]?\d+)C"
        else:
            pattern = r"Temperature Value: ([-]?\d+[.]?\d?) Degree Celsius"

        temp = self.find_or_empty(pattern, output)

        if not temp:
            return {}

        current_temp = float(temp)

        high_temp_limit: list[tuple[str, str]] = re.findall(
            r"SYSTEM High Temperature Shutdown Threshold: (\d+[.]?\d?) Degree Celsius|"
            r"Red Threshold {4}: (\d+) Degree Celsius",
            output,
        )
        if high_temp_limit:
            high_temp = float("".join(high_temp_limit[0]))
        else:
            high_temp = 60.0

        medium_temp_limit: list[tuple[str, str]] = re.findall(
            r"SYSTEM High Temperature Alert Threshold: (\d+[.]?\d?) Degree Celsius|"
            r"Yellow Threshold : (\d+) Degree Celsius",
            output,
        )
        if medium_temp_limit:
            medium_temp = float("".join(medium_temp_limit[0]))
        else:
            medium_temp = 60.0

        low_temp = float(
            self.find_or_empty(
                r"SYSTEM Low Temperature Alert Threshold: (\d+[.]?\d?) Degree Celsius",
                output,
            )
            or 0
        )

        status = "normal"
        if current_temp >= medium_temp:
            status = "medium"
        elif current_temp >= high_temp - 6:
            status = "high"
        elif current_temp <= low_temp:
            status = "low"

        return {"value": current_temp, "status": status}

    @BaseDevice.lock_session
    def get_current_configuration(self) -> io.BytesIO:
        data = self.send_command(
            "show running-config",
            expect_command=False,
            before_catch=r"Building configuration\.\.\.",
        )
        return io.BytesIO(data.encode())


class CiscoFactory(AbstractDeviceFactory):
    @staticmethod
    def is_can_use_this_factory(session=None, version_output=None) -> bool:
        return version_output and "cisco" in str(version_output).lower()

    @classmethod
    def get_device(
        cls,
        session,
        ip: str,
        snmp_community: str,
        auth: DeviceAuthDict,
        version_output: str = "",
    ) -> BaseDevice:
        model = BaseDevice.find_or_empty(r"Model number\s*:\s*(\S+)", version_output)
        return Cisco(session, ip, auth, model=model, snmp_community=snmp_community)
