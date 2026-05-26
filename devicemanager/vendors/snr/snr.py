import io
import re
from time import sleep

from devicemanager.vendors.base.device import (
    AbstractCableTestDevice,
    AbstractConfigDevice,
    AbstractSearchDevice,
    BaseDevice,
)
from devicemanager.vendors.base.factory import AbstractDeviceFactory
from devicemanager.vendors.base.helpers import normalize_cable_diag_status
from devicemanager.vendors.base.types import (
    COOPER_TYPES,
    FIBER_TYPES,
    ArpInfoResult,
    CableDiagResult,
    DeviceAuthDict,
    InterfaceListType,
    InterfaceType,
    InterfaceVLANListType,
    MACListType,
    MACTableType,
    MACType,
    PortInfoType,
    VlanTableType,
)
from devicemanager.vendors.snr.vlan_parser import parse_vlan_output


class SNRDevice(BaseDevice, AbstractConfigDevice, AbstractSearchDevice, AbstractCableTestDevice):
    """
    # Для оборудования от производителя SNR
    """

    prompt = r"\S+#$"
    space_prompt = "--More--"
    mac_format = r"\S\S\S\S\.\S\S\S\S\.\S\S\S\S"
    vendor = "SNR"

    def __init__(
        self,
        session,
        ip: str,
        auth: DeviceAuthDict,
        model: str = "",
        snmp_community: str = "",
    ):
        """
        :param session: Это объект сеанса pexpect c установленной сессией оборудования
        :param ip: IP-адрес устройства, к которому вы подключаетесь
        :param auth: словарь, содержащий имя пользователя и пароль для устройства
        :param model: Модель коммутатора. Это используется для определения подсказки
        """
        super().__init__(session, ip, auth, model, snmp_community)
        self.send_command("terminal length 0", expect_command=False)

        terminal_width_output = self.send_command("terminal width ?", expect_command=False)
        max_terminal_width = self.find_or_empty(r"<\d+-(\d+)>", terminal_width_output)
        if max_terminal_width:
            self.send_command(f"terminal width {max_terminal_width}", expect_command=False)

        self.__cache_port_info: dict[str, str] = {}

    @staticmethod
    def normalize_interface_name(intf: str) -> str:
        return intf

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
            if self.session.expect([self.prompt, "Building configuration"]):
                self.session.expect(self.prompt)
                return self.SAVED_OK
        return self.SAVED_ERR

    @BaseDevice.lock_session
    def get_interfaces(self) -> InterfaceListType:
        """
        ## Возвращаем список всех интерфейсов на устройстве

        Команда на оборудовании:

            # show interface description

        :return: ```[ ('name', 'status', 'desc'), ... ]```
        """

        output = self.send_command("show interface description", expect_command=False)

        result: list[tuple[str, str, str, str]] = re.findall(
            r"^\s*(\S+)\s+(up|administratively down)\s+(up|down)\s*(\S*)\s*$", output, flags=re.MULTILINE
        )

        interfaces = []
        for port_name, admin_status, link_status, desc in result:
            status: InterfaceType = "up"
            if admin_status.lower() == "administratively down":
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

        interfaces_config: dict[str, str] = self._get_interfaces_config()

        for line in interfaces:
            # Отфильтровываем интерфейсы VLAN.
            intf_config = interfaces_config.get(self.normalize_interface_name(line[0]), "")
            vlans_group: list[str] = re.findall(
                r"(?<=access|llowed) vlan [ad\s]*(\S*\d)",
                intf_config,
            )
            result.append((line[0], line[1], line[2], vlans_group))  # noqa

        return result

    @BaseDevice.lock_session
    def get_vlan_table(self) -> VlanTableType:
        vlan_output = self.send_command("show vlan brief")
        parsed = parse_vlan_output(vlan_output)
        return [(line["vlan_id"], line["ports"], line["name"]) for line in parsed]

    def _get_interfaces_config(self) -> dict[str, str]:
        output = self.send_command("show running-config", expect_command=False)
        interfaces_config: dict[str, str] = {}
        for line in re.findall(r"interface\s+\S+\d.+?!", output, flags=re.DOTALL):
            if interface_name := re.match(r"^interface\s+(\S+)", line):
                interfaces_config[self.normalize_interface_name(interface_name.group(1))] = line
        return interfaces_config

    @BaseDevice.lock_session
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
            self.session.sendline("no shutdown\n")
            self.session.expect(self.prompt)
        elif status == "down":
            self.session.sendline("shutdown\n")
            self.session.expect(self.prompt)
        self.session.sendline("end\n")
        self.session.expect(self.prompt)

        r = (self.session.before or b"").decode(errors="ignore")
        self.lock = False
        s = self.save_config() if save_config else "Without saving"
        return r + s

    @BaseDevice.lock_session
    def get_port_info(self, port: str) -> PortInfoType:
        """
        ## Возвращаем информацию о порте.

        Через команду:

            # show interface {port}

        Выводим строчки в которых указано **media**

        Пример вывода:

        ```Full-duplex, 10Gb/s, link type is auto, media type is 10GBase-LR```

        :param port: Номер порта, для которого требуется получить информацию

        """

        port_info = self.send_command(f"show interface {port}", expect_command=False)

        # Сохраняем в кэш
        self.__cache_port_info[port] = port_info

        return {
            "type": "text",
            "data": "\n".join(port_info.splitlines()[1:]),
        }

    def get_port_type(self, port: str) -> str:
        """
        ## Возвращает тип порта
        :param port: Порт для проверки
        :return: "SFP", "COPPER", "COMBO-SFP", "COMBO-COPPER" или "?"
        """

        # Получаем информацию о порте.
        port_info = self.__cache_port_info.get(port) or self.get_port_info(port).get("data", "")
        # Ищем тип порта.
        port_type = self.find_or_empty(r"Hardware is (\S+)", port_info)

        if "Combo" in port_type:
            if "F" in port_type:
                return "COMBO-SFP"
            return "COMBO-COPPER"
        if "SFP" in port_info or port_type in FIBER_TYPES:
            return "SFP"
        if self.find_or_empty(r"G-(\S+)", port_type) in COOPER_TYPES:
            return "COPPER"

        return "?"

    def get_port_errors(self, port: str) -> str:
        """
        ## Выводим ошибки на порту

        :param port: Порт для проверки на наличие ошибок
        """

        # Получаем информацию о порте.
        port_info = self.get_port_info(port).get("data", "")

        media_type = [line.strip() for line in port_info.split("\n") if "error" in line]
        return "<p>" + "\n".join(media_type) + "</p>"

    @BaseDevice.lock_session
    def get_port_config(self, port: str) -> str:
        """
        ## Выводим конфигурацию порта

        Используем команду:

            # show running-config interface {port}
        """

        return self.send_command(f"show running-config interface {port}").strip()

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
        arp_output = self.send_command(f"show arp | include {address}", expect_command=False)
        parsed: list[tuple[str, str, str]] = re.findall(
            rf"(\d\S+\d)\s+({self.mac_format})\s+vlan(\d+)\s+\S+", arp_output
        )

        result = []
        for ip, mac, vlan in parsed:
            mac_output = self.send_command(f"show mac address-table address {mac}", expect_command=False)
            port = self.find_or_empty(rf"{vlan}\s+{self.mac_format}\s+\S+\s+(\S+)", mac_output)

            result.append(ArpInfoResult(ip=ip, mac=mac, vlan=vlan, port=port))

        return result

    @BaseDevice.lock_session
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

        self.send_command("end")  # Выходим из режима редактирования
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
        return {
            "cpu": {"util": self.get_cpu_utilization()},
            "ram": {},
            "flash": {"util": self.get_flash_utilization()},
            "temp": self.get_temp(),
        }

    def get_cpu_utilization(self) -> tuple:
        """
        ## Возвращает загрузку ЦП хоста
        """

        cpu_percent = re.findall(
            r"Last 1 minute CPU usage\s+:\s+(\d+)%",
            self.send_command("show system resources", expect_command=False),
            flags=re.IGNORECASE,
        )

        return tuple(map(int, cpu_percent))

    def get_flash_utilization(self) -> int:
        """
        ## Возвращает использование флэш-памяти устройства
        """

        flash = self.find_or_empty(
            r"Use:(\d+)%",
            self.send_command("show flash", expect_command=False),
            flags=re.IGNORECASE,
        )

        return int((int(flash[0]) - int(flash[1])) / int(flash[0]) * 100) if flash else -1

    def get_temp(self) -> dict:
        output = self.send_command("show temperature", expect_command=False)
        raw_value = self.find_or_empty(r"Temperature:\s+(\d+)\s+C", output)
        if not raw_value.isdigit():
            return {}

        current_temp = int(raw_value)
        high_temp = 60
        medium_temp = 50
        low_temp = 0

        if current_temp >= high_temp:
            status = "high"
        elif current_temp >= medium_temp:
            status = "medium"
        elif current_temp <= low_temp:
            status = "low"
        else:
            status = "normal"

        return {"value": current_temp, "status": status}

    def virtual_cable_test(self, port: str) -> CableDiagResult:
        result: CableDiagResult = {
            "len": "-",
            "status": "Skip",
        }
        output = self.send_command(f"show cable-test {port}", expect_command=False)
        if "not found" in output:
            result["status"] = normalize_cable_diag_status("Mismatch")
            return result

        if "not support cable" in output:
            result["status"] = normalize_cable_diag_status("Unsupported")

            # Пробуем SFP вариант.
            transceiver_info = self._get_transceiver_diag(port)
            if transceiver_info:
                result["status"] = "SFP"
                result["sfp"] = transceiver_info
                return result

        parsed = re.findall(r"\S+\s+Pair(\d+)\s+(?P<status>\S+)\s+(?P<length>\S+)", output)

        for pair_number, status, length in parsed:
            result[f"pair{int(pair_number) + 1}"] = {"status": status, "length": length}  # noqa

            if status.lower() != "skip":
                result["status"] = status
            if length != "-":
                result["len"] = length

        return result

    def _get_transceiver_diag(self, port: str):
        output = self.send_command(f"show transceiver interface {port} detail", expect_command=False)
        print(output)
        parsed = re.search(
            r"Temperature\S+\s+(?P<temp_value>\S+)\s+\S+\s+\S+\s+(?P<temp_high>\S+)\s+(?P<temp_low>\S+).+"
            r"Voltage\S+\s+(?P<volgate_value>\S+)\s+\S+\s+\S+\s+(?P<volgate_high>\S+)\s+(?P<volgate_low>\S+).+"
            r"Bias Current\S+\s+(?P<current_value>\S+)\s+\S+\s+\S+\s+(?P<current_high>\S+)\s+(?P<current_low>\S+).+"
            r"RX Power\S+\s+(?P<rx_value>\S+)\s+\S+\s+\S+\s+(?P<rx_high>\S+)\s+(?P<rx_low>\S+).+"
            r"TX Power\S+\s+(?P<tx_value>\S+)\s+\S+\s+\S+\s+(?P<tx_high>\S+)\s+(?P<tx_low>\S+)",
            output,
            flags=re.DOTALL,
        )
        if not parsed:
            return {}

        return {
            "Temperature": {
                "Current": parsed.group("temp_value"),
                "High Warning": parsed.group("temp_high"),
                "Low Warning": parsed.group("temp_low"),
            },
            "Voltage": {
                "Current": parsed.group("volgate_value"),
                "High Warning": parsed.group("volgate_high"),
                "Low Warning": parsed.group("volgate_low"),
            },
            "Current": {
                "Current": parsed.group("current_value"),
                "High Warning": parsed.group("current_high"),
                "Low Warning": parsed.group("current_low"),
            },
            "RxPower": {
                "Current": parsed.group("rx_value"),
                "High Warning": parsed.group("rx_high"),
                "Low Warning": parsed.group("rx_low"),
            },
            "TxPower": {
                "Current": parsed.group("tx_value"),
                "High Warning": parsed.group("tx_high"),
                "Low Warning": parsed.group("tx_low"),
            },
        }

    @BaseDevice.lock_session
    def get_current_configuration(self) -> io.BytesIO:
        data = self.send_command("show running-config")
        return io.BytesIO(data.encode())


class SNRFactory(AbstractDeviceFactory):
    @staticmethod
    def support_devices() -> list[type[BaseDevice]]:
        return [SNRDevice]

    @staticmethod
    def is_can_use_this_factory(session=None, version_output=None) -> bool:
        return version_output and "SNR" in version_output or "eNOS software" in version_output

    @classmethod
    def get_device(
        cls,
        session,
        ip: str,
        snmp_community: str,
        auth: DeviceAuthDict,
        version_output: str = "",
    ) -> BaseDevice:
        model = BaseDevice.find_or_empty(r"SNR-\S+", version_output)
        dev = SNRDevice(session, ip, auth, model=model, snmp_community=snmp_community)
        dev.serialno = dev.find_or_empty(r"Serial No.:\s+(\S+)", version_output)
        dev.mac = dev.find_or_empty(r"Vlan MAC (\S+)", version_output)
        return dev
