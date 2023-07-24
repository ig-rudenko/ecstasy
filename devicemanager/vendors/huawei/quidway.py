import io
import re
from time import sleep
from typing import Literal

import pexpect

from ..base.device import BaseDevice
from ..base.helpers import interface_normal_view, parse_by_template
from ..base.validators import validate_and_format_port_as_normal
from ..base.types import (
    COOPER_TYPES,
    FIBER_TYPES,
    T_InterfaceList,
    T_InterfaceVLANList,
    T_MACList,
    T_MACTable,
    MACType,
    InterfaceStatus,
)


class Huawei(BaseDevice):
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

    def __init__(self, session: pexpect, ip: str, auth: dict, model="", snmp_community: str = ""):
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
            match = self.session.expect(
                [self.prompt, r"successfully", r"[Ss]ystem is busy"], timeout=20
            )
            if match == 1:
                return self.SAVED_OK
            if match == 2:
                sleep(2)
                n += 1
                continue
            return self.SAVED_ERR

    @BaseDevice.lock_session
    def get_interfaces(self) -> T_InterfaceList:
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
            if port_name.startswith("NULL") or port_name.startswith("V"):
                continue

            if (
                "*" in link_status.lower()
                or "adm" in link_status.lower()
                or "admin" in link_status.lower()
            ):
                status = InterfaceStatus.admin_down.value
            elif "down" in link_status.lower():
                status = InterfaceStatus.down.value
            else:
                status = InterfaceStatus.up.value

            interfaces.append((port_name, status, desc))

        return interfaces

    @BaseDevice.lock_session
    def get_vlans(self) -> T_InterfaceVLANList:
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
        interfaces = self.get_interfaces()
        self.lock = True

        result = []
        for line in interfaces:
            if (
                not line[0].startswith("V")
                and not line[0].startswith("NU")
                and not line[0].startswith("A")
            ):
                output = self.send_command(
                    f"display current-configuration interface {interface_normal_view(line[0])}",
                    expect_command=False,
                )

                vlans_group = re.sub(
                    r"(?<=undo).+vlan (.+)", "", output
                )  # Убираем строчки, где есть "undo"
                vlans_group = list(
                    set(re.findall(r"vlan (.+)", vlans_group))
                )  # Ищем строчки вланов, без повторений

                result.append((line[0], line[1], line[2], vlans_group))

        return result

    @staticmethod
    def normalize_interface_name(intf: str) -> str:
        return interface_normal_view(intf)

    @BaseDevice.lock_session
    def get_mac_table(self) -> T_MACTable:
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
    def get_mac(self, port) -> T_MACList:
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
                mac_str1 = self.send_command(
                    f"display mac-address dynamic {port}", expect_command=False
                )
                mac_str2 = self.send_command(
                    f"display mac-address secure-dynamic {port}", expect_command=False
                )
                mac_str = mac_str1 + mac_str2

            for i in re.findall(r"(" + self.mac_format + r")\s+(\d+)", mac_str):
                mac_list.append(i[::-1])

        return mac_list

    @validate_and_format_port_as_normal()
    @BaseDevice.lock_session
    def __port_info(self, port):
        """
        ## Возвращаем полную информацию о порте.

        Через команду:

            > display interface {port}

        :param port: Номер порта, для которого требуется получить информацию
        """

        return self.send_command(f"display interface {port}")

    def get_port_type(self, port) -> str:
        """
        ## Возвращает тип порта

        :param port: Порт для проверки
        :return: "SFP", "COPPER", "COMBO-FIBER", "COMBO-COPPER" или "?"
        """

        res = self.__port_info(port)

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

        errors = self.__port_info(port).split("\n")
        return "\n".join(
            [line.strip() for line in errors if "error" in line.lower() or "CRC" in line]
        )

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
        r = self.session.before.decode(errors="ignore")

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
        r = self.session.before.decode(errors="ignore")

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
    @validate_and_format_port_as_normal()
    def set_description(self, port: str, desc: str) -> str:
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
            return "Max length:" + self.find_or_empty(r"no more than (\d+) characters", output)

        self.session.sendline("quit")
        self.session.expect(self.prompt)
        self.session.sendline("quit")
        self.session.expect(self.prompt)
        self.lock = False
        return f'Description has been {"changed" if desc else "cleared"}.' + self.save_config()

    def __parse_virtual_cable_test_data(self, data: str) -> dict:
        """
        ## Эта функция анализирует данные виртуального теста кабеля и возвращает словарь проанализированных данных.

        :param data: Данные для разбора
        """
        parse_data = {
            "len": "-",  # Length
            "status": "",  # Up, Down, Open, Short
            "pair1": {"status": "", "len": ""},  # Open, Short  # Length
            "pair2": {"status": "", "len": ""},
        }
        if "not support" in data:
            return {"status": "Don't support Cable Diagnostic"}

        if "2326" in self.model:
            # Для Huawei 2326
            parse_data["pair1"]["len"] = self.find_or_empty(r"Pair A length: (\d+)meter", data)
            parse_data["pair2"]["len"] = self.find_or_empty(r"Pair B length: (\d+)meter", data)
            parse_data["pair1"]["status"] = self.find_or_empty(r"Pair A state: (\S+)", data).lower()
            parse_data["pair2"]["status"] = self.find_or_empty(r"Pair B state: (\S+)", data).lower()

            if parse_data["pair1"]["status"] == parse_data["pair2"]["status"] == "ok":
                parse_data["status"] = "Up"
                # Вычисляем среднюю длину
                parse_data["len"] = (
                    int(parse_data["pair1"]["len"]) + int(parse_data["pair1"]["len"])
                ) / 2
                del parse_data["pair1"]
                del parse_data["pair2"]

            else:
                # Порт выключен
                parse_data["status"] = "Down"

        elif "2403" in self.model:
            # Для Huawei 2403
            parse_data["len"] = self.find_or_empty(r"(\d+) meter", data)

            status = self.find_or_empty(r"Cable status: (normal)", data) or self.find_or_empty(
                r"Cable status: abnormal\((\S+)\),", data
            )

            parse_data["status"] = "Up" if status == "normal" else status.capitalize()
            del parse_data["pair1"]
            del parse_data["pair2"]

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

        self.session.sendline("system-view")
        self.session.sendline(f"interface {port}")
        self.session.expect(self.prompt)
        self.session.sendline("virtual-cable-test")
        self.session.expect("virtual-cable-test")
        if self.session.expect([self.prompt, "continue"]):  # Требуется подтверждение?
            self.session.sendline("Y")
            self.session.expect(self.prompt)
        cable_test_data = self.session.before.decode("utf-8")

        self.session.sendline("quit")
        self.session.expect(self.prompt)
        self.session.sendline("quit")
        self.session.expect(self.prompt)
        return self.__parse_virtual_cable_test_data(cable_test_data)  # Парсим полученные данные

    def get_port_info(self, port: str) -> dict:
        return {"type": "text", "data": ""}

    @BaseDevice.lock_session
    def get_device_info(self) -> dict:
        return {}

    @BaseDevice.lock_session
    def get_current_configuration(self) -> io.BytesIO:
        config = self.send_command("display current-configuration", expect_command=True)
        config = re.sub(r"[ ]+\n[ ]+(?=\S)", "", config.strip())
        return io.BytesIO(config.encode())
