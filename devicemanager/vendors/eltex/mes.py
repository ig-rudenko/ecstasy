import re
from time import sleep
from typing import List, Tuple

import pexpect
import textfsm

from ..base.device import BaseDevice
from ..base.helpers import interface_normal_view, parse_by_template
from ..base.validators import validate_and_format_port_as_normal
from ..base.types import (
    TEMPLATE_FOLDER,
    T_InterfaceList,
    T_InterfaceVLANList,
    T_MACList,
    T_MACTable,
    InterfaceStatus,
)


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
        ## При инициализации смотрим характеристики устройства.

        :param session: Это объект сеанса pexpect c установленной сессией оборудования
        :param ip: IP-адрес устройства, к которому вы подключаетесь
        :param auth: словарь, содержащий имя пользователя и пароль для устройства
        :param model: Модель коммутатора. Это используется для определения подсказки
        """

        super().__init__(session, ip, auth, model)
        self.mac = mac
        self._find_system_info()

    def _find_system_info(self):
        inv = self.send_command("show inventory", expect_command=False)
        # Нахождение серийного номера устройства.
        self.serialno = self.find_or_empty(r"SN: (\S+)", inv)

    @BaseDevice.lock_session
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

    @BaseDevice.lock_session
    def get_interfaces(self) -> T_InterfaceList:
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
            match = self.session.expect([self.prompt, self.space_prompt, pexpect.TIMEOUT])
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

        result: List[List[str, str, str, str]] = parse_by_template(
            f"interfaces/{self._template_name}.template", output
        )

        interfaces = []
        for port_name, admin_status, link_status, desc in result:
            if port_name.startswith("V"):
                # Пропускаем Vlan интерфейсы
                continue
            if admin_status.lower() != "up":
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
                    f"show running-config interface {interface_normal_view(line[0])}",
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

    @staticmethod
    def normalize_interface_name(intf: str) -> str:
        return interface_normal_view(intf)

    @BaseDevice.lock_session
    def get_mac_table(self) -> T_MACTable:
        """
        ## Возвращаем список из VLAN, MAC-адреса, dynamic и порта для данного оборудования.

        Команда на оборудовании:

            # show mac address-table

        :return: ```[ ({int:vid}, '{mac}', 'dynamic', '{port}'), ... ]```
        """
        mac_str = self.send_command("show mac address-table", expect_command=False)
        mac_table = re.findall(
            rf"(\d+)\s+({self.mac_format})\s+(\S+\s?\d+/\d+/\d+)\s+(dynamic).*\n",
            mac_str,
            flags=re.IGNORECASE,
        )
        return [(int(vid), mac, type_, port) for vid, mac, port, type_ in mac_table]

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal(if_invalid_return=[])
    def get_mac(self, port) -> T_MACList:
        """
        ## Возвращаем список из VLAN и MAC-адреса для данного порта.

        Команда на оборудовании:

            # show mac address-table interface {port}

        :param port: Номер порта коммутатора
        :return: ```[ ('vid', 'mac'), ... ]```
        """

        mac_str = self.send_command(f"show mac address-table interface {port}")
        macs_list: List[Tuple[str, str]] = re.findall(
            rf"(\d+)\s+({self.mac_format})\s+\S+\s+\S+", mac_str
        )
        return [(int(vid), mac) for vid, mac in macs_list]

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal()
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

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal()
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

    @validate_and_format_port_as_normal()
    @BaseDevice.lock_session
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

    @validate_and_format_port_as_normal()
    def _get_port_stats(self, port):
        """
        ## Возвращает полную информацию о порте.

        Через команду:

            # show interfaces {port}

        :param port: Номер порта, для которого требуется получить информацию
        """

        return self.send_command(f"show interfaces {port}").split("\n")

    @validate_and_format_port_as_normal()
    def get_port_type(self, port) -> str:
        """
        ## Возвращает тип порта

        :param port: Порт для проверки
        :return: "SFP", "COPPER", "COMBO-FIBER", "COMBO-COPPER" или "?"
        """

        port_type = self.find_or_empty(r"Type: (\S+)", self.get_port_info(port).get("data"))
        if "Fiber" in port_type:
            return "SFP"
        if "Copper" in port_type:
            return "COPPER"
        if "Combo-F" in port_type:
            return "COMBO-FIBER"
        if "Combo-C" in port_type:
            return "COMBO-COPPER"
        return "?"

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal()
    def get_port_config(self, port: str) -> str:
        """
        ## Выводим конфигурацию порта

        Используем команду:

            # show running-config interface {port}

        """

        return self.send_command(f"show running-config interface {port}").strip()

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal()
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

    @BaseDevice.lock_session
    @validate_and_format_port_as_normal()
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

            return "Max length:" + self.find_or_empty(r" Up to (\d+) characters", output)

        self.session.sendline("end")
        self.session.expect(self.prompt)

        self.lock = False
        # Возвращаем строку с результатом работы и сохраняем конфигурацию
        return f'Description has been {"changed" if desc else "cleared"}. {self.save_config()}'

    def get_device_info(self) -> dict:
        return {}
