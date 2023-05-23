import re
from functools import wraps
from time import sleep
from typing import Literal, Sequence, Tuple, List, Any, Dict

import pexpect
import textfsm
from .base import (
    BaseDevice,
    TEMPLATE_FOLDER,
    range_to_numbers,
    T_InterfaceVLANList,
    T_InterfaceList,
    T_MACList,
    T_MACTable,
    MACType,
)


class Extreme(BaseDevice):
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

    def __init__(self, session: pexpect, ip: str, auth: dict, model=""):
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

        super().__init__(session, ip, auth, model)
        system = self.send_command("show switch")
        self.mac = self.find_or_empty(r"System MAC:\s+(\S+)", system)
        self.model = self.find_or_empty(r"System Type:\s+(\S+)", system)
        version = self.send_command("show version")
        self.serialno = self.find_or_empty(r"Switch\s+: \S+ (\S+)", version)

    @BaseDevice._lock
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

    @BaseDevice._lock
    def get_interfaces(self) -> T_InterfaceList:
        """
        ## Возвращаем список всех интерфейсов на устройстве

        Команда на оборудовании:

            # show ports information

        :return: ```[ ('name', 'status', 'desc'), ... ]```
        """

        # Смотрим имена интерфейсов, статус порта и его состояние
        output_links = self.send_command("show ports information")
        with open(
            f"{TEMPLATE_FOLDER}/interfaces/extreme_links.template",
            "r",
            encoding="utf-8",
        ) as template_file:
            # Создание объекта TextFSM из файла шаблона.
            int_des_ = textfsm.TextFSM(template_file)
            # Анализ вывода команды «show ports information» и возврат списка списков.
            result_port_state = int_des_.ParseText(output_links)

        for position, line in enumerate(result_port_state):
            # Проверяем статус порта и меняем его на более понятный для пользователя
            if result_port_state[position][1].startswith("D"):
                result_port_state[position][1] = "Disable"
            elif result_port_state[position][1].startswith("E"):
                result_port_state[position][1] = "Enable"
            else:
                result_port_state[position][1] = "None"

        # Смотрим имена интерфейсов и описания
        output_des = self.send_command("show ports description")

        with open(
            f"{TEMPLATE_FOLDER}/interfaces/extreme_des.template", "r", encoding="utf-8"
        ) as template_file:
            int_des_ = textfsm.TextFSM(template_file)
            result_des = int_des_.ParseText(output_des)  # Ищем desc

        result = [result_port_state[n] + result_des[n] for n in range(len(result_port_state))]
        return [
            (
                line[0],  # interface
                line[2].replace("ready", "down").replace("active", "up")
                if "Enable" in line[1]
                else "admin down",
                # status
                line[3],  # desc
            )
            for line in result
        ]

    @BaseDevice._lock
    def get_vlans(self) -> T_InterfaceVLANList:
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
        interfaces: T_InterfaceList = self.get_interfaces()
        self.lock = True

        output_vlans = self.send_command(
            'show configuration "vlan"', before_catch=r"Module vlan configuration\."
        )

        with open(
            f"{TEMPLATE_FOLDER}/vlans_templates/extreme.template", "r", encoding="utf-8"
        ) as template_file:
            vlan_templ = textfsm.TextFSM(template_file)
            result_vlans: List[str] = vlan_templ.ParseText(output_vlans)

        # Создаем словарь, где ключи это порты, а значениями будут вланы на них
        ports_vlan: Dict[int, List[str]] = {num: [] for num in range(1, len(interfaces) + 1)}

        for vlan in result_vlans:
            for port in range_to_numbers(vlan[1]):
                # Добавляем вланы на порты
                ports_vlan[port].append(vlan[0])

        interfaces_vlan: T_InterfaceVLANList = []  # итоговый список (интерфейсы и вланы)
        for line in interfaces:
            interfaces_vlan.append((line[0], line[1], line[2], ports_vlan.get(int(line[0]), [])))

        return interfaces_vlan

    def _validate_port(self: Any = None, if_invalid_return=None):
        """
        ## Декоратор для проверки правильности порта Extreme

        :param if_invalid_return: что нужно вернуть, если порт неверный
        """

        if if_invalid_return is None:
            if_invalid_return = "Неверный порт"

        def validate(func):
            @wraps(func)
            def wrapper(self, port: str, *args, **kwargs):
                port = port.strip()
                if not port.isdigit():
                    # Неверный порт
                    if isinstance(if_invalid_return, str):
                        return f"{if_invalid_return} {port}"

                    return if_invalid_return

                # Вызываем метод
                return func(self, port, *args, **kwargs)

            return wrapper

        return validate

    @BaseDevice._lock
    def get_mac_table(self) -> T_MACTable:
        """
        ## Возвращаем список из VLAN, MAC-адреса, dynamic и порта для данного оборудования.

        Команда на оборудовании:

            # show fdb

        :return: ```[ ({int:vid}, '{mac}', 'dynamic', '{port}'), ... ]```
        """
        mac_str = self.send_command("show fdb", expect_command=False)
        mac_table: List[Tuple[str, str, str]] = re.findall(
            rf"({self.mac_format})\s+v\S+\((\d+)\)\s+\d+\s+d m\s+(\d+).*\n",
            mac_str,
            flags=re.IGNORECASE,
        )
        mac_type: MACType = "dynamic"
        return [(int(vid), mac, mac_type, port) for mac, vid, port in mac_table]

    @BaseDevice._lock
    @_validate_port(if_invalid_return=[])
    def get_mac(self, port: str) -> T_MACList:
        """
        ## Возвращаем список из VLAN и MAC-адреса для данного порта.

        Команда на оборудовании:

            # show fdb ports {port}

        :param port: Номер порта коммутатора
        :return: ```[ ('vid', 'mac'), ... ]```
        """

        output = self.send_command(f"show fdb ports {port}", expect_command=False)
        macs: List[Tuple[str, str]] = re.findall(rf"({self.mac_format})\s+v(\d+)", output)

        return [(int(vid), mac) for mac, vid in macs]

    @BaseDevice._lock
    @_validate_port()
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

    @BaseDevice._lock
    @_validate_port()
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
        r = self.session.before.decode(errors="ignore")
        self.lock = False
        s = self.save_config() if save_config else "Without saving"
        return r + s

    @BaseDevice._lock
    @_validate_port()
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
        r = self.session.before.decode(errors="ignore")
        self.lock = False
        s = self.save_config() if save_config else "Without saving"
        return r + s

    @BaseDevice._lock
    @_validate_port()
    def get_port_type(self, port) -> str:
        """
        ## Возвращает тип порта

        Проверяем с помощью команды:

            show ports {port} transceiver information detail | include Media

        :param port: Порт для проверки
        :return: "SFP" или "COPPER"
        """

        if "Media Type" in self.send_command(
            f"show ports {port} transceiver information detail | include Media"
        ):
            return "SFP"

        return "COPPER"

    @BaseDevice._lock
    @_validate_port()
    def set_description(self, port: str, desc: str) -> str:
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
        # Возвращаем строку с результатом работы и сохраняем конфигурацию
        return f'Description has been {"changed" if desc else "cleared"}. {self.save_config()}'

    def get_port_info(self, port: str) -> dict:
        return {"type": "text", "data": ""}

    def get_port_config(self, port: str) -> str:
        return ""

    def get_device_info(self) -> dict:
        return {}

    def get_current_configuration(self, *args, **kwargs) -> str:
        config = self.send_command("show configuration")
        return config.strip()

    @BaseDevice._lock
    @_validate_port()
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
         VLAN будут добавлены или удалены как тегированные на порту
        """

        tagged_option = "tagged" if tagged else ""

        for vlan in vlans:
            self.send_command(f"configure vlan v{vlan} {operation} ports {port} {tagged_option}")

        self.lock = False
        self.save_config()
