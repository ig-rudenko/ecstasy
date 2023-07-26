import re
from time import sleep
from typing import Tuple, List
from functools import lru_cache

import pexpect
from django.template.loader import render_to_string

from devicemanager import snmp
from ..base.device import BaseDevice
from ..base.types import (
    T_InterfaceList,
    T_InterfaceVLANList,
    T_MACList,
    T_MACTable,
    T_SplittedPort,
)


class HuaweiMA5600T(BaseDevice):
    """
    # Для DSLAM оборудования MA5600T от производителя Huawei
    """

    prompt = r"config\S+#|\S+#"
    space_prompt = r"---- More \( Press \'Q\' to break \) ----"
    # Регулярное выражение, которое соответствует MAC-адресу.
    mac_format = r"\S\S\S\S-\S\S\S\S-\S\S\S\S"
    vendor = "Huawei"

    def __init__(
        self, session: pexpect, ip: str, auth: dict, model: str = "", snmp_community: str = ""
    ):
        """
        При инициализации активируем режим пользователя командой:

            # enable

        :param session: Это объект сеанса pexpect c установленной сессией оборудования
        :param ip: IP-адрес устройства, к которому вы подключаетесь
        :param auth: словарь, содержащий имя пользователя и пароль для устройства
        :param model: Модель коммутатора
        """

        super().__init__(session, ip, auth, model, snmp_community)
        self.session.sendline("enable")
        self.session.expect(r"\S+#")

        self.adsl_profiles: str = self.get_adsl_profiles()
        self.vdsl_templates: list = self.get_vdsl_templates()
        self.interfaces: T_InterfaceList = []
        self.interfaces_vlans: T_InterfaceVLANList = []

    def get_adsl_profiles(self) -> str:
        return self.send_command(
            "display adsl line-profile\n",
            before_catch="display adsl line-profile",
            expect_command=False,
        )

    def get_vdsl_templates(self) -> list:
        """
        ## Все шаблоны профилей:

            Template  Template
            Index     Name
            ------------------------------
                   1  DEFVAL
                   2  VDSL LINE TEMPLATE 2
                   3  VDSL LINE TEMPLATE 3
                   4  NO_CHANGE
                   5  VDSL
        """

        self.send_command("config")
        templates = sorted(
            re.findall(
                r"\s+(\d+)\s+(.+)",
                self.send_command("display vdsl line-template info", expect_command=False),
            ),
            key=lambda x: int(x[0]),  # Сортируем по убыванию индекса
            reverse=True,
        )
        self.send_command("quit")
        return templates

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
                output += ansi_escape.sub("", self.session.before.decode(errors="ignore"))

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
                    print(f'{self.ip} - timeout во время выполнения команды "{command}"')
                    break

                # Если задано кол-во страниц
                if pages_limit:
                    pages_limit -= 1

        else:  # Если вывод команды выдается полностью, то пропускаем цикл
            try:
                self.session.expect(prompt)
            except pexpect.TIMEOUT:
                pass
            output = re.sub(r"\\x1[bB]\[\d\d\S", "", self.session.before.decode(errors="ignore"))
        return output

    @BaseDevice.lock_session
    def save_config(self):
        pass

    @BaseDevice.lock_session
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

    @lru_cache()
    def get_boards(self, board_index):
        """
        ## Смотрим слоты на плате:

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

        :param board_index: Индекс доски, которую вы хотите получить
        """
        return self.send_command(f"display board {board_index}")

    @lru_cache()
    def split_port(self, port: str) -> T_SplittedPort:
        """
        ## Разделяет строку порта на тип интерфейса и плата, слот, порт

        >>> self.split_port("ADSL 0/2/4")
        ('adsl', ('0', '2', '4'))

        >>> self.split_port("GPON 0/6/7/1")
        ('gpon', ('0', '6', '7', '1'))

        >>> self.split_port("ethernet0/9/1")
        ('eth', ('0', '9', '1'))

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
            board_info = self.get_boards(indexes[0])

            board_list = self.find_or_empty(rf"\s+({indexes[1]})\s+(\S+)\s+\S+", board_info)
            if board_list:
                if "SCU" in board_list[1]:
                    return "scu", tuple(indexes)
                if "GI" in board_list[1]:
                    return "giu", tuple(indexes)

            return "eth", tuple(indexes)

        return port_type, tuple(indexes)

    def _render_adsl_port_info(
        self, port: str, info: str, profile_name: str, all_profiles: list
    ) -> dict:
        """
        ## Преобразовываем информацию о ADSL порте для отображения на странице

        ```[ ('name', 'status', 'desc'), ... ]```
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

        return {
            "type": "adsl",
            "data": {
                "profile_name": profile_name,
                "port": port,
                "first_col": first_col_info,
                "streams": table_dict,
                "profiles": all_profiles,
            },
        }

    def _render_gpon_port_info(self, indexes: Tuple[str, ...]) -> dict:
        """
        ## Преобразовываем информацию о GPON порте для отображения на странице
        """

        # Проверяем индексы
        if not isinstance(indexes, tuple) or len(indexes) not in [3, 4]:
            return {
                "type": "error",
                "data": f'Неверный порт! (GPON {"/".join(indexes)})',
            }

        self.send_command("config")  # Переходим в режим конфигурации
        i: tuple = indexes  # Упрощаем запись переменной

        # GPON
        if len(indexes) == 3:
            # Смотрим порт
            output = self.send_command(
                f'display ont info summary {"/".join(i)}',
                before_catch="Please wait",
                expect_command=False,
            )
            self.send_command("quit")

            data = {
                "total_count": self.find_or_empty(
                    r"the total of ONTs are: (\d+), online: \d+", output
                ),
                "online_count": self.find_or_empty(
                    r"the total of ONTs are: \d+, online: (\d+)", output
                ),
            }

            lines = re.findall(
                r"(\d+)\s+(online|offline)\s+(\d*-?\d*-?\d* ?\d*:?\d*:?\d*)\s+(\d*-?\d*-?\d* ?\d*:?\d*:?\d*)\s+(\S+)",
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

                data["onts_lines"].append(part1 + part2)

            return {
                "type": "gpon",
                "data": data,
            }

        # Смотрим ONT
        data = self._ont_port_info(indexes=i)
        self.send_command("quit")
        return {
            "type": "html",
            "data": render_to_string("check/ont_port_info.html", {"ont_info": data}),
        }

    @lru_cache()
    def _ont_port_info(self, indexes: tuple) -> list:
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
        parts = info.split("---------------------------------------------------------------")

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
                    "ipv4_address": self.find_or_empty(r"IPv4 address\s+: (\S+)", service_part),
                    "subnet_mask": self.find_or_empty(r"Subnet mask\s+: (\S+)", service_part),
                    "manage_vlan": self.find_or_empty(r"Manage VLAN\s+: (\d+)", service_part),
                    "mac": self.find_or_empty(
                        r"MAC address\s+: ([0-9A-F]+-[0-9A-F]+-[0-9A-F]+)", service_part
                    ),
                }
            )

        return data

    def _render_vdsl_port_info(self, info: str, profile_name: str, all_profiles: list) -> dict:
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
            color_code = ""
            """Определяем цвета в зависимости от числовых значений показателя"""
            if "SNR margin" in s:
                gradient = [5, 7, 10, 20]
            elif "attenuation" in s:
                gradient = [-60, -50, -40, -20]
                val = -val
            elif "output power" in s:
                return "#95e522" if val >= 10 else "#e5a522"
            else:
                return color_code
            # проверяем значения по градиенту
            if val <= gradient[0]:
                color_code = "#e55d22"
            elif val <= gradient[1]:
                color_code = "#e5a522"
            elif val <= gradient[2]:
                color_code = "#dde522"
            elif val <= gradient[3]:
                color_code = "#95e522"
            else:
                color_code = "#22e536"

            return color_code

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

        return {
            "type": "adsl",
            "data": {
                "profile_name": profile_name,
                "first_col": [],
                "streams": up_down_streams,
                "profiles": all_profiles,
            },
        }

    def _vdsl_port_info(self, indexes: tuple) -> dict:
        """
        ## Смотрим информацию на VDSL порту
        """

        self.send_command("config")
        self.send_command(f"interface vdsl {indexes[0]}/{indexes[1]}", expect_command=False)

        port_stats = self.send_command(f"display line operation {indexes[2]}", expect_command=False)

        # Индекс текущего шаблона
        current_line_template_index = self.find_or_empty(
            r"\s\d+\s+\S+\s+\S+\s+(\d+)",
            self.send_command(f"display port state {indexes[2]}", expect_command=False),
        )

        template_name = ""
        # Ищем имя текущего шаблона
        for line in self.vdsl_templates:
            if line[0] == current_line_template_index:
                template_name = line[1]

        self.send_command("quit")
        self.send_command("quit")

        return self._render_vdsl_port_info(port_stats, template_name, self.vdsl_templates)

    @BaseDevice.lock_session
    def get_port_info(self, port: str) -> dict:
        """
        ## Смотрим информацию на порту

        В зависимости от порта вывод различается

        :param port: Порт
        :return: Информация о порте либо ```"Неверный порт!"```
        """

        port_type, indexes = self.split_port(port)

        # Для GPON используем отдельный метод
        if port_type == "gpon":
            return self._render_gpon_port_info(indexes=indexes)

        # Для других
        if not port_type or len(indexes) != 3:
            return {
                "type": "error",
                "text": f"Неверный порт! ({port})",
            }

        # Для VDSL используем отдельный метод
        if port_type == "vdsl":
            return self._vdsl_port_info(indexes=indexes)

        self.send_command("config")
        self.send_command(f"interface {port_type} {indexes[0]}/{indexes[1]}", expect_command=False)

        self.session.sendline(f"display line operation {indexes[2]}")
        if self.session.expect([r"Are you sure to continue", "Unknown command"]):
            return {
                "type": "error",
                "text": "Unknown command",
            }

        output = self.send_command("y", expect_command=True, before_catch=r"Failure|------[-]+")

        profile_output = self.send_command(f"display port state {indexes[2]}")
        profile_index = self.find_or_empty(r"\s+\d+\s+\S+\s+(\d+)", profile_output)
        profile_output = self.send_command(f"display adsl line-profile {profile_index}")

        self.session.sendline("quit")
        self.session.sendline("quit")
        self.session.expect(r"\S+#")

        profile_name = self.find_or_empty(r"Name:\s+(.+)[\r\n]", profile_output).strip()

        # Парсим профиля
        res = re.findall(
            r"(\d+)\s+(.+?)\s+\S+\s+\S+\s+\d+\s+\d+\s+(\d+)\s+(\d+)([\s\S]*?)(?= \d+ \S+[ ]+\S+| [-])",
            self.adsl_profiles,
        )

        profiles = []
        for line in res:
            profiles.append([line[0], line[1] + " ".join(line[-1].split())])

        return self._render_adsl_port_info(port, output, profile_name, profiles)

    @BaseDevice.lock_session
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

        self.send_command("config")
        self.send_command(f"interface {port_type} {indexes[0]}/{indexes[1]}", expect_command=False)

        self.send_command(f"deactivate {indexes[2]}")
        status = self.send_command(f"activate {indexes[2]} {change_profile_cmd} {profile_index}")
        self.send_command("quit")
        return status

    def normalize_interface_name(self, intf: str) -> str:
        """
        ## Нормализовать имя интерфейса до стандартного формата.

        >>> self.normalize_interface_name("ADSL 0/2/4")
        'adsl0/2/4'

        >>> self.normalize_interface_name("ethernet 0/2/4")
        'eth0/2/4'

        :param intf: Имя интерфейса для нормализации
        """
        port = self.split_port(intf)
        return port[0] + "/".join(port[1])

    def get_mac_table(self) -> T_MACTable:
        """
        ## Возвращает таблицу MAC-адресов оборудования.

        Для работы требуются раннее найденные интерфейсы, указанные в атрибуте `interfaces`

        :return: ```[ ({int:vid}, '{mac}', 'dynamic', '{port}'), ... ]```
        """

        mac_table: T_MACTable = []

        for interface in self.interfaces:
            port_macs = self.get_mac(interface[0])
            mac_table += [(int(vid), mac, "dynamic", interface[0]) for vid, mac in port_macs]
        return mac_table

    @BaseDevice.lock_session
    def get_mac(self, port) -> T_MACList:
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
            data = self._ont_port_info(indexes)  # Получаем информацию с порта абонента
            macs = []
            for service in data:
                if service.get("mac"):  # Если есть МАС для сервиса
                    macs.append((service.get("manage_vlan"), service["mac"]))
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
        macs1: List[Tuple[str, str]] = re.findall(
            rf"\s+\S+\s+\S+\s+\S+\s+({self.mac_format})\s+\S+\s+\d+\s*/\d+\s*/\d+\s+\S+\s+\S+\s+?.+?\s+(\d+)",
            self.send_command(f"display mac-address port {'/'.join(indexes)}", num_of_expect=6),
        )

        # Попробуем еще одну команду -> display security bind mac
        #   Index     MAC-Address FlowID  F/ S/ P   VLAN-ID  Vpi  Vci FlowType    FlowPara
        #   ------------------------------------------------------------------------------
        #       0  0002-cf93-db80    879  0 /2 /15      735    1   40        -           -
        #       0  0a31-92f7-1625    582  0 /11/16      707    1   40        -           -
        macs2: List[Tuple[str, str]] = re.findall(
            rf"\s+\S+\s+({self.mac_format})\s+\S+\s+\d+\s*/\d+\s*/\d+\s+(\d+)",
            self.send_command(f"display security bind mac {'/'.join(indexes)}", num_of_expect=6),
        )

        res: T_MACList = []
        for mac, vid in macs1 + macs2:
            res.append((int(vid), mac))
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

    @BaseDevice.lock_session
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

        self.send_command("config")
        self.send_command(f"interface {port_type} {indexes[0]}/{indexes[1]}", expect_command=False)

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
            self.session.expect(self.prompt)

            s += self.session.before.decode()

        self.send_command("quit")
        self.send_command("quit")
        return s

    @BaseDevice.lock_session
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

        self.send_command("config")
        self.send_command(f"interface {port_type} {indexes[0]}/{indexes[1]}", expect_command=False)

        if port_type == "gpon" and len(indexes) == 4:
            # Для ONT
            self.session.sendline(
                f"ont port {self._up_down_command(port_type, status)} {indexes[2]} {indexes[3]}"
            )
            self.send_command("\n", expect_command=False)
            s = f"ont port {self._up_down_command(port_type, status)} {indexes[2]} {indexes[3]}"

        else:
            # Другие порты
            # Выключаем или включаем порт, в зависимости от типа будут разные команды
            self.session.sendline(f"{self._up_down_command(port_type, status)} {indexes[2]}")
            self.send_command("\n", expect_command=False)
            s = f"{self._up_down_command(port_type, status)} {indexes[2]}"

        self.session.sendline("quit")

        return s

    @BaseDevice.lock_session
    def get_interfaces(self) -> T_InterfaceList:
        return snmp.get_interfaces(device_ip=self.ip, community=self.snmp_community)

    @BaseDevice.lock_session
    def get_vlans(self) -> T_InterfaceVLANList:
        return []

    @BaseDevice.lock_session
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

        self.send_command("config")

        if desc == "":
            # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            self.send_command(
                f"undo port desc {indexes[0]}/{indexes[1]}/{indexes[2]}",
                expect_command=False,
            )

        else:  # В другом случае, меняем описание на оборудовании
            self.send_command(
                f"port desc {indexes[0]}/{indexes[1]}/{indexes[2]} description {desc}",
                expect_command=False,
            )

        self.send_command("quit")

        return f'Description has been {"changed" if desc else "cleared"}.'

    @BaseDevice.lock_session
    def get_port_type(self, port: str) -> str:
        return ""

    @BaseDevice.lock_session
    def get_port_errors(self, port: str) -> str:
        return ""

    def get_device_info(self) -> dict:
        return {}
