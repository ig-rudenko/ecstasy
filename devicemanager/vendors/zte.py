import re
from functools import wraps
from time import sleep
from typing import List, Tuple, Literal

import pexpect
import textfsm
from .base import (
    BaseDevice,
    TEMPLATE_FOLDER,
    COOPER_TYPES,
    FIBER_TYPES,
    range_to_numbers,
    T_InterfaceList,
    T_InterfaceVLANList,
    T_MACList, T_MACTable,
)


class ZTE(BaseDevice):
    """
    # Для оборудования от производителя ZTE

    Проверено для:
     - ZXR10 2928E
     - ZXR10 2936-FI
     - ZXR10 2952E

    """

    prompt = r"\S+\(cfg\)#|\S+>"
    space_prompt = "----- more -----"
    # Два формата для МАС "e1.3f.45.d6.23.53" и "e13f.45d6.2353"
    mac_format = (
        r"\S\S\.\S\S\.\S\S\.\S\S\.\S\S\.\S\S"
        + "|"
        + r"[a-f0-9]{4}\.[a-f0-9]{4}\.[a-f0-9]{4}"
    )
    vendor = "ZTE"

    def __init__(self, session: pexpect, ip: str, auth: dict, model=""):
        """
        ## При инициализации повышаем уровень привилегий:

            > enable

          - MAC
          - серийный номер

        :param session: Это объект сеанса pexpect c установленной сессией оборудования
        :param ip: IP-адрес устройства, к которому вы подключаетесь
        :param auth: словарь, содержащий имя пользователя и пароль для устройства
        :param model: Модель коммутатора. Это используется для определения подсказки
        """

        super().__init__(session, ip, auth, model)
        version = self.send_command("show version")
        self.mac = self.find_or_empty(r"Mac Address: (\S+)", version)

        # Turning on privileged mode
        self.session.sendline("enable")

        # Если ещё не привилегированный
        match_ = self.session.expect([self.prompt, r"password", r"[Ss]imultaneous"])

        if match_ == 1:
            # send secret
            self.session.sendline(self.auth.get("privilege_mode_password"))
            if self.session.expect([r"refused", r"\(cfg\)#"]):
                self.__privileged = True
            else:
                self.__privileged = False

        elif match_ == 2:
            self.__privileged = False

        else:
            self.__privileged = True

    @BaseDevice._lock
    def get_interfaces(self) -> T_InterfaceList:
        """
        ## Возвращаем список всех интерфейсов на устройстве

        Команда на оборудовании:

            (cfg)# show port

        :return: ```[ ('name', 'status', 'desc'), ... ]```
        """

        output = self.send_command("show port")

        with open(
            f"{TEMPLATE_FOLDER}/interfaces/zte.template", encoding="utf-8"
        ) as template_file:
            int_des_ = textfsm.TextFSM(template_file)
            result = int_des_.ParseText(output)  # Ищем интерфейсы
        return [
            (
                line[0],  # interface
                line[2] if "enabled" in line[1] else "admin down",  # status
                line[3],  # desc
            )
            for line in result
        ]

    @BaseDevice._lock
    def get_vlans(self) -> T_InterfaceVLANList:
        """
        ## Возвращаем список всех интерфейсов и его VLAN на коммутаторе.

        Для начала получаем список всех интерфейсов через метод **get_interfaces()**

        Затем для смотрим вланы командой:

            (cfg)# show vlan

        И сопоставляем их с интерфейсами

        :return: ```[ ('name', 'status', 'desc', [vid:int, vid:int, ...] ), ... ]```
        """

        self.lock = False
        interfaces = self.get_interfaces()
        self.lock = True
        output = self.send_command("show vlan")

        with open(
            f"{TEMPLATE_FOLDER}/vlans_templates/zte_vlan.template",
            encoding="utf-8",
        ) as template_file:
            vlan_templ = textfsm.TextFSM(template_file)
            result_vlan = vlan_templ.ParseText(output)

        vlan_port = {}
        for vlan in result_vlan:
            # Если не нашли влан, или он деактивирован, то пропускаем
            if not vlan[0] or vlan[4] == "disabled":
                continue
            # Объединяем тегированные вланы и нетегированные в один список
            vlan_port[int(vlan[0])] = range_to_numbers(",".join([vlan[2], vlan[3]]))

        interfaces_vlan = []  # итоговый список (интерфейсы и вланы)

        for line in interfaces:
            vlans = []  # Строка со списком VLANов с переносами
            for vlan_id in vlan_port:
                if int(line[0]) in vlan_port[vlan_id]:
                    vlans.append(vlan_id)
            interfaces_vlan.append((line[0], line[1], line[2], vlans))
        return interfaces_vlan

    def _validate_port(self=None, if_invalid_return=None):
        """
        ## Декоратор для проверки правильности порта ZTE

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
        ## Возвращаем список из VLAN, MAC-адреса, MAC-type и порта для данного оборудования.

        Команда на оборудовании:

            > show fdb detail

            MacAddress        Vlan  PortId   Type
            ----------------- ----- -------- --------
            3c.ef.8c.d5.83.11 1945  36       dynamic
            40.d8.55.1d.37.2a 3779  36       dynamic
            ...

        :return: ```[ ({int:vid}, '{mac}', 'dynamic', '{port}'), ... ]```
        """

        output = self.send_command("show fdb detail", expect_command=False)
        parsed = re.findall(rf"({self.mac_format})\s+(\d+)\s+(\d+)\s+(\S+).*\n", output)
        return [
            (int(vid), mac, type_, port)
            for mac, vid, port, type_ in parsed
        ]

    @BaseDevice._lock
    @_validate_port(if_invalid_return=[])
    def get_mac(self, port: str) -> T_MACList:
        """
        ## Возвращаем список из VLAN и MAC-адреса для данного порта.

        Используем команды:

            (cfg)# show fdb port {port} detail
            (cfg)# show mac dynamic port {port}

        :param port: Номер порта коммутатора
        :return: ```[ (vid, 'mac'), ... ]```
        """

        output_macs = self.send_command(
            f"show fdb port {port} detail", expect_command=False
        )
        if "not found" in output_macs:
            output_macs = self.send_command(
                f"show mac dynamic port {port}", expect_command=False
            )

        mac_lines: List[Tuple[str, str]] = re.findall(rf"({self.mac_format})\s+(\d+)", output_macs)
        return [(int(vid), mac) for vid, mac in mac_lines]

    @BaseDevice._lock
    def save_config(self) -> str:
        """
        ## Сохраняем конфигурацию оборудования

        Используется одна из команд:

            (cfg)# saveconfig
            (cfg)# write

        Ожидаем ответа от оборудования **Done**,
        если нет, то ошибка сохранения
        """

        self.session.sendline("saveconfig")
        if self.session.expect([r"please wait a minute", "Command not found"]):
            self.session.sendline("write")
            self.session.expect(r"please wait a minute")

        if self.session.expect([self.prompt, r"[Dd]one"]):
            return self.SAVED_OK
        return self.SAVED_ERR

    @BaseDevice._lock
    @_validate_port()
    def reload_port(self, port: str, save_config=True) -> str:
        """
        ## Перезагружает порт

            (cfg)# set port {port} disable
            (cfg)# set port {port} disable

        :param port: Порт для перезагрузки
        :param save_config: Если True, конфигурация будет сохранена на устройстве, defaults to True (optional)
        """

        if not self.__privileged:
            return "Не привилегированный. Операция отклонена!"

        self.session.sendline(f"set port {port} disable")
        sleep(1)
        self.session.sendline(f"set port {port} enable")

        self.lock = False
        s = self.save_config() if save_config else "Without saving"
        return f"reset port {port} " + s

    @BaseDevice._lock
    @_validate_port()
    def set_port(self, port: str, status: Literal["up", "down"], save_config=True) -> str:
        """
        ## Устанавливает статус порта на коммутаторе **up** или **down**

        Меняем состояние порта:

            (cfg)# set port {port} {disable|enable}

        :param port: Порт
        :param status: "up" или "down"
        :param save_config: Если True, конфигурация будет сохранена на устройстве, defaults to True (optional)
        """

        if not self.__privileged:
            return "Не привилегированный. Операция отклонена!"

        if status == "down":
            self.session.sendline(f"set port {port} disable")
        elif status == "up":
            self.session.sendline(f"set port {port} enable")
        else:
            return f"Неверный статус {status}"

        self.lock = False
        s = self.save_config() if save_config else "Without saving"
        return f"{status} port {port} " + s

    @BaseDevice._lock
    @_validate_port()
    def get_port_config(self, port: str) -> str:
        """
        ## Выводим конфигурацию порта

        Используем команду:

            # show running-config

        Затем выбираем конфигурацию нужного порта
        """

        running_config = self.send_command("show running-config").split("\n")
        port_config = ""
        for line in running_config:
            s = self.find_or_empty(rf".+port {port} .*", line)
            if s:
                port_config += s + "\n"

        return port_config

    @BaseDevice._lock
    @_validate_port(if_invalid_return="?")
    def get_port_type(self, port: str) -> str:
        """
        ## Возвращает тип порта

        Тип порта определяется по стандарту IEE 802.3

        ### Обозначения медных типов
            T, TX, VG, CX, CR
        ### Обозначения оптоволоконных типов:
            FOIRL, F, FX, SX, LX, BX, EX, ZX, SR, ER, SW, LW, EW, LRM, PR, LR, ER, FR

        Оптоволокно:

            BaseX
            BaseLR
            BaseFX

        Медь:

            BaseT
            BaseTX

        :param port: Порт для проверки
        :return: "SFP", "COPPER", "Неверный порт!" или "?"
        """

        output = self.send_command(f"show port {port} brief")
        type_ = self.find_or_empty(r"\d+\s+\d+Base(\S+)\s+", output)

        if type_ in COOPER_TYPES:
            return "COPPER"
        if type_ in FIBER_TYPES or type_ == "X":
            return "SFP"

        return "?"

    @BaseDevice._lock
    @_validate_port()
    def get_port_errors(self, port: str) -> str:
        """
        ## Выводим ошибки на порту

        Используем команду:

            (cfg)# show port {port} statistics

        :param port: Порт для проверки на наличие ошибок
        """

        return self.send_command(f"show port {port} statistics")

    @BaseDevice._lock
    @_validate_port()
    def set_description(self, port: str, desc: str) -> str:
        """
        ## Устанавливаем описание для порта предварительно очистив его от лишних символов

        Если длина описания больше допустимой, то вернется ```"Max length:{max_length}"```

        Если была передана пустая строка для описания, то очищаем с помощью команды:

            (cfg)# clear port {port} description

        Если **desc** содержит описание, то используем команду для изменения:

            (cfg)# set port {port} description {desc}

        :param port: Порт, для которого вы хотите установить описание
        :param desc: Описание, которое вы хотите установить для порта
        :return: Вывод команды смены описания
        """

        if not self.__privileged:
            return "Не привилегированный. Операция отклонена!"

        desc = self.clear_description(desc)

        if desc == "":
            # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            status = self.send_command(
                f"clear port {port} description", expect_command=False
            )

        else:  # В другом случае, меняем описание на оборудовании
            status = self.send_command(
                f"set port {port} description {desc}", expect_command=False
            )

        if "Parameter too long" in status:
            # Если длина описания больше чем доступно на оборудовании
            output = self.send_command(f"set port {port} description ?")
            return "Max length:" + self.find_or_empty(r"maxsize:(\d+)", output)

        self.lock = False
        return (
            f'Description has been {"changed" if desc else "cleared"}.'
            + self.save_config()
        )

    @BaseDevice._lock
    @_validate_port(if_invalid_return={})
    def virtual_cable_test(self, port: str):
        """
        Эта функция запускает диагностику состояния линии на порту оборудования через команду:

            (cfg)# show vct port {port}

        Реализация виртуального тестирования линий **VCT** (Virtual Line Detection) благодаря TDR.
        С помощью этого метода модно выполнять диагностику неисправного состояния линии, например обрыв линии
        (Open), короткое замыкание (Short), рассогласование импеданса (Impedance Mismatch).
        Разница в сопротивлении (слишком большое затухание в линии).
        Плохая скрутка, либо кабель с некорректным сопротивлением. Или, к примеру, очень большая длина.

        Функция возвращает данные в виде словаря.
        В зависимости от результата диагностики некоторые ключи могут отсутствовать за ненадобностью.

        ```python
        {
            "len": "-",         # Длина кабеля в метрах, либо "-", когда не определено
            "status": "",       # Состояние на порту (Up, Down, Mismatch)
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

        Реализация виртуального тестирования линий **VCT** (Virtual Line Detection) благодаря TDR.
        С помощью этого метода модно выполнять диагностику неисправного состояния линии, например обрыв линии
        (Open), короткое замыкание (Short), рассогласование импеданса (Impedance Mismatch).
        """

        result = {
            "len": "-",  # Length
            "status": "",  # Up, Down
        }

        cable_diag = self.send_command(f"show vct port {port}")
        if "doesn't support VCT" in cable_diag:
            # Порт не поддерживает Virtual Cable Test
            result["status"] = "Doesn't support VCT"
            return result

        if "No problem" in cable_diag:
            # Нет проблем
            result["status"] = "Up"
            return result

        port_cable_diag = re.findall(
            r"Cable Test Passed[ .]+(with Impedance Mismatch|Cable is \S+)\.\s*\n\s+Approximately (\d+) meters",
            cable_diag,
        )

        result["status"] = "Down"

        # Смотрим пары
        for i, pair in enumerate(port_cable_diag, start=1):
            if "open" in pair[0].lower():
                status = "open"
            elif "short" in pair[0].lower():
                status = "short"
            else:
                # Разница в сопротивлении (слишком большое затухание в линии).
                # Плохая скрутка, либо кабель с некорректным сопротивлением. Или, к примеру, очень большая длина.
                status = "mismatch"

            result[f"pair{i}"] = {}
            result[f"pair{i}"]["status"] = status
            result[f"pair{i}"]["len"] = pair[1]

        if result["pair1"]["status"] == result["pair1"]["status"]:
            result["status"] = result["pair1"]["status"].capitalize()

        return result

    def get_port_info(self, port: str) -> str:
        return ""

    def get_device_info(self) -> dict:
        pass
