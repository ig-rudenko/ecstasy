import io
import re
from functools import partial
from time import sleep
from typing import Literal

from .base.device import AbstractCableTestDevice, AbstractConfigDevice, AbstractSearchDevice, BaseDevice
from .base.factory import AbstractDeviceFactory
from .base.helpers import create_mac_regexp, normalize_cable_diag_result, parse_by_template
from .base.types import (
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
from .base.validators import validate_and_format_port


def validate_port(port: str) -> str | None:
    """
    ## Проверка правильности порта Q-Tech.

    valid ports:
      - "Ethernet1/2/1"
      - "Ethernet 1/2/1"
      - "1/2/1"
      - "1/1/21"

    invalid ports:
      - "23"
      - "port12"
    """

    port = port.strip()
    if port_math := re.match(r"^(?:[Ee]thernet\s*)?(?P<indexes>\d+/\d+/\d+)$", port):
        return port_math.group("indexes")
    return None


# Создаем свой декоратор для проверки портов
qtech_validate_and_format_port = partial(validate_and_format_port, validator=validate_port)


class Qtech(BaseDevice, AbstractConfigDevice, AbstractSearchDevice, AbstractCableTestDevice):
    """
    # Для оборудования от производителя Q-Tech

    Проверено для:
     - QSW-8200
     - QSW-6500
    """

    prompt = r"\S+#$"
    space_prompt = r"\s*--More--\s*"
    mac_format = create_mac_regexp("00-11-22-33-44-55")
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
        self.send_command("terminal length 100")
        self.__cache_port_info: dict[str, str] = {}

    @staticmethod
    def normalize_interface_name(intf: str) -> str:
        intf = intf.strip()
        return validate_port(intf) or intf

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

        Затем для каждого интерфейса смотрим конфигурацию и выбираем строчки,
        в которых указаны VLAN:

         - ```access vlan {vid}```
         - ```allowed vlan {vid},{vid},...{vid}```
         - ```allowed vlan add {vid},{vid},...{vid}```

        :return: ```[ ('name', 'status', 'desc', ['{vid}', '{vid},{vid},...{vid}', ...] ), ... ]```
        """

        result: InterfaceVLANListType = []

        interfaces: InterfaceListType = self.get_interfaces()

        interfaces_config: dict[str, str] = self._get_interfaces_config()

        for line in interfaces:
            # Отфильтровываем интерфейсы VLAN.
            intf_config = interfaces_config.get(self.normalize_interface_name(line[0]), "")
            vlans_group: list[str] = re.findall(
                r"(?<=access|llowed) vlan [ad\s]*(\S*\d)",
                intf_config,
            )
            result.append(
                (line[0], line[1], line[2], [part.replace(";", ",") for part in vlans_group])  # noqa
            )

        return result

    def _get_interfaces_config(self) -> dict[str, str]:
        output = self.send_command("show running-config", expect_command=False)
        interfaces_config: dict[str, str] = {}
        for line in re.findall(r"interface\s+\S+\d.+?!(?=\r?\n)", output, flags=re.DOTALL | re.IGNORECASE):
            if interface_name := re.match(r"^interface\s+(\S+)", line, flags=re.IGNORECASE):
                interfaces_config[self.normalize_interface_name(interface_name.group(1))] = line
        return interfaces_config

    @BaseDevice.lock_session
    def get_vlan_table(self) -> VlanTableType:

        vlan_output = self.send_command("show vlan")

        def parse_ports(text: str) -> list[str]:
            return list(map(self.normalize_interface_name, re.findall(r"(\S+\d)", text)))

        vlans: list[dict] = []
        current_vlan: None | dict = None
        for line in vlan_output.splitlines():
            line_match = re.search(r"(?P<vid>\d+)\s+(?P<name>\S+)\s+\S+\s+\S+\s+(?P<ports>.+)", line)
            if not line_match and not current_vlan:
                continue

            if line_match:
                vlan = {
                    "vlan_id": int(line_match.group("vid")),
                    "name": line_match.group("name").strip(),
                    "ports": parse_ports(line_match.group("ports")),
                }
                current_vlan = vlan
                vlans.append(vlan)
                continue

            if current_vlan:
                current_vlan["ports"].extend(parse_ports(line))
                continue

        return [(line["vlan_id"], line["ports"], line["name"]) for line in vlans]

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
        parsed: list[tuple[str, str, str, str]] = re.findall(
            rf"(?P<vid>\d+)\s+({self.mac_format})\s+(?P<type>DYNAMIC|SECUR\S+|STATIC)\s+\S+\s+(?P<port>\S+).*\n",
            output,
        )

        result: MACTableType = []
        for vid, mac, type_, port in parsed:
            mac_type: MACType = "dynamic"
            if type_.startswith("SECUR"):
                mac_type = "security"
            elif type_ == "STATIC":
                mac_type = "static"

            result.append((int(vid), mac, mac_type, port))

        return result

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

        output = self.send_command(f"show mac-address-table interface ethernet {port}", expect_command=False)
        macs: list[tuple[str, str]] = re.findall(rf"(\d+)\s+({self.mac_format})", output)
        return [(int(vid), mac) for vid, mac in macs]

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

        formatted_mac = "{}{}-{}{}-{}{}-{}{}-{}{}-{}{}".format(*mac_address.lower())
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
        parsed: list[tuple[str, str, str, str]] = re.findall(
            rf"(?P<ip>\d\S+\d)\s+({self.mac_format})\s+vlan(?P<vid>\d+)\s+(?P<port>\S+)",
            arp_output,
            flags=re.IGNORECASE,
        )

        return [ArpInfoResult(ip=ip, mac=mac, vlan=vlan, port=port) for ip, mac, vlan, port in parsed]

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
        return self.save_config() if save_config else "Without saving"

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
    def _get_port_info(self, port: str) -> str:
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

        self.__cache_port_info[port] = self._get_port_info(port)

        return {
            "type": "html",
            "data": "<br>".join(self._get_port_info(port).split("\n")[:10]),
        }

    @qtech_validate_and_format_port(if_invalid_return="?")
    def get_port_type(self, port: str) -> str:
        """
        ## Возвращает тип порта

        :param port: Порт для проверки
        :return: "SFP", "COPPER" или "Неверный порт {port}"
        """
        port_info = self.__cache_port_info.get(port) or self._get_port_info(port)

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
        port_info = self.__cache_port_info.get(port) or self._get_port_info(port)

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

        # Возвращаем строку с результатом работы и сохраняем конфигурацию
        return {
            "description": desc,
            "port": port,
            "status": "changed" if desc else "cleared",
            "saved": self.save_config(),
        }

    @BaseDevice.lock_session
    def get_device_info(self) -> dict:
        return {
            "temp": self._get_temp(),
            "cpu": {
                "util": self._get_cpu_utilization(),
            },
            "flash": {
                "util": self._get_flash_utilization(),
            },
            "ram": {
                "util": self._get_ram_utilization(),
            },
        }

    def _get_flash_utilization(self):
        output = self.send_command("show flash | include %", expect_command=False)
        if value_match := re.search(r"(\d+)\s*%", output):
            return value_match.group(1)
        return -1

    def _get_ram_utilization(self):
        output = self.send_command("show memory usage", expect_command=False)
        if value_match := re.search(r"(\d+\.?\d*?)\s*%", output):
            return float(value_match.group(1))
        return -1

    def _get_cpu_utilization(self) -> tuple:
        """
        ## Возвращает загрузку ЦП хоста
        """

        cpu_percent = re.findall(
            r"(\d+)\s*%",
            self.send_command("show cpu utilization | include minute", expect_command=False),
            flags=re.IGNORECASE,
        )

        return tuple(map(int, cpu_percent))

    def _get_temp(self) -> dict:
        output = self.send_command("show temperature", expect_command=False)
        parsed = re.search(r"Temperature:\s+(?P<value>\d+)C", output)
        if not parsed:
            return {}

        current_temp = int(parsed.group("value"))
        high_temp = 80
        medium_temp = 60
        low_temp = 0

        status = "normal"
        if current_temp >= high_temp:
            status = "high"
        elif current_temp >= medium_temp:
            status = "medium"
        elif current_temp <= low_temp:
            status = "low"

        return {"value": current_temp, "status": status}

    @BaseDevice.lock_session
    @qtech_validate_and_format_port(if_invalid_return={"len": "-", "status": "Unknown"})
    def virtual_cable_test(self, port: str) -> CableDiagResult:
        return normalize_cable_diag_result(self._get_transceiver_diag(port))

    def _get_transceiver_diag(self, port: str) -> dict:
        output = self.send_command(f"show transceiver interface ethernet {port} detail", expect_command=False)
        parsed = re.search(
            r"Temperature\S+\s+(?P<temp_value>-?\d+\.?\d+)\S*\s+\S+\s+\S+\s+?(?P<temp_high>\S+)\s+(?P<temp_low>\S+).+?"
            r"Voltage\S+\s+(?P<volt_value>-?\d+\.?\d+)\S*\s+\S+\s+\S+\s+?(?P<volt_high>\S+)\s+(?P<volt_low>\S+).+?"
            r"Current\S+\s+(?P<cur_value>-?\d+\.?\d+)\S*\s+\S+\s+\S+\s+?(?P<cur_high>\S+)\s+(?P<cur_low>\S+).+?"
            r"RX Power\S+\s+(?P<rx_value>-?\d+\.?\d+)\S*\s+\S+\s+\S+\s+?(?P<rx_high>\S+)\s+(?P<rx_low>\S+).+?"
            r"TX Power\S+\s+(?P<tx_value>-?\d+\.?\d+)\S*\s+\S+\s+\S+\s+?(?P<tx_high>\S+)\s+(?P<tx_low>\S+).+?",
            output,
            flags=re.DOTALL,
        )
        if not parsed:
            return {"len": "-", "status": "not supported"}

        return {
            "sfp": {
                "Temperature": {
                    "Current": parsed.group("temp_value"),
                    "High Warning": parsed.group("temp_high"),
                    "Low Warning": parsed.group("temp_low"),
                },
                "Voltage": {
                    "Current": parsed.group("volt_value"),
                    "High Warning": parsed.group("volt_high"),
                    "Low Warning": parsed.group("volt_low"),
                },
                "Current": {
                    "Current": parsed.group("cur_value"),
                    "High Warning": parsed.group("cur_high"),
                    "Low Warning": parsed.group("cur_low"),
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
        }

    @BaseDevice.lock_session
    def get_current_configuration(self) -> io.BytesIO:
        data = self.send_command("show running-config", timeout=30)
        return io.BytesIO(data.encode("utf-8"))


class QtechFactory(AbstractDeviceFactory):
    @staticmethod
    def support_devices() -> list[type[BaseDevice]]:
        return [Qtech]

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
        device = Qtech(session, ip, auth, model=model, snmp_community=snmp_community)
        device.os_version = device.find_or_empty(
            r"SoftWare (?:Package )?(Version \S+)", version_output, flags=re.IGNORECASE
        )
        device.serialno = device.find_or_empty(r"Serial No\.:\s*(\S+)", version_output)
        device.mac = device.find_or_empty(r"(?i)VLAN\s+MAC\s+(\S+)", version_output)
        return device
