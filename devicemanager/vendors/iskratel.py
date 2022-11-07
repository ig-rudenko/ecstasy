import re
from time import sleep
from django.template.loader import render_to_string
from .base import BaseDevice


class IskratelControl(BaseDevice):
    """
    Для плат управления DSLAM от производителя Iskratel
    """

    prompt = r"\(\S+\)\s*#"
    space_prompt = r"--More-- or \(q\)uit"
    mac_format = r"\S\S:" * 5 + r"\S\S"
    vendor = "Iskratel"

    def save_config(self):
        pass

    def get_mac(self, port) -> list:
        """
        Смотрим MAC'и на порту и отдаем в виде списка

        [ ["vlan", "mac"],  ... ]
        """

        if not re.findall(r"\d+/\d+", port):  # Неверный порт
            return []

        output = self.send_command(f"show mac-addr-table interface {port}")
        macs = re.findall(rf"({self.mac_format})\s+(\d+)", output)

        res = []
        for m in macs:
            res.append(m[::-1])
        return res

    def get_interfaces(self) -> list:
        pass

    def get_vlans(self) -> list:
        pass

    def reload_port(self, port, save_config=True) -> str:
        pass

    def set_port(self, port: str, status: str, save_config=True) -> str:
        pass

    def set_description(self, port: str, desc: str) -> str:
        pass


class IskratelMBan(BaseDevice):
    """
    Для плат DSLAM от производителя Iskratel

    Проверено для:
     - MPC8560
    """

    prompt = r"mBAN>\s"
    space_prompt = r"Press any key to continue or Esc to stop scrolling\."
    mac_format = r"\S\S:" * 5 + r"\S\S"
    vendor = "Iskratel"

    def save_config(self):
        pass

    @property
    def get_service_ports(self):
        """Сервисные порты для DSLAM"""
        return ["1_32", "1_33", "1_40"]

    def __dsl_port_info_parser(self, info: str) -> str:
        """
        Парсит информацию о порте DSL и создает таблицу html для представления показателей сигнал/шума, затухания,
        мощности и прочей информации
        """

        def color(val: str, s: str) -> str:
            if not val:
                return ""
            val = float(val)

            # Определяем цвета в зависимости от числовых значений показателя
            if "Сигнал/Шум" in s:
                gradient = [5, 7, 10, 20]
            elif "Затухание линии" in s:
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

        # mBAN> show dsl profile
        # ADSL profiles:
        #  Id   Name
        # ------------------------------------
        #  20   160/160
        #  10   160/320
        #  ...
        all_profiles = sorted(
            re.findall(
                r"(\d+)\s+(.+)",
                self.send_command(
                    "show dsl profile",
                    expect_command=False,
                    before_catch=r"ADSL profiles",
                ),
            ),
            key=lambda pr: int(pr[0]),
            reverse=True,
        )

        first_col_info = []
        oper_state = self.find_or_empty(r"Operational State\s+(\S+)\/", info)
        if self.find_or_empty(r"Equipment\s+Unequipped", info):
            first_col_info.append("Порт - ADMIN DOWN")
        elif oper_state == "Down":
            first_col_info.append("Порт - DOWN")
        elif oper_state == "Up":
            first_col_info.append("Порт - UP")

        first_col_info.append(self.find_or_empty(r"Type .*", info))

        # Данные для таблицы
        data_rate = re.findall(
            r"DS Data Rate AS0\s+(\d+) kbit/s\s+US Data Rate LS0\s+(\d+) kbit", info
        ) or [("", "")]
        max_rate = [
            (
                self.find_or_empty(
                    r"Maximum DS attainable aggregate rate\s+(\d+) kbit", info
                ),
                self.find_or_empty(
                    r"Maximum US attainable aggregate rate\s+(\d+) kbit", info
                ),
            )
        ]

        snr = re.findall(r"DS SNR Margin\s+(\d+) dB\s+US SNR Margin\s+(\d+)", info) or [
            ("", "")
        ]
        intl = re.findall(
            r"DS interleaved delay\s+(\d+) ms\s+US interleaved delay\s+(\d+)", info
        ) or [("", "")]
        att = re.findall(
            r"DS Attenuation\s+(\d+) dB\s+US Attenuation\s+(\d+)", info
        ) or [("", "")]

        names = [
            "Фактическая скорость передачи данных (Кбит/с)",
            "Максимальная скорость передачи данных (Кбит/с)",
            "Сигнал/Шум (дБ)",
            "Interleaved channel delay (ms)",
            "Затухание линии (дБ)",
        ]

        # Создаем список из элементов:
        # {
        #   'name': 'Фактическая скорость передачи данных (Кбит/с)',
        #   'down': {'color': 'red', 'value': 34.1},
        #   'up': {'color': 'red', 'value': 34.1}
        # }, ...
        table_dict = [
            {
                "name": line[0],
                "down": {"color": color(line[1][0], line[0]), "value": line[1][0]},
                "up": {"color": color(line[1][1], line[0]), "value": line[1][1]},
            }
            for line in zip(names, data_rate + max_rate + snr + intl + att)
        ]

        return render_to_string(
            "check/adsl-port-info.html",
            {
                "profile_name": self.find_or_empty(r"Profile Name\s+(\S+)", info),
                "first_col": first_col_info,
                "streams": table_dict,
                "profiles": all_profiles,
            },
        )

    def get_port_info(self, port: str) -> str:
        """Смотрим информацию на порту"""

        port_type, port = self.validate_port(port)
        if port_type is None:
            return "Invalid port"

        if port_type == "fasteth":
            cmd = f"show interface fasteth{port}"
            before_catch = r"\[Enabled Connected Bridging\]"

        else:  # Если указан физический adsl порт
            cmd = f"show dsl port {port} detail"
            before_catch = None

        output = self.send_command(cmd, expect_command=False, before_catch=before_catch)

        if port_type == "fasteth":  # Возвращаем первые 4 строки
            # Requested Speed  : Auto
            # Requested Duplex : Auto
            # Actual Speed     : 1000 Mbit/s
            # Actual Duplex    : Full
            return "<br>".join(output.split("\n")[1:5])

        # Парсим данные
        return self.__dsl_port_info_parser(output)

    def get_mac(self, port: str) -> list:
        """
        Смотрим MAC'и на порту и отдаем в виде списка

        [ ["vlan", "mac"],  ... ]
        """

        macs = []  # Итоговый список маков

        port_type, port = self.validate_port(port)
        if port_type is None:
            return []

        # Для fasteth портов
        if port_type == "fasteth":
            output = self.send_command(
                f"show bridge mactable interface fasteth{port}", expect_command=False
            )
            macs = re.findall(rf"(\d+)\s+({self.mac_format})", output)
            return macs

        # Для dsl портов
        for sp in self.get_service_ports:  # смотрим маки на сервис портах
            output = self.send_command(
                f"show bridge mactable interface dsl{port}:{sp}", expect_command=False
            )
            macs.extend(re.findall(rf"(\d*)\s+({self.mac_format})", output))

        return macs

    @staticmethod
    def validate_port(port: str) -> tuple:
        """
        Проверяем правильность полученного порта
        Возвращает тип порта и его номер

        >>> IskratelMBan.validate_port('dsl2:1_40')
        ('dsl', 2)

        >>> IskratelMBan.validate_port('port23')
        ('dsl', 23)

        >>> IskratelMBan.validate_port('ISKRATEL:sv-263-3443 atm 2/1')
        ('dsl', 1)

        >>> IskratelMBan.validate_port('24')
        ('dsl', 24)

        >>> IskratelMBan.validate_port('fasteth2')
        ('fasteth', 2)

        >>> IskratelMBan.validate_port('asd 1')
        (None, None)

        """
        port = port.strip()

        # Для fasteth
        if re.match(r"^fasteth\d+$", port):
            return "fasteth", int(port[7:])

        # Для портов типа: 12, port1, dsl2:1_40, ISKRATEL:sv-263-3443 atm 2/1
        port = re.findall(
            r"^(\d+)$|^port(\d+)$|^ISKRATEL.+/(\d+)$|^dsl(\d+):\S+$", port
        )
        if port and any(port[0]):
            return "dsl", int("".join(port[0]))  # Возвращаем номер порта

        return None, None

    def reload_port(self, port: str, save_config=True) -> str:
        """Перезагружаем порт"""

        port_type, port = self.validate_port(port)
        if port_type is None:
            return "Неверный порт!"

        s1 = self.send_command(
            f"set dsl port {port} port_equp unequipped", expect_command=False
        )
        sleep(1)
        s2 = self.send_command(
            f"set dsl port {port} port_equp equipped", expect_command=False
        )

        return s1 + s2

    def set_port(self, port: str, status: str, save_config=True) -> str:
        port_type, port = self.validate_port(port)
        if port_type is None:
            return "Неверный порт!"

        # Меняем состояние порта
        return self.send_command(
            f'set dsl port {port} port_equp {"equipped" if status == "up" else "unequipped"}',
            expect_command=False,
        )

    def get_interfaces(self) -> list:
        """
        Смотрим DSL порты
        :return: [ ['name', 'status', 'desc'], ... ]
        """

        output = self.send_command("show dsl port", expect_command=False)
        res = []
        for line in output.split("\n"):
            interface = re.findall(
                r"(\d+)\s+(\S+)\s+\S+\s+(Equipped|Unequipped)\s+(Up|Down|)", line
            )
            if interface:
                res.append(
                    [
                        interface[0][0],  # name
                        interface[0][3].lower()
                        if interface[0][2] == "Equipped"
                        else "admin down",
                        interface[0][1],  # desc
                    ]
                )

        return res

    def get_vlans(self) -> list:
        return self.get_interfaces()

    def set_description(self, port: str, desc: str) -> str:
        """Меняем описание на порту (ограничение по макс. кол-ву символов - 32)"""

        port_type, port = self.validate_port(port)
        if port_type is None:
            return "Неверный порт!"

        desc = self.clear_description(desc)

        if len(desc) > 32:
            return "Max length:32"

        self.send_command(f"set dsl port {port} name {desc}", expect_command=False)

        return f'Description has been {"changed" if desc else "cleared"}.'

    def change_profile(self, port: str, profile_index: int) -> str:
        """Меняем профиль на DSL порту"""

        port_type, port = self.validate_port(port)
        if port_type is None or port_type != "dsl":
            return "Неверный порт!"

        return self.send_command(
            f"set dsl port {port} profile {profile_index}", expect_command=False
        )
