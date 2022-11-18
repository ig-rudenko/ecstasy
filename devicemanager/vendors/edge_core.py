import re
from time import sleep
from functools import lru_cache
import pexpect
import textfsm
from .base import (
    BaseDevice,
    TEMPLATE_FOLDER,
    _interface_normal_view,
    InterfaceList,
    InterfaceVLANList,
    MACList,
)


class EdgeCore(BaseDevice):
    """
    # Для оборудования от производителя Edge-Core
    """

    prompt = r"\S+#$"
    space_prompt = "---More---"
    vendor = "Edge-Core"
    mac_format = r"\S\S-" * 5 + r"\S\S"

    def get_interfaces(self) -> InterfaceList:
        """
        ## Возвращаем список всех интерфейсов на устройстве

        Команда на оборудовании:

            # show interfaces status

        :return: [ ('name', 'status', 'desc'), ... ]
        """

        output = self.send_command("show interfaces status")
        with open(
            f"{TEMPLATE_FOLDER}/interfaces/edge_core.template", "r", encoding="utf-8"
        ) as template_file:
            int_des_ = textfsm.TextFSM(template_file)
        result = int_des_.ParseText(output)  # Ищем интерфейсы
        return [
            (
                line[0],  # interface
                line[2].lower()
                if "Up" in line[1].lower()
                else line[1].lower(),  # status
                line[3],  # desc
            )
            for line in result
            if not line[0].startswith("V")
        ]

    def get_vlans(self) -> InterfaceVLANList:
        """
        ## Возвращаем список всех интерфейсов и его VLAN на коммутаторе.

        Для начала получаем список всех интерфейсов через метод **get_interfaces()**

        Затем для каждого интерфейса смотрим конфигурацию и выбираем строчки,
        в которых указаны VLAN:

         - ```VLAN {vid}```
         - ```VLAN add {vid},{vid},...{vid}```

        :return: [ ('name', 'status', 'desc', ['{vid}', '{vid},{vid},...{vid}', ...] ), ... ]
        """

        # Получение текущей конфигурации устройства.
        running_config = self.send_command("show running-config")
        interfaces = self.get_interfaces()

        # Разделение текущей конфигурации на список строк. Каждая строка является частью конфигурации порта.
        split_config = running_config.split("interface ")
        int_vlan = {}

        # Разбиваем конфиг на части.
        for piece in split_config:
            # Проверяем, что начинается строка с интерфейса.
            if piece.startswith("ethernet"):
                vlans = []

                # Ищем VLAN в конфигурации.
                for v in re.findall(r"VLAN[ad ]*([\d,]*)", piece):
                    # Разбиваем строку чисел, разделенных запятыми, на список чисел.
                    vlans.extend(v.split(","))

                # Добавляем в словарь с ключом интерфейса отсортированный список VLANs
                int_vlan[self.find_or_empty(r"^ethernet \d+/\d+", piece)] = sorted(
                    list(set(vlans))
                )

        # Распаковка кортежа `line` и добавление кортежа `vlans` в конец нового кортежа.
        # Создание списка кортежей.
        interfaces_vlans = [
            (
                line[0],  # Интерфейс
                line[1],  # Статус
                line[2],  # Описание
                int_vlan[_interface_normal_view(line[0]).lower()],  # Добавляем VLANs
            )
            for line in interfaces
        ]

        return interfaces_vlans

    def save_config(self):
        """
        ## Сохраняем конфигурацию оборудования командой:

            # copy running-config startup-config

        Ожидаем ответа от оборудования.
        Если **fail** или **error** - ошибка сохранения, иначе сохранено
        """

        self.session.sendline("copy running-config startup-config")
        self.session.sendline("\n")
        if self.session.expect([r"fail|err", self.prompt, pexpect.TIMEOUT]) == 1:
            return self.SAVED_OK
        return self.SAVED_ERR

    @staticmethod
    def validate_port(port: str):
        """
        ## Проверяем порт на валидность

        >>> EdgeCore.validate_port("1/2")
        None
        >>> EdgeCore.validate_port("eth 1/1")
        'Ethernet 1/1'
        >>> EdgeCore.validate_port("gi 2/1")
        'GigabitEthernet 2/1'
        >>> EdgeCore.validate_port("re 1/1")
        None
        """

        port = port.strip()
        # Проверяем, имеет ли порт формат `<type> <number>/<number>`
        if re.findall(r"^\S+ \d+/\d+$", port):
            return _interface_normal_view(port) or None

        return None

    def get_mac(self, port: str) -> MACList:
        """
        ## Возвращаем список из VLAN и MAC-адреса для данного порта.

        Команда на оборудовании:

            # show mac address-table interface {port}

        :param port: Номер порта коммутатора
        :return: [ ('vid', 'mac'), ... ]
        """

        port = self.validate_port(port)
        if port is None:
            return []

        output = self.send_command(f"show mac-address-table interface {port}")
        macs = re.findall(rf"({self.mac_format})\s+(\d+)", output)
        return [m[::-1] for m in macs]

    def reload_port(self, port: str, save_config=True) -> str:
        """
        ## Перезагружает порт

        Переходим в режим конфигурирования:

            # configure

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

        port = self.validate_port(port)
        if port is None:
            return "Неверный порт!"

        self.session.sendline("configure")
        self.session.expect(self.prompt)
        self.session.sendline(f"interface {port}")
        self.session.sendline("shutdown")
        self.session.expect(self.prompt)
        sleep(1)
        self.session.sendline("no shutdown")
        self.session.expect(self.prompt)
        self.session.sendline("end")
        self.session.expect(self.prompt)

        s = self.save_config() if save_config else "Without saving"
        return s

    def set_port(self, port: str, status: str, save_config=True) -> str:
        """
        ## Устанавливает статус порта на коммутаторе **up** или **down**

        Переходим в режим конфигурирования:
            # configure

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

        port = self.validate_port(port)
        if port is None:
            return "Неверный порт!"

        self.session.sendline("configure")
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
        s = self.save_config() if save_config else "Without saving"
        return r + s

    @lru_cache
    def __get_port_info(self, port: str) -> str:
        """
        ## Возвращает информацию о порте.

        Если переданный порт неверный, то вернет ```"Неверный порт!"```

        :param port: Номер порта, для которого требуется получить информацию
        """
        port = self.validate_port(port)
        if port is None:
            return "Неверный порт!"

        return self.send_command(f"show interfaces status {port}")

    def port_type(self, port: str) -> str:
        """
        # Возвращает тип порта

        :param port: Порт для проверки
        :return: "SFP" или "COPPER"
        """
        if self.find_or_empty(r"Port type: (\S+)", self.__get_port_info(port)) == "SFP":
            return "SFP"
        return "COPPER"

    def port_config(self, port: str) -> str:
        """
        ## Выводим конфигурацию порта

        Смотрим всю конфигурацию:

            # show running-config

        Затем возвращаем только для нужного порта

        :param port: Порт
        :return: Конфигурация порта либо пустая строка
        """
        running_config = self.send_command("show running-config")
        split_config = running_config.split("interface ")
        # Разделение конфигурации на список строк.
        # Каждая строка является частью конфигурации порта.
        for piece in split_config:
            # Проверяем, является ли интерфейс тем, который мы ищем.
            if piece.startswith(_interface_normal_view(port).lower()):
                return piece
        return ""

    def get_port_errors(self, port: str) -> str:
        """
        ## Выводим ошибки на порту

        Используем команду:

            # show interfaces counters {port}

        :param port: Порт для проверки на наличие ошибок
        """

        port = self.validate_port(port)
        if port is None:
            return "Неверный порт!"

        output = self.send_command(f"show interfaces counters {port}").split("\n")
        for line in output:
            if "Error" in line:
                return line

        return ""

    def set_description(self, port: str, desc: str) -> str:
        """
        ## Устанавливаем описание для порта предварительно очистив его от лишних символов

        Максимальная длина описания 64 символа

        Переходим в режим конфигурирования:

            # configure

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
        self.session.sendline("configure")
        self.session.sendline(f"interface {_interface_normal_view(port)}")

        if (
            desc == ""
        ):  # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            res = self.send_command("no description", expect_command=False)

        else:  # В другом случае, меняем описание на оборудовании
            res = self.send_command(f"description {desc}", expect_command=False)

        self.session.sendline("end")  # Выходим из режима редактирования
        if "Invalid parameter value/range" in res:
            return "Max length:64"  # По умолчанию у Edge-Core 64

        # Возвращаем строку с результатом работы и сохраняем конфигурацию
        return f'Description has been {"changed" if desc else "cleared"}. {self.save_config()}'
