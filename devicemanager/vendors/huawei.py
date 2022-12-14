import datetime
import re
import pexpect
import textfsm
from time import sleep
from functools import lru_cache
from typing import Tuple
from django.template.loader import render_to_string
from .base import (
    BaseDevice,
    TEMPLATE_FOLDER,
    COOPER_TYPES,
    FIBER_TYPES,
    range_to_numbers,
    _interface_normal_view,
    InterfaceList,
    InterfaceVLANList,
    MACList,
)


SplittedPort: type = Tuple[str, Tuple[str]]


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

    def __init__(self, session: pexpect, ip: str, auth: dict, model=""):
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

        super().__init__(session, ip, auth, model)
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
            [r"<\S+>", r"\[\S+\]"]  # 0 - режим просмотра  # 1 - режим редактирования
        ):
            # Если находимся в режиме редактирования, то понижаем до режима просмотра
            self.session.sendline("quit")
            self.session.expect(r"<\S+>$")

        version = self.send_command("display version")
        # Нахождение модели устройства.
        self.model = self.find_or_empty(
            r"Quidway (\S+) [Routing Switch]*uptime", version
        )

        if "S2403" in self.model:
            manuinfo = self.send_command("display device manuinfo")
            # Нахождение MAC-адреса устройства.
            self.mac = self.find_or_empty(r"MAC ADDRESS\s+:\s+(\S+)", manuinfo)
            # Нахождение серийного номера устройства.
            self.serialno = self.find_or_empty(
                r"DEVICE SERIAL NUMBER\s+:\s+(\S+)", manuinfo
            )

        elif "S2326" in self.model:
            mac = self.send_command("display bridge mac-address")
            # Нахождение mac адреса устройства.
            self.mac = self.find_or_empty(
                r"System Bridge Mac Address\s+:\s+(\S+)\.", mac
            )

            elabel = self.send_command("display elabel")
            # Нахождение серийного номера устройства.
            self.serialno = self.find_or_empty(r"BarCode=(\S+)", elabel)

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

    def get_interfaces(self) -> InterfaceList:
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

        with open(
            f"{TEMPLATE_FOLDER}/interfaces/{ht}.template", "r", encoding="utf-8"
        ) as template_file:
            int_des_ = textfsm.TextFSM(template_file)
            result = int_des_.ParseText(output)  # Ищем интерфейсы
        return [
            (
                line[0],  # interface
                line[1]
                .lower()
                .replace("adm", "admin")
                .replace("*", "admin "),  # status
                line[2],  # desc
            )
            for line in result
            if not line[0].startswith("NULL") and not line[0].startswith("V")
        ]

    def get_vlans(self) -> InterfaceVLANList:
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

        interfaces = self.get_interfaces()
        result = []
        for line in interfaces:
            if (
                not line[0].startswith("V")
                and not line[0].startswith("NU")
                and not line[0].startswith("A")
            ):
                output = self.send_command(
                    f"display current-configuration interface {_interface_normal_view(line[0])}",
                    expect_command=False,
                )

                vlans_group = re.sub(
                    r"(?<=undo).+vlan (.+)", "", output
                )  # Убираем строчки, где есть "undo"
                vlans_group = list(
                    set(re.findall(r"vlan (.+)", vlans_group))
                )  # Ищем строчки вланов, без повторений
                port_vlans = []
                for v in vlans_group:
                    port_vlans = range_to_numbers(v)
                result.append((line[0], line[1], line[2], [port_vlans]))

        return result

    def get_mac(self, port) -> MACList:
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
            mac_str = self.send_command(
                f"display mac-address interface {_interface_normal_view(port)}"
            )
            for i in re.findall(
                r"(" + self.mac_format + r")\s+(\d+)\s+\S+\s+\S+\s+\S+", mac_str
            ):
                mac_list.append(i[::-1])

        elif "2326" in self.model:
            mac_str = self.send_command(
                f"display mac-address {_interface_normal_view(port)}"
            )

            if "Wrong parameter" in mac_str:
                # Если необходимо ввести тип
                mac_str1 = self.send_command(
                    f"display mac-address dynamic {_interface_normal_view(port)}",
                    expect_command=False,
                )
                mac_str2 = self.send_command(
                    f"display mac-address secure-dynamic {_interface_normal_view(port)}",
                    expect_command=False,
                )
                mac_str = mac_str1 + mac_str2

            for i in re.findall(r"(" + self.mac_format + r")\s+(\d+)", mac_str):
                mac_list.append(i[::-1])

        return mac_list

    @lru_cache
    def __port_info(self, port):
        """
        ## Возвращаем полную информацию о порте.

        Через команду:

            > display interface {port}

        :param port: Номер порта, для которого требуется получить информацию
        """

        return self.send_command(f"display interface {_interface_normal_view(port)}")

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
            [
                line.strip()
                for line in errors
                if "error" in line.lower() or "CRC" in line
            ]
        )

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
        self.session.sendline(f"interface {_interface_normal_view(port)}")
        self.session.sendline("shutdown")
        sleep(1)
        self.session.sendline("undo shutdown")
        self.session.sendline("quit")
        self.session.expect(self.prompt)
        self.session.sendline("quit")
        self.session.expect(self.prompt)
        r = self.session.before.decode(errors="ignore")
        s = self.save_config() if save_config else "Without saving"
        return r + s

    def set_port(self, port, status, save_config=True) -> str:
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
        self.session.sendline(f"interface {_interface_normal_view(port)}")
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
        s = self.save_config() if save_config else "Without saving"
        return r + s

    def get_port_config(self, port):
        """
        ## Выводим конфигурацию порта

        Используем команду:

            > display current-configuration interface {port}
        """

        config = self.send_command(
            f"display current-configuration interface {_interface_normal_view(port)}",
            expect_command=False,
            before_catch=r"#",
        )
        return config

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
        self.session.sendline(f"interface {_interface_normal_view(port)}")

        desc = self.clear_description(desc)  # Очищаем описание от лишних символов

        if desc == "":
            # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            status = self.send_command("undo description", expect_command=False)

        else:  # В другом случае, меняем описание на оборудовании
            status = self.send_command(f"description {desc}", expect_command=False)

        if "Wrong parameter found" in status:
            # Если длина описания больше чем доступно на оборудовании
            output = self.send_command("description ?")
            return "Max length:" + self.find_or_empty(
                r"no more than (\d+) characters", output
            )

        self.session.sendline("quit")
        self.session.expect(self.prompt)
        self.session.sendline("quit")
        self.session.expect(self.prompt)

        return (
            f'Description has been {"changed" if desc else "cleared"}.'
            + self.save_config()
        )

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
            return parse_data

        if "2326" in self.model:
            # Для Huawei 2326
            parse_data["pair1"]["len"] = self.find_or_empty(
                r"Pair A length: (\d+)meter", data
            )
            parse_data["pair2"]["len"] = self.find_or_empty(
                r"Pair B length: (\d+)meter", data
            )
            parse_data["pair1"]["status"] = self.find_or_empty(
                r"Pair A state: (\S+)", data
            ).lower()
            parse_data["pair2"]["status"] = self.find_or_empty(
                r"Pair B state: (\S+)", data
            ).lower()

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

            status = self.find_or_empty(
                r"Cable status: (normal)", data
            ) or self.find_or_empty(r"Cable status: abnormal\((\S+)\),", data)

            parse_data["status"] = "Up" if status == "normal" else status.capitalize()
            del parse_data["pair1"]
            del parse_data["pair2"]

        return parse_data

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
        self.session.sendline(f"interface {_interface_normal_view(port)}")
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
        return self.__parse_virtual_cable_test_data(
            cable_test_data
        )  # Парсим полученные данные

    def get_port_info(self, port: str) -> str:
        return ""


class HuaweiMA5600T(BaseDevice):
    """
    # Для DSLAM оборудования MA5600T от производителя Huawei
    """

    prompt = r"config\S+#|\S+#"
    space_prompt = r"---- More \( Press \'Q\' to break \) ----"
    # Регулярное выражение, которое соответствует MAC-адресу.
    mac_format = r"\S\S\S\S-\S\S\S\S-\S\S\S\S"
    vendor = "Huawei"

    def __init__(self, session: pexpect, ip: str, auth: dict, model=""):
        """
        При инициализации активируем режим пользователя командой:

            # enable

        :param session: Это объект сеанса pexpect c установленной сессией оборудования
        :param ip: IP-адрес устройства, к которому вы подключаетесь
        :param auth: словарь, содержащий имя пользователя и пароль для устройства
        :param model: Модель коммутатора
        """

        super().__init__(session, ip, auth, model)
        self.session.sendline("enable")
        self.session.expect(r"\S+#")

    def send_command(
        self,
        command: str,
        before_catch: str = None,
        expect_command=True,
        num_of_expect=10,
        space_prompt=None,
        prompt=None,
        pages_limit=None,
        command_linesep="\n",
    ) -> str:
        """
        ## Отправляет команду на оборудование и считывает её вывод

        Вывод будет содержать в себе строки от момента ввода команды, до (prompt: str), указанного в классе

        При вводе некоторых команд оборудование будет запрашивать продолжение команды после её ввода, например:
        ```{ <cr>|ontid<U><0,255> }:```, которое не требуется для указанной команды.
        Если встречается строка ```}:```, будет отправлено пустое значение и продолжится запись результата команды

        :param command: Команда, которую необходимо выполнить на оборудовании
        :param before_catch: Регулярное выражение, указывающее начало
        :param expect_command: Не вносить текст команды в вывод
        :param num_of_expect: Кол-во символов с конца команды, по которым необходимо её находить
        :param space_prompt: Регулярное выражение, которое указывает на ожидание ввода клавиши,
                             для последующего отображения информации
        :param prompt: Регулярное выражение, которое указывает на приглашение для ввода следующей команды
        :param pages_limit: Кол-во страниц, если надо, которые будут выведены при постраничном отображении
        :param command_linesep: Символ отправки команды (по умолчанию ```\\\\n```)
        :return: Строка с результатом команды
        """

        if space_prompt is None:
            space_prompt = self.space_prompt
        if prompt is None:
            prompt = self.prompt

        output = ""
        self.session.send(command + command_linesep)  # Отправляем команду

        if expect_command:
            self.session.expect(
                command[-num_of_expect:]
            )  # Считываем введенную команду с поправкой по длине символов
        if before_catch:
            self.session.expect(before_catch)

        if space_prompt:  # Если необходимо постранично считать данные, то создаем цикл
            while pages_limit is None or pages_limit > 0:
                match = self.session.expect(
                    [
                        prompt,  # 0 - конец
                        space_prompt,  # 1 - далее
                        pexpect.TIMEOUT,  # 2
                        r"\}:",  # 3 { <cr>|ontid<U><0,255> }:
                    ],
                    timeout=20,
                )

                # Управляющие последовательности ANSI
                ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

                # Убираем их
                output += ansi_escape.sub(
                    "", self.session.before.decode(errors="ignore")
                )

                if match == 0:
                    break
                if match == 1:
                    # Отправляем символ пробела, для дальнейшего вывода
                    self.session.send(" ")
                    output += "\n"
                elif match == 3:
                    # { <cr>|ontid<U><0,255> }:
                    self.session.send("\n")
                else:
                    print(
                        f'{self.ip} - timeout во время выполнения команды "{command}"'
                    )
                    break

                # Если задано кол-во страниц
                if pages_limit:
                    pages_limit -= 1

        else:  # Если вывод команды выдается полностью, то пропускаем цикл
            try:
                self.session.expect(prompt)
            except pexpect.TIMEOUT:
                pass
            output = re.sub(
                r"\\x1[bB]\[\d\d\S", "", self.session.before.decode(errors="ignore")
            )
        return output

    def save_config(self):
        pass

    def get_port_config(self, port: str) -> str:
        """
        ## Выводим конфигурацию порта

        В данный момент выводит информацию только для ONT

        Используем команду:

            # display current-configuration ont {i0}/{i1}/{i2} {i3}

        """

        port_type, indexes = self.split_port(port)

        # Для GPON ONT используем отдельный поиск
        if port_type == "gpon" and len(indexes) == 4:
            i: tuple = indexes
            self.session.sendline("config")
            self.session.expect(self.prompt)
            config = self.send_command(
                f"display current-configuration ont {i[0]}/{i[1]}/{i[2]} {i[3]}",
                prompt=r"\S+config\S+#",
                expect_command=False,
                before_catch=r"\[\S+: \S+\]",
            )
            self.session.sendline("quit")
            self.session.expect(self.prompt)
            # Меняем "<" ">" на их представление, чтобы не обозначалось как теги html
            return config.replace("<", "&#8249;").replace(">", "&#8250;")

        return ""

    def split_port(self, port: str) -> SplittedPort:
        """
        ## Разделяет строку порта на тип интерфейса и плата, слот, порт

        >>> self.split_port("ADSL 0/2/4")
        ('adsl', ('0', '2', '4'))

        >>> self.split_port("GPON 0/6/7/1")
        ('gpon', ('0', '6', '7', '1'))

        >>> self.split_port("ethernet0/9/1")
        ('eth', ('0', '9', '1'))

        Также смотрит слоты:

            # display board {i0}

            #------------------------------------------------------------------------
            SlotID  BoardName  Status         SubType0 SubType1    Online/Offline
            #------------------------------------------------------------------------
            0
            1
            2       H808ADLF   Normal
            3       H808ADLF   Normal
            4       H808ADLF   Normal
            5       H808ADLF   Normal
            6       H808ADLF   Normal
            7
            8       H805ADPD   Normal
            9       H801SCUB   Active_normal

        На 9 слоте плата **H801SCUB**, значит результатом будет:

        >>> self.split_port('ethernet0/9/2')
        ('scu', ('0', '9', '2'))

        """

        # Преобразование порта в нижний регистр и удаление всех пробелов.
        port = port.lower().strip()
        # Нахождение типа порта.
        port_type = self.find_or_empty(r"^ethernet|^[av]dsl|^gpon", port)
        # Удаление букв в имени порта и последующее разделение строки на "/"
        indexes = re.sub(r"^[a-z]+", "", port).split("/")
        if port_type == "ethernet":
            board_info = self.send_command(f"display board {indexes[0]}")

            board_list = self.find_or_empty(
                rf"\s+({indexes[1]})\s+(\S+)\s+\S+", board_info
            )
            if board_list:
                if "SCU" in board_list[1]:
                    return "scu", tuple(indexes)
                if "GI" in board_list[1]:
                    return "giu", tuple(indexes)

            return "eth", tuple(indexes)

        return port_type, tuple(indexes)

    def render_adsl_port_info(
        self, info: str, profile_name: str, all_profiles: list
    ) -> str:
        """
        ## Преобразовываем информацию о ADSL порте для отображения на странице

        ``````[ ('name', 'status', 'desc'), ... ]``````

        :param info: Информация порта ADSL
        :param profile_name: Название текущего профиля
        :param all_profiles: Все существующие ADSL профиля на оборудовании
        """

        def color(val: float, s: str) -> str:
            """Определяем цвета в зависимости от числовых значений показателя"""
            if "channel SNR margin" in s:
                gradient = [5, 7, 10, 20]
            elif "channel attenuation" in s:
                gradient = [-60, -50, -40, -20]
                val = -val
            elif "total output power" in s:
                return "#95e522" if val >= 10 else "#e5a522"
            else:
                return ""
            # проверяем значения по градиенту
            if val <= gradient[0]:
                return "#e55d22"
            if val <= gradient[1]:
                return "#e5a522"
            if val <= gradient[2]:
                return "#dde522"
            if val <= gradient[3]:
                return "#95e522"

            return "#22e536"

        lines = info.strip().split("\n")  # Построчно создаем список

        up_down_streams = {"Do": [], "Up": []}  # Down Stream info  # Up   Stream info

        first_col_info = []  # Информация про порт

        for line in lines:  # Построчно смотрим данные
            line = line.strip()

            if line.startswith("-" * 10):
                # Прерываем, если дошли до строки с разделителем ------------
                break

            if not re.findall(r"^[DU].+?(-?\d+\.?\d*)", line):
                first_col_info.append(line)
            else:
                value = self.find_or_empty(r"-?\d+\.?\d*", line)  # Числовое значение
                if value:
                    line_new = {"color": color(float(value), line), "value": value}
                else:  # Если нет значения - ошибка
                    line_new = {"color": "#e55d22", "value": 0}

                # Обновляем ключ "Do" или "Up"
                up_down_streams[line[:2]].append(line_new)

        names = [
            "Фактическая скорость передачи данных (Кбит/с)",
            "Максимальная скорость передачи данных (Кбит/с)",
            "Сигнал/Шум (дБ)",
            "Interleaved channel delay (ms)",
            "Затухание линии (дБ)",
            "Общая выходная мощность (dBm)",
        ]

        # Создаем список из элементов:
        # {
        #   'name': 'Фактическая скорость передачи данных (Кбит/с)',
        #   'down': {'color': 'red', 'value': 34.1},
        #   'up': {'color': 'red', 'value': 34.1}
        # }, ...
        table_dict = [
            {"name": line[0], "down": line[1], "up": line[2]}
            for line in zip(names, up_down_streams["Do"], up_down_streams["Up"])
        ]

        return render_to_string(
            "check/adsl-port-info.html",
            {
                "profile_name": profile_name,
                "first_col": first_col_info,
                "streams": table_dict,
                "profiles": all_profiles,
            },
        )

    def render_gpon_port_info(
        self, indexes: (Tuple[str, str, str], Tuple[str, str, str, str])
    ):
        """
        ## Преобразовываем информацию о GPON порте для отображения на странице
        """

        from check.models import Devices

        # Проверяем индексы
        if not isinstance(indexes, tuple) or len(indexes) not in [3, 4]:
            return f'Неверный порт! (GPON {"/".join(indexes)})'

        self.session.sendline("config")  # Переходим в режим конфигурации
        self.session.expect(self.prompt)
        i: tuple = indexes  # Упрощаем запись переменной

        # GPON
        if len(indexes) == 3:
            # Смотрим порт
            output = self.send_command(
                f'display ont info summary {"/".join(i)}',
                before_catch="Please wait",
                expect_command=False,
            )
            self.session.sendline("quit")

            data = {
                "device": Devices.objects.get(ip=self.ip).name,
                "port": f'GPON {"/".join(i)}',
                "total_count": self.find_or_empty(
                    r"the total of ONTs are: (\d+), online: \d+", output
                ),
                "online_count": self.find_or_empty(
                    r"the total of ONTs are: \d+, online: (\d+)", output
                ),
            }

            lines = re.findall(
                r"(\d+)\s+(online|offline)\s+(\d+-\d+-\d+ \d+:\d+:\d+)\s+(\d+-\d+-\d+ \d+:\d+:\d+)\s+(\S+)",
                output,
            )

            ont_info = re.findall(
                r"\d+\s+\S+\s+\S+\s+([-\d]+)\s+(-?\d+\.?\d+/-?\d+\.?\d+|-/-)\s+\S+",
                output,
            )

            data["onts_lines"] = []

            for j in range(len(lines)):
                part1 = list(lines[j])
                part2 = list(ont_info[j])

                part1[2] = datetime.datetime.strptime(part1[2], "%Y-%m-%d %H:%M:%S")
                part1[3] = datetime.datetime.strptime(part1[3], "%Y-%m-%d %H:%M:%S")

                data["onts_lines"].append(part1 + part2)

            return render_to_string("check/gpon_port_info.html", data)

        # Смотрим ONT
        data = self.ont_port_info(indexes=i)
        self.session.sendline("quit")
        return render_to_string("check/ont_port_info.html", {"ont_info": data})

    @lru_cache
    def ont_port_info(self, indexes: tuple) -> list:
        """
        ## Смотрим информацию на конкретном ONT

            # display ont wan-info {i0}/{i1} {i2} {i3}

        Возвращаем список сервисов у абонента:

        ```python
        {
            "type": "",
            "index": "",
            "ipv4_status": "",
            "ipv4_access_type": "",
            "ipv4_address": "",
            "subnet_mask": "",
            "manage_vlan": "",
            "mac": "",
        }
        ```

        """
        i: tuple = indexes  # Упрощаем запись переменной
        info = self.send_command(
            f"display ont wan-info {i[0]}/{i[1]} {i[2]} {i[3]}", expect_command=False
        )
        data = []  # Общий список

        # Разделяем на сервисы
        parts = info.split(
            "---------------------------------------------------------------"
        )

        for service_part in parts:
            if "Service type" not in service_part:
                # Пропускаем те части, которые не содержат информации о сервисе
                continue

            data.append(
                {
                    "type": self.find_or_empty(r"Service type\s+: (\S+)", service_part),
                    "index": self.find_or_empty(r"Index\s+: (\d+)", service_part),
                    "ipv4_status": self.find_or_empty(
                        r"IPv4 Connection status\s+: (\S+)", service_part
                    ),
                    "ipv4_access_type": self.find_or_empty(
                        r"IPv4 access type\s+: (\S+)", service_part
                    ),
                    "ipv4_address": self.find_or_empty(
                        r"IPv4 address\s+: (\S+)", service_part
                    ),
                    "subnet_mask": self.find_or_empty(
                        r"Subnet mask\s+: (\S+)", service_part
                    ),
                    "manage_vlan": self.find_or_empty(
                        r"Manage VLAN\s+: (\d+)", service_part
                    ),
                    "mac": self.find_or_empty(
                        r"MAC address\s+: ([0-9A-F]+-[0-9A-F]+-[0-9A-F]+)", service_part
                    ),
                }
            )

        return data

    def render_vdsl_port_info(self, info: str, profile_name: str, all_profiles: list):
        """
        ## Преобразовываем информацию о VDSL порте для отображения на странице

        ------------------------------------------------------
        -  Line attenuation downstream(dB)            : 9.5
        -  Line attenuation upstream(dB)              : 10.7
        -  Maximum attainable rate downstream(Kbps)   : 20076
        -  Maximum attainable rate upstream(Kbps)     : 1315
        -  Actual line rate downstream(Kbps)          : 17324
        -  Actual line rate upstream(Kbps)            : 1384
        -  Line SNR margin downstream(dB)             : 12.9
        -  Line SNR margin upstream(dB)               : 8.1
        -  Total output power downstream(dBm)         : -8.7
        -  Total output power upstream(dBm)           : 11.1
        """

        def color(val: float, s: str) -> str:
            """Определяем цвета в зависимости от числовых значений показателя"""
            if "SNR margin" in s:
                gradient = [5, 7, 10, 20]
            elif "attenuation" in s:
                gradient = [-60, -50, -40, -20]
                val = -val
            elif "output power" in s:
                return "#95e522" if val >= 10 else "#e5a522"
            else:
                return ""
            # проверяем значения по градиенту
            if val <= gradient[0]:
                return "#e55d22"
            if val <= gradient[1]:
                return "#e5a522"
            if val <= gradient[2]:
                return "#dde522"
            if val <= gradient[3]:
                return "#95e522"

            return "#22e536"

        up_down_streams = [
            {
                "name": "Фактическая скорость передачи данных (Кбит/с)",
                "down": {},
                "up": {},
            },
            {
                "name": "Максимальная скорость передачи данных (Кбит/с)",
                "down": {},
                "up": {},
            },
            {
                "name": "Сигнал/Шум (дБ)",
                "down": {},
                "up": {},
            },
            {
                "name": "Затухание линии (дБ)",
                "down": {},
                "up": {},
            },
            {
                "name": "Общая выходная мощность (dBm)",
                "down": {},
                "up": {},
            },
        ]

        for line in info.split("\n"):  # Построчно смотрим данные

            if "Actual line rate downstream" in line:
                index = 0
                stream = "down"
            elif "Actual line rate upstream" in line:
                index = 0
                stream = "up"

            elif "Maximum attainable rate downstream" in line:
                index = 1
                stream = "down"
            elif "Maximum attainable rate upstream" in line:
                index = 1
                stream = "up"

            elif "Line SNR margin downstream" in line:
                index = 2
                stream = "down"
            elif "Line SNR margin upstream" in line:
                index = 2
                stream = "up"

            elif "Line attenuation downstream" in line:
                index = 3
                stream = "down"
            elif "Line attenuation upstream" in line:
                index = 3
                stream = "up"

            elif "Total output power downstream" in line:
                index = 4
                stream = "down"
            elif "Total output power upstream" in line:
                index = 4
                stream = "up"

            else:
                continue

            value = self.find_or_empty(r"-?\d+\.?\d*", line)
            up_down_streams[index][stream]["value"] = value
            up_down_streams[index][stream]["color"] = color(float(value), line)

        return render_to_string(
            "check/adsl-port-info.html",
            {
                "profile_name": profile_name,
                "first_col": [],
                "streams": up_down_streams,
                "profiles": all_profiles,
            },
        )

    def vdsl_port_info(self, indexes: tuple):
        """
        ## Смотрим информацию на VDSL порту
        """

        self.session.sendline("config")

        self.session.sendline(f"interface vdsl {indexes[0]}/{indexes[1]}")
        self.session.expect(self.prompt)

        port_stats = self.send_command(
            f"display line operation {indexes[2]}", expect_command=False
        )

        # Индекс текущего шаблона
        current_line_template_index = self.find_or_empty(
            r"\s\d+\s+\S+\s+\S+\s+(\d+)",
            self.send_command(f"display port state {indexes[2]}", expect_command=False),
        )

        # Все шаблоны профилей:
        #   Template  Template
        #   Index     Name
        #   ------------------------------
        #          1  DEFVAL
        #          2  VDSL LINE TEMPLATE 2
        #          3  VDSL LINE TEMPLATE 3
        #          4  NO_CHANGE
        #          5  VDSL
        line_templates = sorted(
            re.findall(
                r"\s+(\d+)\s+(.+)",
                self.send_command(
                    "display vdsl line-template info", expect_command=False
                ),
            ),
            key=lambda x: int(x[0]),  # Сортируем по убыванию индекса
            reverse=True,
        )

        template_name = ""
        # Ищем имя текущего шаблона
        for line in line_templates:
            if line[0] == current_line_template_index:
                template_name = line[1]

        self.session.sendline("quit")
        self.session.sendline("quit")
        self.session.expect(self.prompt)

        return self.render_vdsl_port_info(port_stats, template_name, line_templates)

    def get_port_info(self, port: str) -> str:
        """
        ## Смотрим информацию на порту

        В зависимости от порта вывод различается

        :param port: Порт
        :return: Информация о порте либо ```"Неверный порт!"```
        """

        port_type, indexes = self.split_port(port)

        # Для GPON используем отдельный метод
        if port_type == "gpon":
            return self.render_gpon_port_info(indexes=indexes)

        # Для других
        if not port_type or len(indexes) != 3:
            return f"Неверный порт! ({port})"

        # Для VDSL используем отдельный метод
        if port_type == "vdsl":
            return self.vdsl_port_info(indexes=indexes)

        self.session.sendline("config")
        self.session.sendline(f"interface {port_type} {indexes[0]}/{indexes[1]}")
        self.session.expect(r"\S+#")
        self.session.sendline(f"display line operation {indexes[2]}")
        if self.session.expect([r"Are you sure to continue", "Unknown command"]):
            return ""
        output = self.send_command(
            "y", expect_command=True, before_catch=r"Failure|------[-]+"
        )

        if "is not activated" in output:  # У данного порта нет таких команд
            return ""

        profile_output = self.send_command(f"display port state {indexes[2]}")
        profile_index = self.find_or_empty(r"\s+\d+\s+\S+\s+(\d+)", profile_output)
        profile_output = self.send_command(f"display adsl line-profile {profile_index}")
        self.session.sendline("quit")
        self.session.sendline("quit")
        self.session.expect(r"\S+#")
        all_profiles = self.send_command(
            "display adsl line-profile\n",
            before_catch="display adsl line-profile",
            expect_command=False,
        )

        profile_name = self.find_or_empty(r"Name:\s+(\S+)", profile_output)

        # Парсим профиля
        res = re.findall(
            r"(\d+)\s+(.+?)\s+\S+\s+\S+\s+\d+\s+\d+\s+(\d+)\s+(\d+)([\s\S]*?)(?= \d+ \S+[ ]+\S+)",
            all_profiles,
        )

        profiles = []
        for line in res:
            line = list(line)
            profiles.append(
                [line[0], line[1] + line[-1].replace(" ", "").replace("\n", "")]
            )

        return self.render_adsl_port_info(output, profile_name, profiles)

    def change_profile(self, port: str, profile_index: int) -> str:
        """
        ## Меняем профиль на xDSL порту

        :param port: Порт
        :param profile_index: Индекс нового профиля
        :return: Статус изменения профиля либо "Неверный порт!"
        """

        port_type, indexes = self.split_port(port)

        # Проверяем индекс профиля и порт
        if port_type not in ["adsl", "vdsl"] or len(indexes) != 3 or profile_index <= 0:
            return "Неверный порт!"

        if port_type == "adsl":
            # Если порт ADSL, то команда для смена профиля
            change_profile_cmd = "profile-index"
        else:
            # Если порт VDSL
            change_profile_cmd = "template-index"

        self.session.sendline("config")
        self.session.sendline(f"interface {port_type} {indexes[0]}/{indexes[1]}")
        self.session.expect(self.prompt)
        self.session.sendline(f"deactivate {indexes[2]}")
        self.session.expect(self.prompt)
        status = self.send_command(
            f"activate {indexes[2]} {change_profile_cmd} {profile_index}"
        )
        self.session.sendline("quit")
        return status

    def get_mac(self, port) -> list:
        """
        ## Возвращаем список из VLAN и MAC-адреса для данного порта.

        Команда на оборудовании:

            # display mac-address port {i0}/{i1}/{i2}
            # display security bind mac {i0}/{i1}/{i2}

        :param port: Номер порта коммутатора
        :return: ```[ ('vid', 'mac'), ... ]```
        """

        port_type, indexes = self.split_port(port)

        # Для GPON ONT используем отдельный поиск
        if port_type == "gpon" and len(indexes) == 4:
            data = self.ont_port_info(indexes)  # Получаем информацию с порта абонента
            macs = []
            for service in data:
                if service.get("mac"):  # Если есть МАС для сервиса
                    macs.append([service.get("manage_vlan"), service["mac"]])
            return macs

        if len(indexes) != 3:  # Неверный порт
            return []

        # -> display mac-address port
        #   SRV-P BUNDLE TYPE MAC            MAC TYPE F /S /P  VPI  VCI   VLAN ID
        #   INDEX INDEX
        #   ---------------------------------------------------------------------
        #     689    -   adl  9afc-8d4c-1525 dynamic  0 /3 /27 1    33    1418
        #     689    -   adl  e0cc-f85d-3818 dynamic  0 /11/27 1    33    1418
        #     690    -   adl  bc76-706c-c671 dynamic  0 /11/27 1    40    704
        #   ---------------------------------------------------------------------
        macs1 = re.findall(
            rf"\s+\S+\s+\S+\s+\S+\s+({self.mac_format})\s+\S+\s+\d+\s*/\d+\s*/\d+\s+\S+\s+\S+\s+?.+?\s+(\d+)",
            self.send_command(
                f"display mac-address port {'/'.join(indexes)}", num_of_expect=6
            ),
        )

        # Попробуем еще одну команду -> display security bind mac
        #   Index     MAC-Address FlowID  F/ S/ P   VLAN-ID  Vpi  Vci FlowType    FlowPara
        #   ------------------------------------------------------------------------------
        #       0  0002-cf93-db80    879  0 /2 /15      735    1   40        -           -
        #       0  0a31-92f7-1625    582  0 /11/16      707    1   40        -           -
        macs2 = re.findall(
            rf"\s+\S+\s+({self.mac_format})\s+\S+\s+\d+\s*/\d+\s*/\d+\s+(\d+)",
            self.send_command(
                f"display security bind mac {'/'.join(indexes)}", num_of_expect=6
            ),
        )

        res = []
        for m in macs1 + macs2:
            res.append(m[::-1])
        return res

    @staticmethod
    def _up_down_command(port_type: str, status: str) -> str:
        """
        В зависимости от типа порта возвращает команды для управления его статусом
        """

        if port_type in ("scu", "giu", "gpon"):
            if status == "down":
                return "shutdown"
            if status == "up":
                return "undo shutdown"

        if port_type in ("adsl", "ont", "vdsl"):
            if status == "down":
                return "deactivate"
            if status == "up":
                return "activate"

        return ""

    def reload_port(self, port, save_config=True) -> str:
        """
        ## Перезагружает порт

        Переходим в режим конфигурирования:

            # config

        Переходим к интерфейсу:

            (config)# interface {port_type} {i0}/{i1}

        Для xDSL порта или ONT:

            (config-if)# deactivate {i2}
            (config-if)# activate {i2}

        Для GPON, Ethernet порта:

            (config-if)# shutdown {i2}
            (config-if)# undo shutdown {i2}

        Выходим из режима конфигурирования:

            (config-if)# quit
            (config)# quit

        :param port: Порт
        :param save_config: Сохранять конфигурацию?
        :return: Статус выполнения
        """

        port_type, indexes = self.split_port(port)

        if not port_type or len(indexes) not in [3, 4]:
            return f"Неверный порт! ({port})"

        self.session.sendline("config")
        self.session.sendline(f"interface {port_type} {indexes[0]}/{indexes[1]}")
        self.session.expect(self.prompt)

        s = ""
        if port_type == "gpon" and len(indexes) == 4:
            # Перезагрузка ONT
            self.session.sendline(f"ont reset {indexes[2]} {indexes[3]}")
            self.session.expect("Are you sure to reset the ONT")
            self.session.sendline("y")
            self.session.expect(self.prompt)

        else:
            cmd = f"{self._up_down_command(port_type, 'down')} {indexes[2]}"  # Выключить порт
            self.session.sendline(cmd)
            self.session.expect(cmd)
            self.session.sendline("\n")
            sleep(1)  # Пауза

            cmd = f"{self._up_down_command(port_type, 'up')} {indexes[2]}"  # Включить порт
            self.session.sendline(cmd)
            self.session.expect(cmd)

            s = self.session.before.decode()

            self.session.sendline("\n")
            self.session.expect(r"\S+#$")

            s += self.session.before.decode()

        self.session.sendline("quit")
        self.session.sendline("quit")
        return s

    def set_port(self, port, status, save_config=True) -> str:
        """
        ## Перезагружает порт

        Переходим в режим конфигурирования:

            # config

        Переходим к интерфейсу:

            (config)# interface {port_type} {i0}/{i1}

        Для xDSL порта или ONT:

            (config-if)# {deactivate|activate} {i2}

        Для GPON, Ethernet порта:

            (config-if)# {shutdown|undo shutdown} {i2}

        :param port: Порт
        :param status: 'up' или 'down'
        :param save_config: Сохранять конфигурацию?
        :return: Статус выполнения
        """

        port_type, indexes = self.split_port(port)

        if not port_type or len(indexes) not in [3, 4]:
            return f"Неверный порт! ({port})"

        self.session.sendline("config")
        self.session.sendline(f"interface {port_type} {indexes[0]}/{indexes[1]}")
        self.session.expect(self.prompt)

        if port_type == "gpon" and len(indexes) == 4:
            # Для ONT
            s = self.send_command(
                f"ont port {self._up_down_command(port_type, status)} {indexes[2]} {indexes[3]}"
            )
            self.send_command("\n", expect_command=False)

        else:
            # Другие порты
            # Выключаем или включаем порт, в зависимости от типа будут разные команды
            s = self.send_command(
                f"{self._up_down_command(port_type, status)} {indexes[2]}",
                expect_command=False,
            )
            self.send_command("\n", expect_command=False)

        self.session.sendline("quit")

        return s

    def get_interfaces(self) -> list:
        pass

    def get_vlans(self) -> list:
        pass

    def set_description(self, port: str, desc: str) -> str:
        """
        ## Устанавливаем описание для порта предварительно очистив его от лишних символов

        Максимальная длина 32 символа

        Переходим в режим конфигурирования:

            # config

        Если была передана пустая строка для описания, то очищаем с помощью команды:

            (config)# undo port desc {i0}/{i1}/{i2}

        Если **desc** содержит описание, то используем команду для изменения:

            (config)# port desc {i0}/{i1}/{i2} description {desc}

        Выходим из режима конфигурирования:

            (config)# quit

        :param port: Порт, для которого вы хотите установить описание
        :param desc: Описание, которое вы хотите установить для порта
        :return: Вывод команды смены описания
        """

        port_type, indexes = self.split_port(port)
        if not port_type or len(indexes) != 3:
            return f"Неверный порт! ({port})"

        # Очищаем описание от лишних символов
        desc = self.clear_description(desc)

        if len(desc) > 32:
            # Длина описания больше допустимого
            return "Max length:32"

        self.session.sendline("config")

        if desc == "":
            # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            self.session.sendline(
                f"undo port desc {indexes[0]}/{indexes[1]}/{indexes[2]}"
            )

        else:  # В другом случае, меняем описание на оборудовании
            self.session.sendline(
                f"port desc {indexes[0]}/{indexes[1]}/{indexes[2]} description {desc}"
            )

        self.session.sendline("quit")
        self.session.expect(self.prompt)

        return f'Description has been {"changed" if desc else "cleared"}.'

    def get_port_type(self, port: str) -> str:
        return ""

    def get_port_errors(self, port: str) -> str:
        return ""


class HuaweiCX600(BaseDevice):
    """
    # Для оборудования серии CX600 от производителя Huawei
    """

    prompt = r"<\S+>$|\[\S+\]$|Unrecognized command"
    space_prompt = r"  ---- More ----"
    # Регулярное выражение, которое соответствует MAC-адресу.
    mac_format = r"\S\S\S\S-\S\S\S\S-\S\S\S\S"
    vendor = "Huawei"

    def search_mac(self, mac_address: str) -> list:
        """
        ## Возвращаем данные абонента по его MAC адресу

        **MAC необходимо передавать без разделительных символов** он сам преобразуется к виду, требуемому для CX600

        Отправляем на оборудование команду:

            # display access-user mac-address {mac_address}

        Возвращаем список всех IP-адресов, VLAN, связанных с этим MAC-адресом.

        :param mac_address: MAC-адрес
        :return: ```['IP', 'MAC', 'VLAN', 'Agent-Circuit-Id', 'Agent-Remote-Id']```
        """

        formatted_mac = "{}{}{}{}-{}{}{}{}-{}{}{}{}".format(*mac_address)

        match = self.send_command(
            f"display access-user mac-address {formatted_mac}",
            prompt=self.prompt + "|Are you sure to display some information",
            expect_command=False,
        )
        self.session.sendline("N")

        # Форматируем вывод
        with open(
            f"{TEMPLATE_FOLDER}/arp_format/{self.vendor.lower()}-{self.model.lower()}.template",
            encoding="utf-8",
        ) as template_file:
            template = textfsm.TextFSM(template_file)

        formatted_result = template.ParseText(match)
        if formatted_result:
            return formatted_result[0]

        return []

    def search_ip(self, ip_address: str) -> list:
        """
        ## Ищем абонента по его IP адресу

        Отправляем на оборудование команду:

            # display access-user ip-address {ip_address}

        Возвращаем список всех IP-адресов, VLAN, связанных с этим MAC-адресом.

        :param ip_address: IP-адрес
        :return: ```['IP', 'MAC', 'VLAN', 'Agent-Circuit-Id', 'Agent-Remote-Id']```
        """

        match = self.send_command(
            f"display access-user ip-address {ip_address}",
            prompt=self.prompt + "|Are you sure to display some information",
            expect_command=False,
        )
        self.session.sendline("N")

        # Форматируем вывод
        with open(
            f"{TEMPLATE_FOLDER}/arp_format/{self.vendor.lower()}-{self.model.lower()}.template",
            encoding="utf-8",
        ) as template_file:
            template = textfsm.TextFSM(template_file)

        formatted_result = template.ParseText(match)
        if formatted_result:
            return formatted_result[0]

        return []

    def get_interfaces(self) -> list:
        pass

    def get_vlans(self) -> list:
        pass

    def get_mac(self, port: str) -> list:
        pass

    def reload_port(self, port: str, save_config=True) -> str:
        pass

    def set_port(self, port: str, status: str, save_config=True) -> str:
        pass

    def save_config(self):
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
