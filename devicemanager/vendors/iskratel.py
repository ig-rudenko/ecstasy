import os
import pathlib
import re
import shutil
from functools import lru_cache
from time import sleep

from gathering.ftp import FTPCollector
from gathering.ftp.exceptions import NotFound
from .base.device import BaseDevice
from .base.factory import AbstractDeviceFactory
from .base.types import (
    T_InterfaceList,
    T_InterfaceVLANList,
    T_MACList,
    T_MACTable,
    MACType,
    DeviceAuthDict,
    T_Interface,
)
from .. import UnknownDeviceError


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

    @BaseDevice.lock_session
    def get_mac(self, port) -> T_MACList:
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
        return []

    def get_vlans(self) -> list:
        return []

    def reload_port(self, port, save_config=True) -> str:
        return ""

    def set_port(self, port: str, status: str, save_config=True) -> str:
        return ""

    def set_description(self, port: str, desc: str) -> dict:
        return {}

    def get_port_info(self, port: str) -> dict:
        return {}

    def get_port_type(self, port: str) -> str:
        return ""

    def get_port_config(self, port: str) -> str:
        return ""

    def get_port_errors(self, port: str) -> str:
        return ""

    def get_device_info(self) -> dict:
        return {}


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

    def __init__(
        self,
        session,
        ip: str,
        auth: DeviceAuthDict,
        model: str = "",
        snmp_community: str = "",
    ):
        super().__init__(session, ip, auth, model, snmp_community)
        self.dsl_profiles = self._get_dsl_profiles()

    def _get_dsl_profiles(self) -> list:
        return sorted(
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

    def save_config(self):
        pass

    @property
    def _get_service_ports(self) -> list:
        """
        ## Возвращает список сервисных портов

        :return: ```['1_32', '1_33', '1_40']```
        """
        return ["1_32", "1_33", "1_40"]

    def _render_dsl_port_info(self, info: str) -> dict:
        """
        ## Возвращаем информацию о порте DSL

        Создаем таблицу html для представления показателей сигнал/шума, затухания,
        мощности и прочей информации

        ![img.png](/static/docs/img/adsl_info_table.png)

        """

        def color(value: str, s: str) -> str:
            try:
                val = float(value)
            except ValueError:
                return ""

            color_code = ""
            # Определяем цвета в зависимости от числовых значений показателя
            if "Сигнал/Шум" in s:
                gradient = [5, 7, 10, 20]
            elif "Затухание линии" in s:
                gradient = [-60, -50, -40, -20]
                val = -val
            elif "total output power" in s:
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

        # mBAN> show dsl profile
        # ADSL profiles:
        #  Id   Name
        # ------------------------------------
        #  20   160/160
        #  10   160/320
        #  ...

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
        data_rate = re.findall(r"DS Data Rate AS0\s+(\d+) kbit/s\s+US Data Rate LS0\s+(\d+) kbit", info) or [
            ("", "")
        ]
        max_rate = [
            (
                self.find_or_empty(r"Maximum DS attainable aggregate rate\s+(\d+) kbit", info),
                self.find_or_empty(r"Maximum US attainable aggregate rate\s+(\d+) kbit", info),
            )
        ]

        # Нахождение сигнал/шума для нисходящего и восходящего каналов.
        snr = re.findall(r"DS SNR Margin\s+(\d+) dB\s+US SNR Margin\s+(\d+)", info) or [("", "")]
        # Нахождение чередующейся задержки для нисходящего и восходящего каналов.
        intl = re.findall(r"DS interleaved delay\s+(\d+) ms\s+US interleaved delay\s+(\d+)", info) or [
            ("", "")
        ]
        # Нахождение уровня затухания для нисходящего и восходящего каналов.
        att = re.findall(r"DS Attenuation\s+(\d+) dB\s+US Attenuation\s+(\d+)", info) or [("", "")]

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

        return {
            "type": "adsl",
            "data": {
                "profile_name": self.find_or_empty(r"Profile Name\s+(\S+)", info),
                "first_col": first_col_info,
                "streams": table_dict,
                "profiles": self.dsl_profiles,
            },
        }

    @BaseDevice.lock_session
    def get_port_info(self, port: str) -> dict:
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

        port_type, port_number = self.validate_port(port)
        if port_type is None:
            return {"type": "error", "detail": "Неверный порт!"}

        if port_type == "fasteth":
            cmd = f"show interface fasteth{port_number}"
            before_catch = r"\[Enabled Connected Bridging\]"

        else:  # Если указан физический adsl порт
            cmd = f"show dsl port {port_number} detail"
            before_catch = None

        output = self.send_command(cmd, expect_command=False, before_catch=before_catch)

        if port_type == "fasteth":  # Возвращаем первые 4 строки
            # Requested Speed  : Auto
            # Requested Duplex : Auto
            # Actual Speed     : 1000 Mbit/s
            # Actual Duplex    : Full
            return {"type": "text", "data": "\n".join(output.split("\n")[1:5])}

        # Парсим данные
        return self._render_dsl_port_info(output)

    @BaseDevice.lock_session
    def get_mac_table(self) -> T_MACTable:
        """
        ## Возвращает таблицу MAC-адресов оборудования.

        :return: ```[ ({int:vid}, '{mac}', 'dynamic', '{port}'), ... ]```
        """

        output = self.send_command("show bridge mactable", expect_command=False)
        parsed: list[tuple[str, str, str]] = re.findall(rf"(\d+)\s+({self.mac_format})\s+(\S+).*\n", output)
        mac_type: MACType = "dynamic"
        return [(int(vid), mac, mac_type, port) for vid, mac, port in parsed]

    @BaseDevice.lock_session
    def get_mac(self, port: str) -> T_MACList:
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

        port_type, port_number = self.validate_port(port)
        if port_type is None:
            return []

        # Для fasteth портов
        if port_type == "fasteth":
            output = self.send_command(
                f"show bridge mactable interface fasteth{port_number}",
                expect_command=False,
            )
            macs = re.findall(rf"(\d+)\s+({self.mac_format})", output)
            return macs

        # Для dsl портов
        for sp in self._get_service_ports:  # смотрим маки на сервис портах
            output = self.send_command(
                f"show bridge mactable interface dsl{port_number}:{sp}",
                expect_command=False,
            )
            macs.extend(re.findall(rf"(\d*)\s+({self.mac_format})", output))

        return macs

    @staticmethod
    @lru_cache()
    def validate_port(port: str) -> tuple[str | None, int | None]:
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
        port_slice: list[tuple[str, str, str, str]] = re.findall(
            r"^(\d+)$|^port(\d+)$|^ISKRATEL.+/(\d+)$|^dsl(\d+):\S+$", port
        )
        if port_slice and any(port_slice[0]):
            return "dsl", int("".join(port_slice[0]))  # Возвращаем номер порта

        return None, None

    @BaseDevice.lock_session
    def reload_port(self, port: str, save_config=True) -> str:
        """
        ## Перезагружает порт

            mBAN> set dsl port {port_number} port_equp unequipped
            mBAN> set dsl port {port_number} port_equp equipped

        :param port: Порт для перезагрузки
        :param save_config: Если True, конфигурация будет сохранена на устройстве, defaults to True (optional)
        """

        port_type, port_number = self.validate_port(port)
        if port_type is None:
            return "Неверный порт!"

        s1 = self.send_command(f"set dsl port {port_number} port_equp unequipped", expect_command=False)
        sleep(1)
        s2 = self.send_command(f"set dsl port {port_number} port_equp equipped", expect_command=False)

        return s1 + s2

    @BaseDevice.lock_session
    def set_port(self, port: str, status: str, save_config=True) -> str:
        """
        ## Устанавливает статус порта на коммутаторе **up** или **down**

            mBAN> set dsl port {port_number} port_equp {unequipped|equipped}

        :param port: Порт
        :param status: "up" или "down"
        :param save_config: Если True, конфигурация будет сохранена на устройстве, defaults to True (optional)
        """

        port_type, port_number = self.validate_port(port)
        if port_type is None:
            return "Неверный порт!"

        # Меняем состояние порта
        return self.send_command(
            f'set dsl port {port_number} port_equp {"equipped" if status == "up" else "unequipped"}',
            expect_command=False,
        )

    @BaseDevice.lock_session
    def get_interfaces(self) -> T_InterfaceList:
        """
        ## Возвращаем список всех интерфейсов на устройстве

        Команда на оборудовании:

            # show dsl port

        :return: ```[ ('name', 'status', 'desc'), ... ]```
        """

        output = self.send_command("show dsl port", expect_command=False)
        interfaces_list = []
        for line in output.split("\n"):
            interface: list[list[str]] = re.findall(
                r"(\d+)\s+(\S*?)\s+\S+\s+(Equipped|Unequipped)\s*(Up|Down|)", line
            )

            if interface:
                status: T_Interface = "notPresent"
                if interface[0][2] != "Equipped":
                    status = "admin down"
                elif interface[0][3] == "Down":
                    status = "down"
                elif interface[0][3] == "Up":
                    status = "up"

                interfaces_list.append(
                    (
                        interface[0][0],  # name
                        status,
                        interface[0][1],  # desc
                    )
                )

        return interfaces_list

    def get_vlans(self) -> T_InterfaceVLANList:
        """
        ## Возвращаем список всех интерфейсов и его VLAN на коммутаторе.

        Обнаружение VLAN не реализовано

        :return: ```[ ('name', 'status', 'desc', [''] ), ... ]```
        """
        return [(line[0], line[1], line[2], []) for line in self.get_interfaces()]

    @BaseDevice.lock_session
    def set_description(self, port: str, desc: str) -> dict:
        """
        ## Устанавливаем описание для порта предварительно очистив его от лишних символов

        Максимальная длина 32 символа

        Используем команду для изменения:

            mBAN> set dsl port {port_number} name {desc}

        :param port: Порт, для которого вы хотите установить описание
        :param desc: Описание, которое вы хотите установить для порта
        :return: Вывод команды смены описания
        """

        port_type, port_number = self.validate_port(port)
        if port_type is None:
            return {
                "error": "Неверный порт",
                "status": "fail",
                "port": port,
            }

        desc = self.clear_description(desc)

        if len(desc) > 32:
            return {
                "port": port,
                "status": "fail",
                "error": "Too long",
                "max_length": 32,
            }

        self.send_command(f"set dsl port {port_number} name {desc}", expect_command=False)

        return {
            "description": desc,
            "port": port,
            "status": "changed" if desc else "cleared",
            "saved": "no",
        }

    @BaseDevice.lock_session
    def change_profile(self, port: str, profile_index: int) -> str:
        """
        ## Меняем профиль на DSL порту

        :param port: Порт
        :param profile_index: Индекс нового профиля
        :return: Статус изменения профиля либо "Неверный порт!"
        """

        port_type, port_number = self.validate_port(port)
        if port_type is None or port_type != "dsl":
            return "Неверный порт!"

        output = self.send_command(
            f"set dsl port {port_number} profile {profile_index}", expect_command=False
        )
        if "According to the attached ATM QoS" in output:
            # Если возникает ошибка:
            #   Profile can't be changed. According to the attached ATM QoS profile
            #   DSL downstream rate can't be less than 21024 kbits/s!
            no_policing = self.send_command(
                f"set atm vc tp dsl{port_number}:1_33 qos_profile UBR:No-policing",
                expect_command=False,
            )
            if "successfully updated" in no_policing:
                # Если ограничение снято, снова меняем профиль
                output = self.send_command(
                    f"set dsl port {port_number} profile {profile_index}",
                    expect_command=False,
                )

        return output

    def get_port_type(self, port: str) -> str:
        return "COPPER"

    def get_port_config(self, port: str) -> str:
        return ""

    def get_port_errors(self, port: str) -> str:
        return ""

    def get_device_info(self) -> dict:
        # > show system info
        return {}

    def get_current_configuration(self) -> pathlib.Path:
        """
        Эта функция загружает с FTP-сервера папку конфигурации
        """

        local_folder_path = pathlib.Path(os.getenv("CONFIG_FOLDER_PATH", "temp_configs"))
        local_folder_path.mkdir(parents=True, exist_ok=True)

        ftp = FTPCollector(host=self.ip, timeout=30)
        ftp.login(username=self.auth["login"], password=self.auth["password"])
        folder_pattern = re.compile(r"^MY\S+77$")

        # Предпочтительная папка MY****77
        try:
            config_folder = ftp.download_folder(folder_or_pattern=folder_pattern, local_dir=local_folder_path)
        except NotFound:
            # Если такой нет, то MY****5*
            folder_pattern = re.compile(r"^MY\S+5\d$")
            config_folder = ftp.download_folder(folder_or_pattern=folder_pattern, local_dir=local_folder_path)

        archive_path = config_folder

        # Создаем архив
        shutil.make_archive(str(archive_path.absolute()), "zip", config_folder)
        archive_path = archive_path.parent / f"{archive_path.name}.zip"
        shutil.rmtree(config_folder, ignore_errors=True)  # Удаляем папку
        return archive_path


class IskratelFactory(AbstractDeviceFactory):
    @staticmethod
    def is_can_use_this_factory(session=None, version_output=None) -> bool:
        return bool(version_output and re.search(r"ISKRATEL|IskraTEL", str(version_output)))

    @classmethod
    def get_device(
        cls,
        session,
        ip: str,
        snmp_community: str,
        auth: DeviceAuthDict,
        version_output: str = "",
    ) -> BaseDevice:
        # ISKRATEL CONTROL
        if "ISKRATEL" in version_output:
            return IskratelControl(
                session,
                ip,
                auth,
                model="ISKRATEL Switching",
                snmp_community=snmp_community,
            )

        # ISKRATEL mBAN>
        if "IskraTEL" in version_output:
            model = BaseDevice.find_or_empty(r"CPU: IskraTEL \S+ (\S+)", version_output)
            return IskratelMBan(session, ip, auth, model=model, snmp_community=snmp_community)

        raise UnknownDeviceError("IskratelFactory не удалось распознать модель оборудования", ip=ip)
