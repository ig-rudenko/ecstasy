import re
from functools import lru_cache
from time import sleep
from typing import Tuple

from django.template.loader import render_to_string
from .base import BaseDevice, InterfaceList, InterfaceVLANList, MACList


class IskratelControl(BaseDevice):
    """
    # Для плат управления DSLAM от производителя Iskratel
    """

    prompt = r"\(\S+\)\s*#"
    space_prompt = r"--More-- or \(q\)uit"
    mac_format = r"\S\S:" * 5 + r"\S\S"
    vendor = "Iskratel"

    def save_config(self):
        pass

    @BaseDevice._lock
    def get_mac(self, port) -> MACList:
        """
        ## Возвращаем список из VLAN и MAC-адреса для данного порта.

        Команда на оборудовании:

            # show mac-addr-table interface {port}

        :param port: Номер порта коммутатора
        :return: ```[ ('vid', 'mac'), ... ]```
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

    def get_port_info(self, port: str) -> str:
        pass

    def get_port_type(self, port: str) -> str:
        pass

    def get_port_config(self, port: str) -> str:
        pass

    def get_port_errors(self, port: str) -> str:
        pass


class IskratelMBan(BaseDevice):
    """
    # Для плат DSLAM от производителя Iskratel

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
    def _get_service_ports(self) -> list:
        """
        ## Возвращает список сервисных портов

        :return: ```['1_32', '1_33', '1_40']```
        """
        return ["1_32", "1_33", "1_40"]

    def _render_dsl_port_info(self, info: str) -> str:
        """
        ## Возвращаем информацию о порте DSL

        Создаем таблицу html для представления показателей сигнал/шума, затухания,
        мощности и прочей информации

        ![img.png](/static/docs/img/adsl_info_table.png)

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

        # Определение скорости передачи данных для порта DSL.
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

        # Нахождение сигнал/шума для нисходящего и восходящего каналов.
        snr = re.findall(r"DS SNR Margin\s+(\d+) dB\s+US SNR Margin\s+(\d+)", info) or [
            ("", "")
        ]
        # Нахождение чередующейся задержки для нисходящего и восходящего каналов.
        intl = re.findall(
            r"DS interleaved delay\s+(\d+) ms\s+US interleaved delay\s+(\d+)", info
        ) or [("", "")]
        # Нахождение уровня затухания для нисходящего и восходящего каналов.
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

    @BaseDevice._lock
    def get_port_info(self, port: str) -> str:
        """
        ## Смотрим информацию на порту

        Порт будет преобразован в число

        Для Ethernet порта используем команду:

            mBAN> show interface fasteth{port_number}

        И возвращаем:

            # Requested Speed  : Auto
            # Requested Duplex : Auto
            # Actual Speed     : 1000 Mbit/s
            # Actual Duplex    : Full

        Для DLS порта используем команду:

            mBAN> show dsl port {port_number} detail

        И возвращаем:

            HTML

        ![img.png](/static/docs/img/adsl_info.png)

        :param port: Порт
        :return: Информация о порте либо ```"Неверный порт!"```
        """

        port_type, port = self.validate_port(port)
        if port_type is None:
            return "Неверный порт!"

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
        return self._render_dsl_port_info(output)

    @BaseDevice._lock
    def get_mac(self, port: str) -> MACList:
        """
        ## Возвращаем список из VLAN и MAC-адреса для данного порта.

        Для Ethernet порта используем команду:

            mBAN> show bridge mactable interface fasteth{port_number}

        Для DLS порта используем команду:

            mBAN> show bridge mactable interface dsl{port_number}:{service_port}

        :param port: Номер порта коммутатора
        :return: ```[ ('vid', 'mac'), ... ]```
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
        for sp in self._get_service_ports:  # смотрим маки на сервис портах
            output = self.send_command(
                f"show bridge mactable interface dsl{port}:{sp}", expect_command=False
            )
            macs.extend(re.findall(rf"(\d*)\s+({self.mac_format})", output))

        return macs

    @staticmethod
    @lru_cache()
    def validate_port(port: str) -> (Tuple[str, int], Tuple[None, None]):
        """
        ## Проверяем правильность полученного порта

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

    @BaseDevice._lock
    def reload_port(self, port: str, save_config=True) -> str:
        """
        ## Перезагружает порт

            mBAN> set dsl port {port_number} port_equp unequipped
            mBAN> set dsl port {port_number} port_equp equipped

        :param port: Порт для перезагрузки
        :param save_config: Если True, конфигурация будет сохранена на устройстве, defaults to True (optional)
        """

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

    @BaseDevice._lock
    def set_port(self, port: str, status: str, save_config=True) -> str:
        """
        ## Устанавливает статус порта на коммутаторе **up** или **down**

            mBAN> set dsl port {port_number} port_equp {unequipped|equipped}

        :param port: Порт
        :param status: "up" или "down"
        :param save_config: Если True, конфигурация будет сохранена на устройстве, defaults to True (optional)
        """

        port_type, port = self.validate_port(port)
        if port_type is None:
            return "Неверный порт!"

        # Меняем состояние порта
        return self.send_command(
            f'set dsl port {port} port_equp {"equipped" if status == "up" else "unequipped"}',
            expect_command=False,
        )

    @BaseDevice._lock
    def get_interfaces(self) -> InterfaceList:
        """
        ## Возвращаем список всех интерфейсов на устройстве

        Команда на оборудовании:

            # show dsl port

        :return: ```[ ('name', 'status', 'desc'), ... ]```
        """

        output = self.send_command("show dsl port", expect_command=False)
        interfaces_list = []
        for line in output.split("\n"):
            interface = re.findall(
                r"(\d+)\s+(\S+)\s+\S+\s+(Equipped|Unequipped)\s+(Up|Down|)", line
            )
            if interface:
                interfaces_list.append(
                    (
                        interface[0][0],  # name
                        interface[0][3].lower()
                        if interface[0][2] == "Equipped"
                        else "admin down",
                        interface[0][1],  # desc
                    )
                )

        return interfaces_list

    def get_vlans(self) -> InterfaceVLANList:
        """
        ## Возвращаем список всех интерфейсов и его VLAN на коммутаторе.

        Обнаружение VLAN не реализовано

        :return: ```[ ('name', 'status', 'desc', [''] ), ... ]```
        """
        return [(line[0], line[1], line[2], [""]) for line in self.get_interfaces()]

    @BaseDevice._lock
    def set_description(self, port: str, desc: str) -> str:
        """
        ## Устанавливаем описание для порта предварительно очистив его от лишних символов

        Максимальная длина 32 символа

        Используем команду для изменения:

            mBAN> set dsl port {port_number} name {desc}

        :param port: Порт, для которого вы хотите установить описание
        :param desc: Описание, которое вы хотите установить для порта
        :return: Вывод команды смены описания
        """

        port_type, port = self.validate_port(port)
        if port_type is None:
            return "Неверный порт!"

        desc = self.clear_description(desc)

        if len(desc) > 32:
            return "Max length:32"

        self.send_command(f"set dsl port {port} name {desc}", expect_command=False)

        return f'Description has been {"changed" if desc else "cleared"}.'

    @BaseDevice._lock
    def change_profile(self, port: str, profile_index: int) -> str:
        """
        ## Меняем профиль на DSL порту

        :param port: Порт
        :param profile_index: Индекс нового профиля
        :return: Статус изменения профиля либо "Неверный порт!"
        """

        port_type, port = self.validate_port(port)
        if port_type is None or port_type != "dsl":
            return "Неверный порт!"

        return self.send_command(
            f"set dsl port {port} profile {profile_index}", expect_command=False
        )

    def get_port_type(self, port: str) -> str:
        pass

    def get_port_config(self, port: str) -> str:
        pass

    def get_port_errors(self, port: str) -> str:
        pass
