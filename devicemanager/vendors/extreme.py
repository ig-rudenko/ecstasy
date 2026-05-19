import io
import re
from collections.abc import Sequence
from time import sleep
from typing import Literal

from .. import DeviceException
from .base.device import AbstractConfigDevice, BaseDevice
from .base.factory import AbstractDeviceFactory
from .base.helpers import parse_by_template, range_to_numbers
from .base.types import (
    DeviceAuthDict,
    InterfaceListType,
    InterfaceType,
    InterfaceVLANListType,
    MACListType,
    MACTableType,
    MACType,
    PortInfoType,
)
from .base.validators import validate_and_format_port_only_digit


class Extreme(BaseDevice, AbstractConfigDevice):
    """
    # Для оборудования от производителя Extreme

    Проверено для:
     - X460
     - X670
    """

    prompt = r"\S+ ?#\s*$"
    space_prompt = "Press <SPACE> to continue or <Q> to quit:"
    mac_format = r"\S\S:" * 5 + r"\S\S"
    vendor = "Extreme"

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

            # show switch
            # show version

          - MAC
          - модель
          - Серийный номер

        :param session: Это объект сеанса pexpect c установленной сессией оборудования
        :param ip: IP-адрес устройства, к которому вы подключаетесь
        :param auth: словарь, содержащий имя пользователя и пароль для устройства
        :param model: Модель коммутатора
        """

        super().__init__(session, ip, auth, model, snmp_community)
        system = self.send_command("show switch")
        self.mac = self.find_or_empty(r"System MAC:\s+(\S+)", system)
        self.model = self.find_or_empty(r"System Type:\s+(\S+)", system)

    @BaseDevice.lock_session
    def save_config(self):
        """
        ## Сохраняем конфигурацию оборудования командой и подтверждаем:

            # save
            Y

        Ожидаем ответа от оборудования **successfully**,
        если нет, то ошибка сохранения
        """

        self.session.sendline("save")
        self.session.sendline("y")
        if self.session.expect([self.prompt, r"successfully"]):
            return self.SAVED_OK
        return self.SAVED_ERR

    @BaseDevice.lock_session
    def get_interfaces(self) -> InterfaceListType:
        """
        ## Возвращаем список всех интерфейсов на устройстве

        Команда на оборудовании:

            # show ports information

        :return: ```[ ('name', 'status', 'desc'), ... ]```
        """

        # Смотрим имена интерфейсов, статус порта и его состояние
        output_links = self.send_command("show ports information")

        result_port_state: list[list[str]] = parse_by_template(
            "interfaces/extreme_links.template", output_links
        )

        # Смотрим имена интерфейсов и описания
        output_des = self.send_command("show ports description")
        result_des: list[list[str]] = parse_by_template("interfaces/extreme_des.template", output_des)

        interfaces_lines = [result_port_state[n] + result_des[n] for n in range(len(result_port_state))]

        interfaces: list[tuple[str, InterfaceType, str]] = []
        for port_name, admin_status, link_status, desc in interfaces_lines:
            # Проверяем статус порта и меняем его на более понятный для пользователя
            status: InterfaceType = "up"
            if "notpresent" in link_status.lower():
                status = "notPresent"
            elif admin_status.startswith("D"):
                status = "admin down"
            elif link_status == "ready":
                status = "down"

            interfaces.append((port_name, status, desc))

        return interfaces

    @BaseDevice.lock_session
    def get_vlans(self) -> InterfaceVLANListType:
        r"""
        ## Возвращаем список всех интерфейсов и его VLAN на коммутаторе.

        Для начала получаем список всех интерфейсов через метод **get_interfaces()**

        Затем смотрим конфигурации вланов

            # show configuration "vlan"

        и выбираем строчки, в которых указаны вланы на портах с помощью регулярного выражения:

            .*v[lm]an v(\d+) add ports (.+) (tagged|untagged)

        :return: ```[ ('name', 'status', 'desc', ['{vid}', '{vid},{vid},...{vid}', ...] ), ... ]```
        """
        self.lock = False
        interfaces: InterfaceListType = self.get_interfaces()
        self.lock = True

        output_vlans = self.send_command(
            'show configuration "vlan"', before_catch=r"Module vlan configuration\."
        )
        result_vlans: list[tuple[str, str]] = parse_by_template(
            "vlans_templates/extreme.template", output_vlans
        )

        # Создаем словарь, где ключи это порты, а значениями будут вланы на них
        ports_vlan: dict[int, list[str]] = {num: [] for num in range(1, len(interfaces) + 1)}

        for vlan_id, ports in result_vlans:
            for port in range_to_numbers(ports):
                # Добавляем вланы на порты
                ports_vlan[port].append(vlan_id)

        interfaces_vlan: InterfaceVLANListType = []  # итоговый список (интерфейсы и вланы)
        for line in interfaces:
            interfaces_vlan.append((line[0], line[1], line[2], ports_vlan.get(int(line[0]), [])))  # noqa

        return interfaces_vlan

    @BaseDevice.lock_session
    def get_mac_table(self) -> MACTableType:
        """
        ## Возвращаем список из VLAN, MAC-адреса, dynamic и порта для данного оборудования.

        Команда на оборудовании:

            # show fdb

        :return: ```[ ({int:vid}, '{mac}', 'dynamic', '{port}'), ... ]```
        """
        mac_str = self.send_command("show fdb", expect_command=False)
        mac_table: list[tuple[str, str, str]] = re.findall(
            rf"({self.mac_format})\s+v\S+\((\d+)\)\s+\d+\s+d m\s+(\d+).*\n",
            mac_str,
            flags=re.IGNORECASE,
        )
        mac_type: MACType = "dynamic"
        return [(int(vid), mac, mac_type, port) for mac, vid, port in mac_table]

    @BaseDevice.lock_session
    @validate_and_format_port_only_digit(if_invalid_return=[])
    def get_mac(self, port: str) -> MACListType:
        """
        ## Возвращаем список из VLAN и MAC-адреса для данного порта.

        Команда на оборудовании:

            # show fdb ports {port}

        :param port: Номер порта коммутатора
        :return: ```[ ('vid', 'mac'), ... ]```
        """

        output = self.send_command(f"show fdb ports {port}", expect_command=False)
        macs: list[tuple[str, str]] = re.findall(rf"({self.mac_format})\s+v(\d+)", output)

        return [(int(vid), mac) for mac, vid in macs]

    @BaseDevice.lock_session
    @validate_and_format_port_only_digit()
    def get_port_errors(self, port: str):
        """
        ## Выводим ошибки на порту

        Используются команды

            show ports {port} rxerrors no-refresh
            show ports {port} txerrors no-refresh

        :param port: Порт для проверки на наличие ошибок
        """

        rx_errors = self.send_command(f"show ports {port} rxerrors no-refresh")
        tx_errors = self.send_command(f"show ports {port} txerrors no-refresh")

        return rx_errors + "\n" + tx_errors

    @BaseDevice.lock_session
    @validate_and_format_port_only_digit()
    def reload_port(self, port, save_config=True) -> str:
        """
        ## Перезагружает порт

            # disable ports {port}
            # enable ports {port}

        :param port: Порт для перезагрузки
        :param save_config: Если True, конфигурация будет сохранена на устройстве, defaults to True (optional)
        """

        self.session.sendline(f"disable ports {port}")
        self.session.expect(self.prompt)
        sleep(1)
        self.session.sendline(f"enable ports {port}")
        self.session.expect(self.prompt)
        r = (self.session.before or b"").decode(errors="ignore")
        self.lock = False
        s = self.save_config() if save_config else "Without saving"
        return r + s

    @BaseDevice.lock_session
    @validate_and_format_port_only_digit()
    def set_port(self, port: str, status: Literal["up", "down"], save_config=True) -> str:
        """
        ## Устанавливает статус порта на коммутаторе **up** или **down**

            # {disable|enable} ports {port}

        :param port: Порт
        :param status: "up" или "down"
        :param save_config: Если True, конфигурация будет сохранена на устройстве, defaults to True (optional)
        """

        if status == "up":
            cmd = "enable"
        elif status == "down":
            cmd = "disable"
        else:
            cmd = ""

        self.session.sendline(f"{cmd} ports {port}")
        self.session.expect(self.prompt)
        r = (self.session.before or b"").decode(errors="ignore")
        self.lock = False
        s = self.save_config() if save_config else "Without saving"
        return r + s

    @BaseDevice.lock_session
    @validate_and_format_port_only_digit()
    def get_port_type(self, port) -> str:
        """
        ## Возвращает тип порта

        Проверяем с помощью команды:

            debug hal show optic-info port {port}

        :param port: Порт для проверки
        :return: "SFP" или "COPPER"
        """
        debug_optical_info = self.send_command(f"debug hal show optic-info port {port}")
        wavelength = self.find_or_empty(debug_optical_info, r"Wavelength:\s+(\d+)")
        if wavelength == "0":
            return "COPPER"

        return "SFP"

    @BaseDevice.lock_session
    @validate_and_format_port_only_digit(if_invalid_return={"error": "Неверный порт", "status": "fail"})
    def set_description(self, port: str, desc: str) -> dict:
        """
        ## Устанавливаем описание для порта предварительно очистив его от лишних символов

        Если была передана пустая строка для описания, то очищаем с помощью команды:

            # unconfigure ports {port} description-string

        Если **desc** содержит описание, то используем команду для изменения:

            # configure ports {port} description-string {desc}

        :param port: Порт, для которого вы хотите установить описание
        :param desc: Описание, которое вы хотите установить для порта
        :return: Вывод команды смены описания
        """

        desc = self.clear_description(desc)  # Очищаем описание от лишних символов

        if desc == "":
            # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            self.send_command(f"unconfigure ports {port} description-string", expect_command=False)

        else:  # В другом случае, меняем описание на оборудовании
            self.send_command(
                f"configure ports {port} description-string {desc}",
                expect_command=False,
            )

        self.lock = False
        # Возвращаем результат работы и сохраняем конфигурацию
        return {
            "description": desc,
            "port": port,
            "status": "changed" if desc else "cleared",
            "saved": self.save_config(),
        }

    @BaseDevice.lock_session
    @validate_and_format_port_only_digit(if_invalid_return={"type": "text", "data": "Неверный порт"})
    def get_port_info(self, port: str) -> PortInfoType:
        debug_optical_info = self.send_command(f"debug hal show optic-info port {port}")
        information_detail = self.send_command(f"show port {port} information detail")
        return {"type": "text", "data": f"{debug_optical_info}\n\n{information_detail}"}

    def get_port_config(self, port: str) -> str:
        return ""

    def get_device_info(self) -> dict:
        return {}

    def get_current_configuration(self) -> io.BytesIO:
        config = self.send_command("show configuration")
        return io.BytesIO(config.strip().encode())

    @BaseDevice.lock_session
    @validate_and_format_port_only_digit()
    def vlans_on_port(
        self,
        port: str,
        operation: Literal["add", "delete"],
        vlans: Sequence[int],
        tagged: bool = True,
    ):
        """
        Эта функция добавляет или удаляет VLAN на указанном порту устройства и сохраняет конфигурацию.

        :param port: Параметр `port` представляет собой строку, представляющую имя или идентификатор порта,
         на котором будет выполняться операция VLAN
        :param operation: Параметр `operation` представляет собой строковый литерал, который указывает,
         следует ли добавлять или удалять VLAN на данном порту. Может иметь два возможных значения: «add» или «delete»
        :param vlans: Параметр `vlans` представляет собой последовательность целых чисел, представляющих идентификаторы
         VLAN, которые будут добавлены или удалены из указанного порта
        :param tagged: (optional) Параметр tagged представляет собой логический флаг, указывающий, следует ли добавлять
         или удалять VLAN как тегированные или нетегированные на указанном порту. Если `tagged` равно `True`,
         VLAN будут добавлены или удалены как тегированные на порту.
        """

        tagged_option = "tagged" if tagged else ""
        if operation not in {"add", "delete"}:
            raise DeviceException(
                f"Параметр `operation` должен принимать значения `add` или `delete`,"
                f" а было передано {operation}",
                ip=self.ip,
            )

        for vlan in vlans:
            self.send_command(f"configure vlan v{vlan} {operation} ports {port} {tagged_option}")

        self.lock = False
        self.save_config()


class ExtremeFactory(AbstractDeviceFactory):
    @staticmethod
    def support_devices() -> list[type[BaseDevice]]:
        return [Extreme]

    @staticmethod
    def is_can_use_this_factory(session=None, version_output=None) -> bool:
        return version_output and "ExtremeXOS" in str(version_output)

    @classmethod
    def get_device(
        cls,
        session,
        ip: str,
        snmp_community: str,
        auth: DeviceAuthDict,
        version_output: str = "",
    ) -> BaseDevice:
        device = Extreme(session, ip, auth, snmp_community=snmp_community)

        device.serialno = device.find_or_empty(r"Switch\s+: \S+ (\S+)", version_output)
        device.os_version = device.find_or_empty(r"Image\s+:\s+(.+)BootROM", version_output, flags=re.DOTALL)
        device.os_version = re.sub(r"\s+", " ", device.os_version)
        return device
