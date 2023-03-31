from functools import wraps
import re
from time import sleep
import pexpect
import textfsm
from .base import (
    BaseDevice,
    TEMPLATE_FOLDER,
    FIBER_TYPES,
    COOPER_TYPES,
    interface_normal_view,
    T_InterfaceList,
    T_InterfaceVLANList,
    T_MACList,
    T_MACTable,
)


class Cisco(BaseDevice):
    """
    # Для оборудования от производителя Cisco

    Проверено для:
     - WC-C3550
     - WC-C3560
     - WC-C3750G
     - WC-C4500X
     - ME-3400
     - ME-3600X
     - ME-3800X
     - ME-4924
    """

    prompt = r"\S+#$"
    space_prompt = r" --More-- "
    mac_format = r"\S\S\S\S\.\S\S\S\S\.\S\S\S\S"  # 0018.e7d3.1d43
    vendor = "Cisco"

    def __init__(self, session: pexpect, ip: str, auth: dict, model: str = ""):
        """
        ## При инициализации смотрим характеристики устройства:

            # show version

          - MAC
          - серийный номер

        :param session: Это объект сеанса pexpect c установленной сессией оборудования
        :param ip: IP-адрес устройства, к которому вы подключаетесь
        :param auth: словарь, содержащий имя пользователя и пароль для устройства
        :param model: Модель коммутатора. Это используется для определения подсказки
        """
        super().__init__(session, ip, auth, model)
        version = self.send_command("show version")
        self.serialno = self.find_or_empty(r"System serial number\s+: (\S+)", version)
        self.mac = self.find_or_empty(r"[MACmac] [Aa]ddress\s+: (\S+)", version)
        self.__cache_port_info = {}

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
                port = interface_normal_view(port)
                if not port:
                    # Неверный порт
                    return if_invalid_return

                # Вызываем метод
                return func(self, port, *args, **kwargs)

            return __wrapper

        return validate

    @staticmethod
    def normalize_interface_name(intf: str) -> str:
        return interface_normal_view(intf)

    @BaseDevice._lock
    def save_config(self):
        """
        ## Сохраняем конфигурацию оборудования командой:

            # write

        Ожидаем ответа от оборудования **[OK]**,
        если нет, то пробуем еще 2 раза, в противном случае ошибка сохранения
        """

        for _ in range(3):  # Пробуем 3 раза, если ошибка
            self.session.sendline("write")
            # self.session.expect(r'Building configuration')
            if self.session.expect([self.prompt, r"\[OK\]"]):
                self.session.expect(self.prompt)
                return self.SAVED_OK
        return self.SAVED_ERR

    @BaseDevice._lock
    def get_interfaces(self) -> T_InterfaceList:
        """
        ## Возвращаем список всех интерфейсов на устройстве

        Команда на оборудовании:

            # show interfaces description

        :return: ```[ ('name', 'status', 'desc'), ... ]```
        """

        output = self.send_command("show interfaces description")
        output = re.sub(".+\nInterface", "Interface", output)
        with open(
            f"{TEMPLATE_FOLDER}/interfaces/cisco.template", "r", encoding="utf-8"
        ) as template_file:
            int_des_ = textfsm.TextFSM(template_file)
            result = int_des_.ParseText(output)  # Ищем интерфейсы
        return [
            (
                line[0],  # interface
                line[2].lower()
                if "up" in line[1].lower()
                else line[1].lower(),  # status
                line[3],  # desc
            )
            for line in result
            if not line[0].startswith("V")
        ]

    @BaseDevice._lock
    def get_vlans(self) -> T_InterfaceVLANList:
        """
        ## Возвращаем список всех интерфейсов и его VLAN на коммутаторе.

        Для начала получаем список всех интерфейсов через метод **get_interfaces()**

        Затем для каждого интерфейса смотрим конфигурацию и выбираем строчки,
        в которых указаны VLAN:

         - ```access vlan {vid}```
         - ```allowed vlan {vid},{vid},...{vid}```
         - ```allowed vlan add {vid},{vid},...{vid}```

        :return: ```[ ('name', 'status', 'desc', ['{vid}', '{vid},{vid},...{vid}', ...] ), ... ]```
        """

        result = []

        self.lock = False
        interfaces = self.get_interfaces()
        self.lock = True

        for line in interfaces:
            line: list = list(line)
            # Отфильтровываем интерфейсы VLAN.
            if not line[0].startswith("V"):
                output = self.send_command(
                    command=f"show running-config interface {interface_normal_view(line[0])}",
                    before_catch="Building configuration",
                    expect_command=False,
                )
                vlans_group = re.findall(
                    r"(?<=access|llowed) vlan [ad\s]*(\S*\d)", output
                )  # Строчки вланов
                line = line + [vlans_group]
                result.append(tuple(line))

        return result

    @BaseDevice._lock
    @_validate_port(if_invalid_return=[])
    def get_mac(self, port) -> T_MACList:
        """
        ## Возвращаем список из VLAN и MAC-адреса для данного порта.

        Команда на оборудовании:

            # show mac address-table interface {port}

        :param port: Номер порта коммутатора
        :return: ```[ ('vid', 'mac'), ... ]```
        """

        mac_str = self.send_command(
            f"show mac address-table interface {port}",
            expect_command=False,
        )
        return re.findall(rf"(\d+)\s+({self.mac_format})\s+\S+\s+\S+", mac_str)

    @BaseDevice._lock
    def get_mac_table(self) -> T_MACTable:
        """
        ## Возвращаем список из VLAN, MAC-адреса, dynamic и порта для данного оборудования.

        Команда на оборудовании:

            # show mac address-table

        :return: ```[ ({int:vid}, '{mac}', 'dynamic', '{port}'), ... ]```
        """

        mac_str = self.send_command(
            f"show mac address-table",
            expect_command=False,
        )
        mac_table = re.findall(
            rf"(\d+)\s+({self.mac_format})\s+(dynamic|static)\s+.*?(\S+)\s*\n",
            mac_str,
            flags=re.IGNORECASE,
        )
        return [(int(vid), mac, type_, port) for vid, mac, type_, port in mac_table]

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
        self.session.expect(self.prompt)
        self.session.sendline(f"interface {port}")
        self.session.expect(self.prompt)
        self.session.sendline("shutdown")
        sleep(1)
        self.session.sendline("no shutdown")
        self.session.expect(self.prompt)
        self.session.sendline("end")

        r = self.session.before.decode(errors="ignore")
        self.lock = False
        s = self.save_config() if save_config else "Without saving"
        return r + s

    @BaseDevice._lock
    @_validate_port()
    def set_port(self, port, status, save_config=True) -> str:
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
        self.session.expect(self.prompt)
        self.session.sendline(f"interface {port}")
        self.session.expect(self.prompt)
        if status == "up":
            self.session.sendline("no shutdown")
        elif status == "down":
            self.session.sendline("shutdown")
        self.session.sendline("end")
        self.session.expect(self.prompt)

        r = self.session.before.decode(errors="ignore")
        self.lock = False
        s = self.save_config() if save_config else "Without saving"
        return r + s

    @_validate_port()
    @BaseDevice._lock
    def get_port_info(self, port: str) -> dict:
        """
        ## Возвращаем информацию о порте.

        Через команду:

            # show interfaces {port}

        Выводим строчки в которых указано **media**

        Пример вывода:

        ```Full-duplex, 10Gb/s, link type is auto, media type is 10GBase-LR```

        :param port: Номер порта, для которого требуется получить информацию

        """

        port_info = self.send_command(f"show interfaces {port}", expect_command=False)

        # Сохраняем в кэш
        self.__cache_port_info[port] = port_info

        return {
            "type": "text",
            "data": "\n".join(port_info.splitlines()[1:]),
        }

    @_validate_port()
    def get_port_type(self, port: str) -> str:
        """
        ## Возвращает тип порта

        Тип порта определяется по стандарту IEE 802.3

        ### Обозначения медных типов
            T, TX, VG, CX, CR
        ### Обозначения оптоволоконных типов:
            FOIRL, F, FX, SX, LX, BX, EX, ZX, SR, ER, SW, LW, EW, LRM, PR, LR, ER, FR, LH

        Оптоволокно:

            media type is LX
            media type is SFP-LR
            media type is No XCVR
            media type is 10GBase-LR
            media type is 1000BaseBX10-U SFP

        Медь:

            media type is RJ45
            media type is 10/100/1000BaseTX

        Не определено:

            media type is unsupported
            media type is Not Present
            media type is unknown media type

        :param port: Порт для проверки
        :return: "SFP", "COPPER" или "?"
        """

        # Получаем информацию о порте.
        port_info = self.__cache_port_info.get(port) or self.get_port_info(port).get(
            "data", ""
        )
        # Ищем тип порта.
        port_type = "".join(
            self.find_or_empty(
                r"media type is .+[Bb]ase[-]?(\S{1,2})|media type is (.+)", port_info
            )
        )
        # Проверка, является ли порт оптоволоконным.
        if "No XCVR" in port_type or "SFP" in port_info or port_type in FIBER_TYPES:
            return "SFP"
        elif "RJ45" in port_type or port_type in COOPER_TYPES:
            return "COPPER"
        else:
            return "?"

    @_validate_port()
    def get_port_errors(self, port: str) -> str:
        """
        ## Выводим ошибки на порту

        :param port: Порт для проверки на наличие ошибок
        """

        # Получаем информацию о порте.
        port_info = self.__cache_port_info.get(port) or self.get_port_info(port).get(
            "data", ""
        )

        media_type = [
            line.strip() for line in port_info.split("\n") if "errors" in line
        ]
        return "<p>" + "\n".join(media_type) + "</p>"

    @BaseDevice._lock
    @_validate_port()
    def get_port_config(self, port: str) -> str:
        """
        ## Выводим конфигурацию порта

        Используем команду:

            # show running-config interface {port}
        """

        config = self.send_command(
            f"show running-config interface {port}",
            before_catch=r"Current configuration.+?\!",
        ).strip()
        return config

    @BaseDevice._lock
    def search_mac(self, mac_address: str) -> list:
        """
        ## Ищем MAC адрес в таблице ARP оборудования

        **MAC необходимо передавать без разделительных символов**
        он сам преобразуется к виду, требуемому для Cisco

        Отправляем на оборудование команду:

            # show arp | include {mac_address}

        Возвращаем список всех IP-адресов, VLAN, связанных с этим MAC-адресом.

        :param mac_address: MAC-адрес, который вы хотите найти
        :return: ```[['IP', 'MAC', 'VLAN'], ...]```
        """
        if len(mac_address) < 12:
            return []

        formatted_mac = "{}{}{}{}.{}{}{}{}.{}{}{}{}".format(*mac_address.lower())

        match = self.send_command(f"show arp | include {formatted_mac}")

        # Форматируем вывод
        with open(
            f"{TEMPLATE_FOLDER}/arp_format/{self.vendor.lower()}.template",
            encoding="utf-8",
        ) as template_file:
            template = textfsm.TextFSM(template_file)
        formatted_result = template.ParseText(match)

        return formatted_result

    @BaseDevice._lock
    def search_ip(self, ip_address: str) -> list:
        """
        ## Ищем IP адрес в таблице ARP оборудования

        Отправляем на оборудование команду:

            # show arp | include {ip_address}

        Возвращаем список всех MAC-адресов, VLAN, связанных с этим IP-адресом.

        :param ip_address: IP-адрес, который вы хотите найти
        :return: ```['IP', 'MAC', 'VLAN']```
        """

        match = self.send_command(f"show arp | include {ip_address}")

        # Форматируем вывод
        with open(
            f"{TEMPLATE_FOLDER}/arp_format/{self.vendor.lower()}.template",
            encoding="utf-8",
        ) as template_file:
            template = textfsm.TextFSM(template_file)
        formatted_result = template.ParseText(match)

        return formatted_result

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

        if (
            desc == ""
        ):  # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            res = self.send_command("no description", expect_command=False)

        else:  # В другом случае, меняем описание на оборудовании
            res = self.send_command(f"description {desc}", expect_command=False)

        self.session.sendline("end")  # Выходим из режима редактирования
        if "Invalid input detected" in res:
            return "Invalid input detected"

        self.lock = False
        # Возвращаем строку с результатом работы и сохраняем конфигурацию
        return f'Description has been {"changed" if desc else "cleared"}. {self.save_config()}'

    @BaseDevice._lock
    def get_device_info(self) -> dict:
        data = {"cpu": {}, "ram": {}, "flash": {}}
        for key in data:
            data[key]["util"] = getattr(self, f"get_{key}_utilization")()
        data["temp"] = self.get_temp()
        return data

    def get_cpu_utilization(self) -> tuple:
        """
        ## Возвращает загрузку ЦП хоста
        """

        cpu_percent = re.findall(
            r"one minute: (\d+)%",
            self.send_command(
                "show processes cpu | include minute", expect_command=False
            ),
            flags=re.IGNORECASE,
        )

        return tuple(map(int, cpu_percent))

    def get_flash_utilization(self) -> int:
        """
        ## Возвращает использование флэш-памяти устройства
        """

        flash = self.find_or_empty(
            r"(\d+)\s+(\d+)\s+\S+\s+\S+\s+[boot]*flash",
            self.send_command("show file systems"),
            flags=re.IGNORECASE,
        )

        flash_percent = (
            int((int(flash[0]) - int(flash[1])) / int(flash[0]) * 100) if flash else -1
        )
        return flash_percent

    def get_ram_utilization(self) -> int:
        """
        ## Возвращает использование DRAM в процентах
        """

        output = self.send_command("show memory statistics")
        pattern = r"Processor\s+\S+\s+(\d+)\s+(\d+)"

        if "Invalid input" in output:
            output = self.send_command("show memory")
            pattern = r"Process\s+(\d+)\s+(\d+)"

        ram = self.find_or_empty(pattern, output, flags=re.IGNORECASE)
        dram_percent = int(int(ram[1]) / int(ram[0]) * 100) if ram else -1

        return dram_percent

    def get_temp(self) -> dict:

        output = self.send_command("show env temp status")
        pattern = r"Temperature Value: ([-]?\d+[.]?\d?) Degree Celsius"

        if "Invalid input" in output:
            output = self.send_command("show env temp")
            pattern = r"CPU\s+([-]?\d+)C"

        temp = self.find_or_empty(pattern, output)

        if not temp:
            return {}

        temp = float(temp)

        high_temp = "".join(
            self.find_or_empty(
                r"SYSTEM High Temperature Shutdown Threshold: (\d+[.]?\d?) Degree Celsius|"
                r"Red Threshold    : (\d+) Degree Celsius",
                output,
            )
            or 80
        )
        medium_temp = "".join(
            self.find_or_empty(
                r"SYSTEM High Temperature Alert Threshold: (\d+[.]?\d?) Degree Celsius|"
                r"Yellow Threshold : (\d+) Degree Celsius",
                output,
            )
            or 60
        )
        low_temp = (
            self.find_or_empty(
                r"SYSTEM Low Temperature Alert Threshold: (\d+[.]?\d?) Degree Celsius",
                output,
            )
            or 0
        )

        status = "normal"
        if temp >= float(medium_temp):
            status = "medium"
        elif temp >= float(high_temp) - 6:
            status = "high"
        elif temp <= float(low_temp):
            status = "low"

        return {"value": temp, "status": status}

    @BaseDevice._lock
    def get_current_configuration(self, *args, **kwargs) -> str:
        return self.send_command(
            "show running-config",
            expect_command=True,
            before_catch=r"Building configuration\.\.\.",
        )
