import re
from time import sleep
from functools import lru_cache, wraps, reduce
from typing import List

import pexpect
import textfsm
from django.template.loader import render_to_string

from .base import (
    BaseDevice,
    TEMPLATE_FOLDER,
    range_to_numbers,
    _interface_normal_view,
    InterfaceList,
    InterfaceVLANList,
    MACList,
)


class EltexBase(BaseDevice):
    """
    # Для оборудования от производителя Eltex

    Промежуточный класс, используется, чтобы определить модель оборудования
    """

    prompt = r"\S+#\s*"
    space_prompt = (
        r"More: <space>,  Quit: q or CTRL\+Z, One line: <return> |"
        r"More\? Enter - next line; Space - next page; Q - quit; R - show the rest\."
    )
    vendor = "Eltex"

    def __init__(self, session: pexpect, ip: str, auth: dict, model=""):
        """
        ## При инициализации смотрим характеристики устройства:

            # show system

          - MAC
          - Модель

        В зависимости от модели можно будет понять, какой класс для Eltex использовать далее

        :param session: Это объект сеанса pexpect c установленной сессией оборудования
        :param ip: IP-адрес устройства, к которому вы подключаетесь
        :param auth: словарь, содержащий имя пользователя и пароль для устройства
        :param model: Модель коммутатора
        """

        super().__init__(session, ip, auth, model)
        # Получение системной информации с устройства.
        system = self.send_command("show system")
        # Нахождение MAC-адреса устройства.
        self.mac = self.find_or_empty(r"System MAC [Aa]ddress:\s+(\S+)", system)
        # Регулярное выражение, которое ищет модель устройства.
        self.model = self.find_or_empty(
            r"System Description:\s+(\S+)|System type:\s+Eltex (\S+)", system
        )
        self.model = self.model[0] or self.model[1]

    def save_config(self):
        pass

    def get_mac(self, port) -> list:
        pass

    def get_interfaces(self) -> list:
        pass

    def get_vlans(self) -> list:
        pass

    def reload_port(self, port: str, save_config=True) -> str:
        pass

    def set_port(self, port: str, status: str, save_config=True) -> str:
        pass

    def set_description(self, port: str, desc: str) -> str:
        pass

    def get_port_info(self, port: str) -> str:
        pass

    def get_port_type(self, port: str) -> str:
        pass

    def get_port_config(self, port: str) -> str:
        pass

    def get_port_errors(self, port: str) -> str:
        pass

    def get_device_info(self) -> dict:
        pass


class EltexMES(BaseDevice):
    """
    # Для оборудования от производителя Eltex серия **MES**

    Проверено для:
     - 2324
     - 3324
    """

    # Регулярное выражение, соответствующее началу для ввода следующей команды.
    prompt = r"\S+#\s*$"
    # Строка, которая отображается, когда вывод команды слишком длинный и не помещается на экране.
    space_prompt = (
        r"More: <space>,  Quit: q or CTRL\+Z, One line: <return> |"
        r"More\? Enter - next line; Space - next page; Q - quit; R - show the rest\."
    )
    # Это переменная, которая используется для поиска файла шаблона для анализа вывода команды.
    _template_name = "eltex-mes"
    # Регулярное выражение, которое будет соответствовать MAC-адресу.
    mac_format = r"\S\S:" * 5 + r"\S\S"
    vendor = "Eltex"

    def __init__(self, session: pexpect, ip: str, auth: dict, model="", mac=""):
        """
        ## При инициализации смотрим характеристики устройства:

            # show inventory

          - серийный номер

        :param session: Это объект сеанса pexpect c установленной сессией оборудования
        :param ip: IP-адрес устройства, к которому вы подключаетесь
        :param auth: словарь, содержащий имя пользователя и пароль для устройства
        :param model: Модель коммутатора. Это используется для определения подсказки
        """

        super().__init__(session, ip, auth, model)
        self.mac = mac
        inv = self.send_command("show inventory", expect_command=False)
        # Нахождение серийного номера устройства.
        self.serialno = self.find_or_empty(r"SN: (\S+)", inv)

    def _validate_port(self=None, if_invalid_return=None):
        """
        ## Декоратор для проверки правильности порта Eltex

        :param if_invalid_return: что нужно вернуть, если порт неверный
        """

        if if_invalid_return is None:
            if_invalid_return = "Неверный порт"

        def validate(func):
            @wraps(func)
            def __wrapper(self, port="", *args, **kwargs):
                port = _interface_normal_view(port)
                if not port:
                    # Неверный порт
                    return if_invalid_return

                # Вызываем метод
                return func(self, port, *args, **kwargs)

            return __wrapper

        return validate

    @BaseDevice._lock
    def save_config(self):
        """
        ## Сохраняем конфигурацию оборудования

            # write
            Y

        Ожидаем ответа от оборудования **succeed**,
        если нет, то пробуем еще 2 раза, в противном случае ошибка сохранения
        """

        for _ in range(3):  # Пробуем 3 раза, если ошибка
            self.session.sendline("write")
            self.session.expect("write")
            status = self.send_command("Y", expect_command=False)
            if "succeed" in status:
                return self.SAVED_OK

        return self.SAVED_ERR

    @BaseDevice._lock
    def get_interfaces(self) -> InterfaceList:
        """
        ## Возвращаем список всех интерфейсов на устройстве

        Команда на оборудовании:

            # show interfaces description

        Считываем до момента вывода VLAN ```"Ch       Port Mode (VLAN)"```

        :return: ```[ ('name', 'status', 'desc'), ... ]```
        """

        self.session.sendline("show interfaces description")
        self.session.expect("show interfaces description")
        output = ""
        while True:
            # Ожидание prompt, space prompt или тайм-аута.
            match = self.session.expect(
                [self.prompt, self.space_prompt, pexpect.TIMEOUT]
            )
            output += self.session.before.decode("utf-8").strip()
            # Проверяем, есть ли в выводе строка "Ch Port Mode (VLAN)".
            # Если это так, он отправляем команду «q», а затем выходим из цикла.
            if "Ch       Port Mode (VLAN)" in output:
                self.session.sendline("q")
                self.session.expect(self.prompt)
                break
            if match == 0:
                break
            if match == 1:
                self.session.send(" ")
            else:
                print(self.ip, "Ошибка: timeout")
                break
        with open(
            f"{TEMPLATE_FOLDER}/interfaces/{self._template_name}.template",
            "r",
            encoding="utf-8",
        ) as template_file:
            # используем TextFSM для анализа вывода команды.
            int_des_ = textfsm.TextFSM(template_file)
            result = int_des_.ParseText(output)  # Ищем интерфейсы

        return [
            (
                line[0],  # interface
                line[2].lower() if "up" in line[1].lower() else "admin down",  # status
                line[3],  # desc
            )
            for line in result
            if not line[0].startswith("V")  # Пропускаем Vlan интерфейсы
        ]

    @BaseDevice._lock
    def get_vlans(self) -> InterfaceVLANList:
        """
        ## Возвращаем список всех интерфейсов и его VLAN на коммутаторе.

        Для начала получаем список всех интерфейсов через метод **get_interfaces()**

        Затем для каждого интерфейса смотрим конфигурацию

            # show running-config interface {interface_name}

        и выбираем строчки, в которых указаны VLAN:

         - ```vlan {vid}```
         - ```vlan add {vid},{vid},...{vid}```
         - ```vlan auto-all```

        :return: ```[ ('name', 'status', 'desc', [vid:int, vid:int, ... vid:int] ), ... ]```
        """

        result = []
        self.lock = False
        interfaces = self.get_interfaces()
        self.lock = True

        for line in interfaces:
            if not line[0].startswith("V"):
                output = self.send_command(
                    f"show running-config interface {_interface_normal_view(line[0])}",
                    expect_command=False,
                )
                # Ищем все строки вланов в выводе команды
                vlans_group = re.findall(r" vlan [ad ]*(\S*\d|auto-all)", output)
                port_vlans = []
                if vlans_group:
                    # Проверка, равен ли первый элемент в списке vlans_group "auto-all".
                    if vlans_group[0] == "auto-all":
                        # Создание списка вланов, которые будут назначены на порт.
                        port_vlans = ["1 to 4096"]
                    else:
                        port_vlans = vlans_group

                # Создаем список кортежей.
                # Первые три элемента кортежа — это имя порта, статус и описание.
                # Четвертый элемент — это список VLAN.
                result.append((line[0], line[1], line[2], port_vlans))

        return result

    @BaseDevice._lock
    @_validate_port(if_invalid_return=[])
    def get_mac(self, port) -> MACList:
        """
        ## Возвращаем список из VLAN и MAC-адреса для данного порта.

        Команда на оборудовании:

            # show mac address-table interface {port}

        :param port: Номер порта коммутатора
        :return: ```[ ('vid', 'mac'), ... ]```
        """

        mac_str = self.send_command(f"show mac address-table interface {port}")
        return re.findall(rf"(\d+)\s+({self.mac_format})\s+\S+\s+\S+", mac_str)

    @BaseDevice._lock
    @_validate_port()
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
        self.session.expect(r"#")
        self.session.sendline(f"interface {port}")
        self.session.sendline("shutdown")
        sleep(1)
        self.session.sendline("no shutdown")
        self.session.sendline("end")
        self.session.expect(r"#")
        r = self.session.before.decode(errors="ignore")

        self.lock = False
        s = self.save_config() if save_config else "Without saving"
        return r + s

    @BaseDevice._lock
    @_validate_port()
    def set_port(self, port, status, save_config=True):
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
        self.session.expect(r"\(config\)#")

        self.session.sendline(f"interface {port}")

        if status == "up":
            self.session.sendline("no shutdown")

        elif status == "down":
            self.session.sendline("shutdown")

        self.session.sendline("end")
        self.session.expect(r"#")

        r = self.session.before.decode(errors="ignore")

        self.lock = False
        s = self.save_config() if save_config else "Without saving"
        return r + s

    @_validate_port()
    @BaseDevice._lock
    def get_port_info(self, port):
        """
        ## Возвращает частичную информацию о порте.

        Пример

            Port: gi1/0/1
            Type: 1G-Fiber
            Link state: Up
            Auto negotiation: Enabled

        Через команду:

            # show interfaces advertise {port}

        :param port: Номер порта, для которого требуется получить информацию
        """

        info = self.send_command(f"show interfaces advertise {port}").split("\n")
        port_info_html = ""
        for line in info:
            if "Preference" in line:
                break
            port_info_html += f"<p>{line}</p>"

        return {"type": "html", "data": port_info_html}

    @_validate_port()
    def _get_port_stats(self, port):
        """
        ## Возвращает полную информацию о порте.

        Через команду:

            # show interfaces {port}

        :param port: Номер порта, для которого требуется получить информацию
        """

        return self.send_command(f"show interfaces {port}").split("\n")

    @_validate_port()
    def get_port_type(self, port) -> str:
        """
        ## Возвращает тип порта

        :param port: Порт для проверки
        :return: "SFP", "COPPER", "COMBO-FIBER", "COMBO-COPPER" или "?"
        """

        port_type = self.find_or_empty(
            r"Type: (\S+)", self.get_port_info(port).get("data")
        )
        if "Fiber" in port_type:
            return "SFP"
        if "Copper" in port_type:
            return "COPPER"
        if "Combo-F" in port_type:
            return "COMBO-FIBER"
        if "Combo-C" in port_type:
            return "COMBO-COPPER"
        return "?"

    @BaseDevice._lock
    @_validate_port()
    def get_port_config(self, port: str) -> str:
        """
        ## Выводим конфигурацию порта

        Используем команду:

            # show running-config interface {port}

        """

        return self.send_command(f"show running-config interface {port}").strip()

    @BaseDevice._lock
    @_validate_port()
    def get_port_errors(self, port: str) -> str:
        """
        ## Выводим ошибки на порту

        :param port: Порт для проверки на наличие ошибок
        """

        port_info = self._get_port_stats(port)
        errors = []
        for line in port_info:
            if "error" in line:
                errors.append(line.strip())
        return "\n".join(errors)

    @BaseDevice._lock
    @_validate_port()
    def set_description(self, port: str, desc: str) -> str:
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

        Если длина описания больше чем разрешено на оборудовании, то выводим ```"Max length:{number}"```

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

        if desc == "":
            # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            res = self.send_command("no description", expect_command=False)

        else:  # В другом случае, меняем описание на оборудовании
            res = self.send_command(f"description {desc}", expect_command=False)

        if "bad parameter value" in res:
            # Если длина описания больше чем доступно на оборудовании
            output = self.send_command("description ?")

            self.session.sendline("end")
            self.session.expect(self.prompt)

            return "Max length:" + self.find_or_empty(
                r" Up to (\d+) characters", output
            )

        self.session.sendline("end")
        self.session.expect(self.prompt)

        self.lock = False
        # Возвращаем строку с результатом работы и сохраняем конфигурацию
        return f'Description has been {"changed" if desc else "cleared"}. {self.save_config()}'

    def get_device_info(self) -> dict:
        pass


class EltexESR(EltexMES):
    """
    # Для оборудования от производителя Eltex серия **ESR**

    Проверено для:
     - ESR-12VF
    """

    _template_name = "eltex-esr"

    def __init__(self, session: pexpect, ip: str, auth: dict, model="", mac=""):
        """
        ## При инициализации смотрим характеристики устройства:

            # show inventory

          - серийный номер

        :param session: Это объект сеанса pexpect c установленной сессией оборудования
        :param ip: IP-адрес устройства, к которому вы подключаетесь
        :param auth: словарь, содержащий имя пользователя и пароль для устройства
        :param model: Модель коммутатора. Это используется для определения подсказки
        :param mac: MAC адрес коммутатора
        """

        self.session: pexpect = session
        self.ip: str = ip
        self.auth: dict = auth
        self.model: str = model
        self.mac: str = mac
        system = self.send_command("show system")
        self.serialno: str = self.find_or_empty(r"serial number:\s+(\S+)", system)
        self.lock = False

    @BaseDevice._lock
    def save_config(self):
        """
        ## Сохраняем конфигурацию оборудования

        Для ESR необходимо сделать коммит конфигурации, а затем подтвердить её

            # commit
            # confirm

        Ожидаем ответа от оборудования **Configuration has been confirmed**,
        если нет, то ошибка сохранения
        """

        self.session.sendline("commit")
        if (
            self.session.expect(
                [
                    self.prompt,  # 0
                    "Configuration has been successfully applied",  # 1
                    "Unknown command",  # 2
                ]
            )
            == 2  # Если неверная команда
        ):
            # Выходим из режима редактирования конфигурации
            self.session.sendline("end")
            self.session.sendline("commit")
            self.session.expect(
                [self.prompt, "Configuration has been successfully applied"]
            )

        # Подтверждаем изменение
        status = self.send_command("confirm")
        if "Configuration has been confirmed" in status:
            return self.SAVED_OK
        return self.SAVED_ERR

    @BaseDevice._lock
    @EltexMES._validate_port()
    def port_type(self, port: str) -> str:
        """
        ## Возвращает тип порта

        Используется команда:

            # show interfaces sfp

        :param port: Порт для проверки
        :return: "SFP" или "COPPER"
        """

        if "SFP present" in self.send_command(f"show interfaces sfp {port}"):
            return "SFP"
        return "COPPER"

    @BaseDevice._lock
    @EltexMES._validate_port()
    def get_port_info(self, port: str) -> dict:
        """
        ## Возвращаем информацию о порте.

        Через команду:

            # show interfaces status {port}

        :param port: Номер порта, для которого требуется получить информацию
        """

        info = self.send_command(
            f"show interfaces status {port}",
            expect_command=False,
            before_catch=r"Description:.+",
        )
        return {
            "type": "text",
            "data": info,
        }

    @BaseDevice._lock
    @EltexMES._validate_port()
    def get_port_errors(self, port: str) -> str:
        """
        ## Выводим ошибки на порту

        Используется команда:

            # show interfaces counters

        :param port: Порт для проверки на наличие ошибок
        """

        port_stat = self.send_command(f"show interfaces counters {port}").split("\n")

        errors = ""
        for line in port_stat:
            if "errors" in line:
                errors += line.strip() + "\n"
        return errors

    def get_device_info(self) -> dict:
        pass


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

    def __init__(self, session: pexpect, ip: str, auth: dict, model="LTP"):
        super().__init__(session, ip, auth)
        self.model = model

        # Проверяем, является ли модель LTP-4X.
        if "LTP-4X" in self.model:
            self._gpon_ports_count = 4
            self._10G_ports_count = 2
            self._front_ports_count = 4

        # Проверяем, является ли модель LTP-8X.
        elif "LTP-8X" in self.model:
            self._gpon_ports_count = 8
            self._10G_ports_count = 2
            self._front_ports_count = 8
        else:
            self._gpon_ports_count = 0
            self._10G_ports_count = 0
            self._front_ports_count = 0

    def send_command(
        self,
        command: str,
        before_catch: str = None,
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

    @BaseDevice._lock
    def save_config(self) -> str:
        """
        ## Сохраняем конфигурацию оборудования

            # commit

        Ожидаем ответа от оборудования **successfully**,
        """

        self.session.send(f"commit\r")
        if self.session.expect([self.prompt, r"successfully|Nothing to commit"]):
            return self.SAVED_OK
        return self.SAVED_ERR

    @BaseDevice._lock
    def get_interfaces(self) -> InterfaceList:
        self.session.send("switch\r")
        self.session.expect(self.prompt)
        interfaces = []

        interfaces_10gig_output = self.send_command(
            f"show interfaces status 10G-front-port 0 - {self._10G_ports_count - 1}",
            expect_command=False,
        )
        interfaces += re.findall(r"(10G\S+ \d+)\s+(\S{2,})\s+", interfaces_10gig_output)

        interfaces_front_output = self.send_command(
            f"show interfaces status front-port 0 - {self._front_ports_count - 1}",
            expect_command=False,
        )
        interfaces += re.findall(
            r"(front\S+ \d+)\s+(\S{2,})\s+", interfaces_front_output
        )

        interfaces_pon_output = self.send_command(
            f"show interfaces status pon-port 0 - {self._gpon_ports_count - 1}",
            expect_command=False,
        )
        interfaces += re.findall(r"(pon\S+ \d+)\s+(\S{2,})\s+", interfaces_pon_output)

        self.session.send("exit\r")
        self.session.expect(self.prompt)

        return [(line[0], line[1], "") for line in interfaces]

    @BaseDevice._lock
    def get_vlans(self) -> InterfaceVLANList:
        self.lock = False
        return [(line[0], line[1], line[2], []) for line in self.get_interfaces()]

    # Декоратор
    def _validate_port(self=None, if_invalid_return=None):
        """
        ## Декоратор для проверки правильности порта Eltex LTP

        :param if_invalid_return: что нужно вернуть, если порт неверный
        """

        if if_invalid_return is None:
            if_invalid_return = "Неверный порт"

        def validate(func):
            @wraps(func)
            def __wrapper(self, port="", *args, **kwargs):

                port_types = {
                    0: {
                        "name": "front-port",
                        "max-number": self._front_ports_count - 1,
                    },
                    1: {
                        "name": "10G-front-port",
                        "max-number": self._10G_ports_count - 1,
                    },
                    2: {
                        "name": "pon-port",
                        "max-number": self._gpon_ports_count - 1,
                    },
                }

                # Регулярное выражения для поиска трёх типов портов на Eltex LTP
                port_match = self.find_or_empty(
                    r"^front[-port]*\s*(\d+)$|"  # `0` - front-port
                    r"^10[Gg]-front[-port]*\s*(\d+)$|"  # `1` - 10G-front-port
                    r"^[gp]*on[-port]*\s*(\d+(?:[/\\]?\d*){,1})$",  # `2` - ont-port | gpon-port
                    port,
                )
                if not port_match:
                    # Неверный порт
                    return if_invalid_return

                for i, port_num in enumerate(port_match):
                    if not port_num:
                        # Пропускаем не найденное сравнение в регулярном выражении
                        continue

                    # Если порт представлен в виде `2/23`, то берем первую цифру `2` как port_num
                    num: str = (
                        port_num if port_num.isdigit() else port_num.split("/")[0]
                    )

                    # Проверка, меньше или равен ли номер порта максимальному количеству портов для этого типа.
                    if int(num) <= port_types[i]["max-number"]:
                        # port_type number
                        port = f"{port_types[i]['name']} {port_num}"
                        # Вызываем метод
                        return func(self, port, *args, **kwargs)

                # Неверный порт
                return if_invalid_return

            return __wrapper

        return validate

    @BaseDevice._lock
    @_validate_port(if_invalid_return=[])
    def get_mac(self, port: str) -> MACList:
        """
        Команда:

            # show mac include interface {port_type} {port}

        :param port:
        :return: ```[ ('vid', 'mac'), ... ]```
        """
        port_type, port_number = port.split()

        if port_number.isdigit():
            self.session.send("switch\r")
            self.session.expect(self.prompt)
            macs_output = self.send_command(
                f"show mac include interface {port_type} {port_number}",
            )
            self.session.send("exit\r")
            self.session.expect(self.prompt)
            return re.findall(rf"(\d+)\s+({self.mac_format})\s+\S+", macs_output)

        # Если указан порт конкретного ONT `0/1`, то используем другую команду
        # И другое регулярное выражение
        elif port_type == "pon-port" and re.match(r"^\d+/\d+$", port_number):
            macs_list = re.findall(
                rf"(\d+)\s+({self.mac_format})",
                self.send_command(f"show mac interface ont {port_number}"),
            )
            return macs_list

        # Если неверный порт
        return []

    @lru_cache
    def get_vlan_name(self, vid: int):
        from net_tools.models import VlanName

        vlan_name = ""
        try:
            vlan_name = VlanName.objects.get(vid=int(vid)).name
        except (ValueError, VlanName.DoesNotExist):
            pass
        finally:
            return vlan_name

    @BaseDevice._lock
    @_validate_port()
    def get_port_info(self, port: str) -> dict:

        # Получаем тип порта и его номер
        port_type, port_number = port.split()

        if port_type == "pon-port":
            # Данные для шаблона
            data = {}

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
            # сконфигурированных ONT в виде List[List], вместо List[Tuple].
            # Добавляем для каждой записи пустой список, который далее будет использоваться
            # для заполнения VLAN/MAC
            data["onts_lines"]: List[List] = onts_lines

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
                data["onts_lines"][int(ont_id)][6].append(
                    [vlan_id, mac, self.get_vlan_name(vlan_id)]
                )

            return {
                "type": "eltex-gpon",
                "data": data,
            }

        return {}

    @BaseDevice._lock
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
            res = self.send_command(f"send omci reset interface ont {port_number}")
            return res + "Without saving"

        return "Этот порт нельзя перезагружать"

    @BaseDevice._lock
    @_validate_port()
    def set_port(self, port: str, status: str, save_config=True) -> str:
        return "Этот порт нельзя установить в " + status

    @BaseDevice._lock
    @_validate_port()
    def set_description(self, port: str, desc: str) -> str:
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

        :param port: Порт, для которого вы хотите установить описание
        :param desc: Описание, которое вы хотите установить для порта
        :return: Вывод команды смены описания
        """

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
                res = self.send_command("no description", expect_command=False)

            else:  # В другом случае, меняем описание на оборудовании
                res = self.send_command(f"description {desc}", expect_command=False)

            self.session.send("exit\r")
            self.session.expect(self.prompt)
            self.session.send("exit\r")
            self.session.expect(self.prompt)

            self.lock = False
            # Возвращаем строку с результатом работы и сохраняем конфигурацию
            return f'Description has been {"changed" if desc else "cleared"}. {self.save_config()}'

    @BaseDevice._lock
    @_validate_port()
    def get_port_config(self, port: str) -> str:
        # Получаем тип порта и его номер
        port_type, port_number = port.split()
        if port_type == "pon-port" and re.match(r"^\d+/\d+$", port_number):
            # Для порта ONT вида - `0/1`
            return self.send_command(f"show interface ont {port_number} configuration")

        return ""

    @BaseDevice._lock
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
        elif "8X" in self.model and int(number) <= 3:
            return "COPPER"
        else:
            return "SFP"

    @BaseDevice._lock
    @_validate_port()
    def get_port_errors(self, port: str) -> str:
        pass

    def get_device_info(self) -> dict:
        pass


class EltexLTP16N(BaseDevice):
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

    def __init__(self, session: pexpect, ip: str, auth: dict, model="LTP-16N"):
        super().__init__(session, ip, auth)
        self.model = model

    @BaseDevice._lock
    def save_config(self) -> str:
        """
        ## Сохраняем конфигурацию оборудования

            # commit

        Ожидаем ответа от оборудования **successfully**,
        """

        self.session.send(f"commit\r")
        if self.session.expect([self.prompt, r"successfully|Nothing to commit"]):
            return self.SAVED_OK
        return self.SAVED_ERR

    @BaseDevice._lock
    def get_interfaces(self) -> InterfaceList:
        """
        Интерфейсы на оборудовании

        :return: ```[ ('name', 'status', 'desc'), ... ]```
        """

        interfaces = []

        interfaces_front_output = self.send_command(
            f"show interface front-port 1-8 state"
        )
        interfaces += [
            (f"front-port {line[0]}", line[1])
            for line in re.findall(r"(\d)\s+(\S+)", interfaces_front_output)
        ]

        interfaces_pon_output = self.send_command(f"show interface pon-port 1-16 state")
        interfaces += [
            (f"pon-port {line[0]}", line[1])
            for line in re.findall(r"(\d+)\s+(\S+).+[\r\n]", interfaces_pon_output)
        ]

        return [(line[0], line[1], "") for line in interfaces]

    @BaseDevice._lock
    def get_vlans(self) -> InterfaceVLANList:
        self.lock = False
        return [(line[0], line[1], line[2], []) for line in self.get_interfaces()]

    # Декоратор
    def _validate_port(self=None, if_invalid_return=None):
        """
        ## Декоратор для проверки правильности порта Eltex LTP

        :param if_invalid_return: что нужно вернуть, если порт неверный
        """

        if if_invalid_return is None:
            if_invalid_return = "Неверный порт"

        def validate(func):
            @wraps(func)
            def __wrapper(self, port="", *args, **kwargs):

                port_types = {
                    0: {
                        "name": "front-port",
                        "max-number": 8,
                    },
                    1: {
                        "name": "pon-port",
                        "max-number": 16,
                    },
                }

                # Регулярное выражения для поиска трёх типов портов на Eltex LTP
                port_match = self.find_or_empty(
                    r"^front[-port]*\s*(\d+)$|"  # `0` - front-port
                    r"^[gp]*on[-port]*\s*(\d+(?:[/\\]?\d*){,1})$",  # `2` - ont-port | gpon-port
                    port,
                )
                if not port_match:
                    # Неверный порт
                    return if_invalid_return

                for i, port_num in enumerate(port_match):
                    if not port_num:
                        # Пропускаем не найденное сравнение в регулярном выражении
                        continue

                    # Если порт представлен в виде `2/23`, то берем первую цифру `2` как port_num
                    num: str = (
                        port_num if port_num.isdigit() else port_num.split("/")[0]
                    )

                    # Проверка, меньше или равен ли номер порта максимальному количеству портов для этого типа.
                    if int(num) <= port_types[i]["max-number"]:
                        # port_type number
                        port = f"{port_types[i]['name']} {port_num}"
                        # Вызываем метод
                        return func(self, port, *args, **kwargs)

                # Неверный порт
                return if_invalid_return

            return __wrapper

        return validate

    @BaseDevice._lock
    @_validate_port(if_invalid_return=[])
    def get_mac(self, port: str) -> MACList:
        """
        Команда:

            # show mac verbose include interface {port_type} {port}

        :param port:
        :return: ```[ ('vid', 'mac'), ... ]```
        """
        port_type, port_number = port.split()

        if not port_number.isdigit():
            port_type = "ont"

        macs_output = self.send_command(
            f"show mac verbose include interface {port_type} {port_number}",
        )

        macs = []
        for line in re.findall(rf"({self.mac_format})\s+\S+\s\d+\s+(\d+)", macs_output):
            macs.append((line[1], line[0]))

        return macs

    @lru_cache
    def get_vlan_name(self, vid: int):
        from net_tools.models import VlanName

        vlan_name = ""
        try:
            vlan_name = VlanName.objects.get(vid=int(vid)).name
        except (ValueError, VlanName.DoesNotExist):
            pass
        finally:
            return vlan_name

    @BaseDevice._lock
    @_validate_port()
    def get_port_info(self, port: str):
        # Получаем тип порта и его номер
        port_type, port_number = port.split()

        if port_type == "pon-port":
            # Данные для шаблона
            data = {}

            # Смотрим ONLINE ONT
            ont_online_info = self.send_command(
                f"show interface ont {port_number} online"
            )
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
            ont_offline_info = self.send_command(
                f"show interface ont {port_number} offline"
            )
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

            # Добавляем в итоговый словарь список из отсортированных по возрастанию ONT ID записей
            data["onts_lines"]: List[List] = sorted(onts_lines, key=lambda x: int(x[0]))

            # Общее кол-во сконфигурированных ONT на данном порту
            data["total_count"] = len(data["onts_lines"])

            # Смотрим MAC на pon порту
            if port_number.isdigit():
                macs_list = re.findall(
                    rf"({self.mac_format})\s+\S+\s\d+\s+(\d+)\s+\d+/(\d+)",
                    self.send_command(
                        f"show mac verbose include interface pon-port {port_number}"
                    ),
                )
            else:
                macs_list = []

            # Перебираем список macs_list и назначаем каждому ONT ID свой VLAN/MAC
            for mac, vlan_id, ont_id in macs_list:
                # Выбираем запись ONT по индексу ONT ID - int(mac_line[0])
                for ont in data["onts_lines"]:
                    if ont[0] == ont_id:
                        # Затем обращаемся к 6 элементу, в котором находится список VLAN/MAC
                        # и добавляем VLAN, MAC и описание VLAN
                        ont[6].append([vlan_id, mac, self.get_vlan_name(vlan_id)])

            return {
                "type": "eltex-gpon",
                "data": data,
            }

        return {}

    @BaseDevice._lock
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

    @BaseDevice._lock
    @_validate_port()
    def set_port(self, port: str, status: str, save_config=True) -> str:
        pass

    @BaseDevice._lock
    @_validate_port()
    def set_description(self, port: str, desc: str) -> str:
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

        :param port: Порт, для которого вы хотите установить описание
        :param desc: Описание, которое вы хотите установить для порта
        :return: Вывод команды смены описания
        """

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
                res = self.send_command("no description", expect_command=False)

            else:  # В другом случае, меняем описание на оборудовании
                res = self.send_command(f"description {desc}", expect_command=False)

            self.session.send("exit\r")
            self.session.expect(self.prompt)
            self.session.send("exit\r")
            self.session.expect(self.prompt)

            self.lock = False

            # Возвращаем строку с результатом работы и сохраняем конфигурацию
            return f'Description has been {"changed" if desc else "cleared"}. {self.save_config()}'

    @BaseDevice._lock
    @_validate_port()
    def get_port_config(self, port: str) -> str:
        # Получаем тип порта и его номер
        port_type, port_number = port.split()
        if port_type == "pon-port" and re.match(r"^\d+/\d+$", port_number):
            # Для порта ONT вида - `0/1`
            return self.send_command(f"show interface ont {port_number} configuration")

        return ""

    @_validate_port(if_invalid_return="?")
    def get_port_type(self, port: str) -> str:
        return "SFP"

    @_validate_port()
    def get_port_errors(self, port: str) -> str:
        return ""

    def get_device_info(self) -> dict:
        pass
