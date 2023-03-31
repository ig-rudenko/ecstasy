import re
from functools import wraps
from time import sleep
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
)


class Dlink(BaseDevice):
    """
    Для оборудования от производителя D-Link

    Проверено для:
     - DES-1228
     - DES-3028
     - DES-3200
     - DES-3526
     - DGS-1210
     - DGS-3420

    """

    prompt = r"\S+#"
    space_prompt = None
    mac_format = r"\S\S-" * 5 + r"\S\S"
    vendor = "D-Link"

    def __init__(self, session: pexpect, ip: str, auth: dict, model: str = ""):
        """
        При инициализации повышаем уровень привилегий до уровня администратора командой:

            # enable admin

        Отключаем постраничный вывод командой:

            # disable clipaging

        Дополнительно смотрим характеристики устройства:

            # show switch

          - MAC
          - модель
          - серийный номер

        :param session: Это объект сеанса pexpect c установленной сессией оборудования
        :param ip: IP-адрес устройства, к которому вы подключаетесь
        :param auth: словарь, содержащий имя пользователя и пароль для устройства
        :param model: Модель коммутатора
        """
        super().__init__(session, ip, auth, model)

        status = True
        # Повышает уровень привилегий до уровня администратора
        self.session.sendline("enable admin")

        if not session.expect(["[Pp]ass", r"You already have"]):
            # 0 - ввод пароля  # 1 - уже администратор
            # Вводим пароль администратора
            self.session.sendline(self.auth["privilege_mode_password"])

        # Проверка prompt или строки "Fail!"
        while self.session.expect([self.prompt, "Fail!"]):
            self.session.sendline("\n")
            print(self.ip, "privilege_mode_password wrong!")
            status = False
        if status:
            # отключение режима постраничного вывода
            self.session.sendline("disable clipaging")
            self.session.expect(self.prompt)

        # Уровень администратора
        self._admin_status: bool = status

        # Смотрим характеристики устройства
        version = self.send_command("show switch")
        self.mac = self.find_or_empty(
            r"MAC Address\s+:\s+(\S+-\S+-\S+-\S+-\S+-\S+)", version
        )
        self.model = self.model or self.find_or_empty(
            r"Device Type\s+:\s+(\S+)\s", version
        )
        self.serialno = self.find_or_empty(r"Serial Number\s+:\s+(\S+)", version)

    def _validate_port(self=None, if_invalid_return=None):
        """
        ## Декоратор для проверки правильности порта Cisco

        :param if_invalid_return: что нужно вернуть, если порт неверный
        """

        if if_invalid_return is None:
            if_invalid_return = "Неверный порт"

        def validate(func):
            @wraps(func)
            def __wrapper(self, port, *args, **kwargs):
                port = Dlink.validate_port(port)
                if port is None:
                    # Неверный порт
                    return if_invalid_return

                # Вызываем метод
                return func(self, port, *args, **kwargs)

            return __wrapper

        return validate

    @staticmethod
    def validate_port(port: str) -> (str, None):
        """
        Проверяем порт на валидность

        >>> Dlink.validate_port("1/2")
        '2'
        >>> Dlink.validate_port("23")
        '23'
        >>> Dlink.validate_port("26(C)")
        '26'
        >>> Dlink.validate_port("уфы(C)")
        None
        """

        port = port.strip()
        if re.findall(r"^\d/\d+$", port):
            # Если порт представлен в виде "1/2"
            port = re.sub(r"^\d/", "", port)  # Оставляем только "2"
        elif re.findall(r"^\d+$|^\d+\s*\([FC]\)$", port):
            port = re.sub(r"\D", "", port)
        else:
            port = ""
        if port.isdigit():
            return port

        return None

    @BaseDevice._lock
    def save_config(self):
        """
        Сохраняем конфигурацию оборудования командой:

            # save

        Ожидаем ответа от оборудования **Success** или **Done**,
        если нет, то ошибка сохранения
        """
        self.session.sendline("save")
        if self.session.expect([self.prompt, r"[Ss]uccess|[Dd]one"]):
            self.session.expect(self.prompt)
            return self.SAVED_OK
        return self.SAVED_ERR

    def send_command(
        self,
        command: str,
        before_catch: str = None,
        expect_command=False,
        num_of_expect=10,
        space_prompt=None,
        prompt=None,
        pages_limit=None,
        command_linesep="\n",
    ):
        return super().send_command(
            command,
            before_catch=before_catch or command,
            expect_command=expect_command,
            num_of_expect=num_of_expect,
            space_prompt=space_prompt,
            prompt=prompt,
            pages_limit=pages_limit,
            command_linesep=command_linesep,
        )

    @BaseDevice._lock
    def get_interfaces(self) -> T_InterfaceList:
        """
        Эта функция возвращает список всех интерфейсов на устройстве

        Команда на оборудовании:

            # show ports description

        :return: ```[ ('name', 'status', 'desc'), ... ]```
        """

        output = self.send_command("show ports des")

        with open(
            f"{TEMPLATE_FOLDER}/interfaces/d-link.template", "r", encoding="utf-8"
        ) as template_file:
            # Используем библиотеку TextFSM для анализа вывода команды show.
            int_des_ = textfsm.TextFSM(template_file)
            # Разбираем вывод команды «show ports description» и ищем интерфейсы.
            result = int_des_.ParseText(output)
        return [
            (
                line[0],  # interface
                re.sub(r"Link\s*?Down", "down", line[2])
                if "Enabled" in line[1]
                else "admin down",  # status
                line[3],  # desc
            )
            for line in result
        ]

    @BaseDevice._lock
    def get_vlans(self) -> T_InterfaceVLANList:
        """
        Эта функция возвращает список всех интерфейсов и его VLAN на коммутаторе.

        Смотрим список всех VLAN командой:

            # show vlan

        Вывод каждого VLAN представляет собой следующее
        Парсим полученные данные и находим соответствие между VLAN и портами

        |                             |                             |
        |:----------------------------|:----------------------------|
        | VID             : 21        |  VLAN Name       : 21       |
        | VLAN Type       : Static    |  Advertisement   : Disabled |
        | Member Ports    : 21,25-28  |                             |
        | Static Ports    : 21,25-28  |                             |

        :return: ```[ ('name', 'status', 'desc', [vid:int, vid:int, ...]), ... ]```
        """
        self.lock = False
        interfaces = self.get_interfaces()
        self.lock = True

        output = self.send_command("show vlan")
        with open(
            f"{TEMPLATE_FOLDER}/vlans_templates/d-link.template", "r", encoding="utf-8"
        ) as template_file:
            vlan_templ = textfsm.TextFSM(template_file)
            result_vlan = vlan_templ.ParseText(output)
        # сортируем и выбираем уникальные номера портов из списка интерфейсов
        port_num = set(sorted([int(re.findall(r"\d+", p[0])[0]) for p in interfaces]))

        # Создаем словарь, где ключи это кол-во портов, а значениями будут вланы на них
        ports_vlan = {str(num): [] for num in range(1, len(port_num) + 1)}

        for vlan in result_vlan:
            # Преобразуем диапазон VLAN в список чисел.
            for port in range_to_numbers(vlan[2]):
                # Добавляем вланы на порты
                ports_vlan[str(port)].append(vlan[0])
        interfaces_vlan = []  # итоговый список (интерфейсы и вланы)
        for line in interfaces:
            interfaces_vlan.append(
                (
                    line[0],
                    line[1],
                    line[2],
                    ports_vlan.get(re.sub(r"\D", "", line[0]), []),
                )
            )
        return interfaces_vlan

    @staticmethod
    def normalize_interface_name(intf: str) -> str:
        """
        ## Интерфейс должен быть числом, поэтому удаляем все остальные символы
        """
        return re.sub(r"\D", "", intf)

    @BaseDevice._lock
    def get_mac_table(self) -> T_MACTable:
        """
        ## Возвращаем список из VLAN, MAC-адреса, тип и порт для данного оборудования.

        Команда на оборудовании:

            # show fdb

        :return: ```[ ({int:vid}, '{mac}', {'static'|'dynamic'|'security'}, '{port}'), ... ]```
        """

        def format_type(type_: str) -> str:
            if type_ == "DeleteOnTimeout":
                return "security"
            return type_.lower()

        mac_str = self.send_command(f"show fdb", expect_command=False)
        mac_table = re.findall(
            rf"(\d+)\s+\S+\s+({self.mac_format})\s+(\d+)\s+(\S+).*\n",
            mac_str,
            flags=re.IGNORECASE,
        )
        return [
            (int(vid), mac, format_type(type_), port)
            for vid, mac, port, type_ in mac_table
        ]

    @BaseDevice._lock
    @_validate_port(if_invalid_return=[])
    def get_mac(self, port) -> T_MACList:
        """
        Эта функция возвращает список из VLAN и MAC-адреса для данного порта.

        Команда на оборудовании:

            # show fdb port {port}

        :param port: Номер порта коммутатора
        :return: ```[ ('vid', 'mac'), ... ]```
        """

        mac_str = self.send_command(f"show fdb port {port}", expect_command=False)
        # Используем регулярное выражение для поиска всех MAC-адресов и VLAN в mac_str.
        return re.findall(rf"(\d+)\s+\S+\s+({self.mac_format})\s+\d+\s+\S+", mac_str)

    @BaseDevice._lock
    def reload_port(self, port, save_config=True) -> str:
        """
        Перезагружает порт

        Если порт передается с пометкой **C** или **F**
        Например ```25(F)```, ```26(C)```, то перезагружаем указанный medium_type

        Для порта с номером больше 23, если не был передан medium_type,
        то перезагружаем и **copper**, и **fiber**

            # config ports {port} medium_type {copper|fiber} state disable
            # config ports {port} medium_type {copper|fiber} state enable

        Для других портов не используется medium_type

            # config ports {port} state disable
            # config ports {port} state enable


        :param port: Порт для перезагрузки
        :param save_config: Если True, конфигурация будет сохранена на устройстве, defaults to True (optional)
        :return: Результат введенных команд и, если было указано, то статус сохранения конфигурации
        """

        if "F" in port:
            media_type = " medium_type fiber"
        elif "C" in port:
            media_type = " medium_type copper"
        else:
            media_type = ""

        port = self.validate_port(port)
        if port is None:
            return "Неверный порт"

        # Отключение порта.
        r1 = self.send_command(f"config ports {port}{media_type} state disable")
        # Проверка, не установлен ли тип порта и порт больше 23
        if not media_type and int(port) > 23:
            r1 += self.send_command(
                f"config ports {port} medium_type fiber state disable"
            )

        # Задержка, позволяющая коммутатору обработать команду.
        sleep(4)

        # Включение порта.
        r2 = self.send_command(f"config ports {port}{media_type} state enable")
        # Проверка, не установлен ли тип порта и порт больше 23
        if not media_type and int(port) > 23:
            r2 += self.send_command(
                f"config ports {port} medium_type fiber state enable"
            )

        self.lock = False
        # Сохранение конфигурации, если для параметра `save_config` установлено значение `True`.
        s = self.save_config() if save_config else "Without saving"
        return r1 + r2 + s

    @BaseDevice._lock
    def set_port(self, port, status, save_config=True) -> str:
        """
        Устанавливает статус порта на коммутаторе **up** или **down**

        Если порт передается с пометкой **C** или **F**
        Например ```25(F)```, ```26(C)```, то используем указанный medium_type

        Для порта с номером больше 23, если не был передан medium_type,
        то используем и **copper**, и **fiber**

            # config ports {port} medium_type {copper|fiber} state {disable|enable}

        Для других портов не используется medium_type

            # config ports {port} state {disable|enable}

        :param port: Порт
        :param status: "up" или "down"
        :param save_config: Если True, конфигурация будет сохранена на устройстве, defaults to True (optional)
        """

        if "F" in port:
            media_type = " medium_type fiber"
        elif "C" in port:
            media_type = " medium_type copper"
        else:
            media_type = ""

        # Проверка правильности порта.
        port = self.validate_port(port)

        if port is None:
            return "Неверный порт"

        if status == "up":
            state = "enable"
        elif status == "down":
            state = "disable"
        else:
            state = ""

        # Установка порта в заданное состояние.
        r = self.send_command(f"config ports {port}{media_type} state {state}")

        # Проверка, не установлен ли тип порта и порт больше 23
        if not media_type and int(port) > 23:
            # Проверка, является ли порт оптоволоконным портом, и если это так,
            # он установит порт в состояние, которое было передано.
            r += self.send_command(
                f"config ports {port} medium_type fiber state {state}"
            )

        self.lock = False
        s = self.save_config() if save_config else "Without saving"

        # Возврат результата команды и результата функции save_config().
        return r + s

    @BaseDevice._lock
    @_validate_port()
    def get_port_errors(self, port: str) -> str:
        """
        Получаем ошибки на порту через команду:

            # show error ports {port}

        :param port: Порт для проверки на наличие ошибок
        """

        self.session.sendline(f"show error ports {port}")

        # Если не удалось отключить clipaging
        if self.session.expect([self.prompt, "Previous Page"]):
            self.session.sendline("q")

        return self.session.before.decode()

    @BaseDevice._lock
    def set_description(self, port: str, desc: str) -> str:
        """
        Устанавливаем описание для порта предварительно очистив его от лишних символов

        Если была передана пустая строка для описания, то очищаем с помощью команды:

            # config ports {port} clear_description

        Если **desc** содержит описание, то используем команду для изменения

            # config ports {port} description {desc}

        Если длина описания больше чем разрешено на оборудовании, то выводим ```"Max length:{number}"```

        :param port: Порт, для которого вы хотите установить описание
        :param desc: Описание, которое вы хотите установить для порта
        :return: Вывод команды смены описания
        """

        if "F" in port:
            media_type = " medium_type fiber"
        elif "C" in port:
            media_type = " medium_type copper"
        else:
            media_type = ""

        port = self.validate_port(port)
        if port is None:
            return "Неверный порт"

        desc = self.clear_description(desc)  # Очищаем описание от лишних символов

        if desc == "":
            # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            status = self.send_command(
                f"config ports {port}{media_type} clear_description",
                expect_command=False,
                before_catch="desc",
            )

        else:  # В другом случае, меняем описание на оборудовании
            status = self.send_command(
                f"config ports {port}{media_type} description {desc}",
                expect_command=False,
                before_catch="desc",
            )

        self.lock = False

        if "Next possible completions" in status:
            # Если длина описания больше чем разрешено на оборудовании
            return "Max length:" + self.find_or_empty(r"<desc (\d+)>", status)

        if "Success" in status:  # Успешно поменяли описание
            # Возвращаем строку с результатом работы и сохраняем конфигурацию
            return f'Description has been {"changed" if desc else "cleared"}. {self.save_config()}'

        # Уникальный случай
        return status

    @BaseDevice._lock
    @_validate_port(if_invalid_return={})
    def virtual_cable_test(self, port: str) -> dict:
        """
        Эта функция запускает диагностику состояния линии на порту оборудования через команду:

            # cable_diag ports {port}

        Функция возвращает данные в виде словаря.
        В зависимости от результата диагностики некоторые ключи могут отсутствовать за ненадобностью.

        ```python
        {
            "len": "-",         # Длина кабеля в метрах, либо "-", когда не определено
            "status": "",       # Состояние на порту (Up, Down, Empty)
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

        diag_output = self.send_command(
            f"cable_diag ports {port}", expect_command=False
        )

        if "Available commands" in diag_output:
            return {}

        result = {
            "len": "-",  # Length
            "status": "",  # Up, Down
        }

        if "can't support" in diag_output or "Unknown" in diag_output:
            result["status"] = "Don't support Cable Diagnostic"
            return result

        if "No Cable" in diag_output:
            # Нет кабеля
            result["status"] = "Empty"
            return result

        if re.findall(r"Link (Up|Down)\s+OK", diag_output):
            # Если статус OK
            match = self.find_or_empty(
                r"\s+\d+\s+\S+\s+Link (Up|Down)\s+OK\s+(\S+)", diag_output
            )
            if len(match) == 2:
                result["len"] = match[1]  # Длина
                result["status"] = match[0]  # Up или Down
        else:
            # C ошибкой
            result["status"] = (
                self.find_or_empty(r"\s+\d+\s+\S+\s+Link (Up|Down)", diag_output)
                or "None"
            )
            # Смотрим по очереди 4 пары
            for i in range(1, 5):
                # Нахождение пары по номеру `i`.
                pair_n = self.find_or_empty(
                    rf"Pair\s*{i} (\S+)\s+at\s+(\d+)", diag_output
                )
                # Проверка, не является ли пара пустой.
                if pair_n:
                    # Создаем пустой словарь для пары
                    result[f"pair{i}"] = {}
                    result[f"pair{i}"]["status"] = pair_n[0].lower()  # Open, Short
                    result[f"pair{i}"]["len"] = pair_n[1]  # Длина

        return result

    @BaseDevice._lock
    def get_device_info(self) -> dict:
        stats = ["cpu", "ram", "flash"]
        data = {}

        for key in stats:
            value = getattr(self, f"get_{key}_utilization")()
            if isinstance(value, tuple) and all(value) or value > 0:
                data[key] = {"util": value}

        return data

    def _get_utilization(self, type_: str, expect: str):
        self.session.sendline("show utilization " + type_)
        self.session.sendcontrol("c")
        self.session.expect(self.prompt)
        output = self.session.before.decode("utf-8", errors="ignore")

        cpu_percent = self.find_or_empty(
            expect,
            output,
            flags=re.IGNORECASE,
        )
        return int(cpu_percent) if cpu_percent else -1

    def get_cpu_utilization(self) -> tuple:
        """
        ## Возвращает загрузку ЦП хоста
        """
        return (self._get_utilization("cpu", r"one minute -\s+(\d+)\s*%"),)

    def get_flash_utilization(self) -> int:
        """
        ## Возвращает использование флэш-памяти устройства
        """
        return self._get_utilization("flash", r"Utilization\s+: (\d+)\s*%")

    def get_ram_utilization(self) -> int:
        """
        ## Возвращает использование DRAM в процентах
        """
        return self._get_utilization("dram", r"Utilization\s+: (\d+)\s*%")

    def get_port_info(self, port: str) -> dict:
        return {"type": "text", "data": ""}

    def get_port_type(self, port: str) -> str:
        return ""

    def get_port_config(self, port: str) -> str:
        return ""

    @BaseDevice._lock
    def get_current_configuration(self, *args, **kwargs) -> str:
        config = self.send_command(
            "show config current_config",
            expect_command=False,
            before_catch="Command: show config current_config",
        )
        return re.sub("[\r\n]{3}", "\n", config.strip())
