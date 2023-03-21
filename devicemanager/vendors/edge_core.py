import re
from time import sleep
from functools import lru_cache, wraps
import pexpect
import textfsm
from .base import (
    BaseDevice,
    TEMPLATE_FOLDER,
    interface_normal_view,
    T_InterfaceList,
    T_InterfaceVLANList,
    T_MACList,
)


# noinspection PyArgumentList
class EdgeCore(BaseDevice):
    """
    # Для оборудования от производителя Edge-Core
    """

    prompt = r"\S+#$"
    space_prompt = "---More---"
    vendor = "Edge-Core"
    mac_format = r"\S\S-" * 5 + r"\S\S"

    def _validate_port(self=None, if_invalid_return=None):
        """
        ## Декоратор для проверки правильности порта Edge Core

        :param if_invalid_return: что нужно вернуть, если порт неверный
        """

        if if_invalid_return is None:
            if_invalid_return = "Неверный порт"

        def validate(func):
            @wraps(func)
            def __wrapper(self, port, *args, **kwargs):
                port = interface_normal_view(port.strip())
                if not port:
                    # Неверный порт
                    return if_invalid_return

                # Вызываем метод
                return func(self, port, *args, **kwargs)

            return __wrapper

        return validate

    @BaseDevice._lock
    def get_interfaces(self) -> T_InterfaceList:
        """
        ## Возвращаем список всех интерфейсов на устройстве

        Команда на оборудовании:

            # show interfaces status

        :return: ```[ ('name', 'status', 'desc'), ... ]```
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

    @BaseDevice._lock
    def get_vlans(self) -> T_InterfaceVLANList:
        """
        ## Возвращаем список всех интерфейсов и его VLAN на коммутаторе.

        Для начала получаем список всех интерфейсов через метод **get_interfaces()**

        Затем для каждого интерфейса смотрим конфигурацию и выбираем строчки,
        в которых указаны VLAN:

         - ```VLAN {vid}```
         - ```VLAN add {vid},{vid},...{vid}```

        :return: ```[ ('name', 'status', 'desc', ['{vid}', '{vid},{vid},...{vid}', ...] ), ... ]```
        """

        # Получение текущей конфигурации устройства.
        running_config = self.send_command("show running-config")
        self.lock = False
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
                    set(vlans)
                )

        # Распаковка кортежа `line` и добавление кортежа `vlans` в конец нового кортежа.
        # Создание списка кортежей.
        interfaces_vlans = [
            (
                line[0],  # Интерфейс
                line[1],  # Статус
                line[2],  # Описание
                int_vlan[interface_normal_view(line[0]).lower()],  # Добавляем VLANs
            )
            for line in interfaces
        ]

        return interfaces_vlans

    @BaseDevice._lock
    def save_config(self):
        """
        ## Сохраняем конфигурацию оборудования командой:

            # copy running-config startup-config
            # \n -- подтверждаем

        Ожидаем ответа от оборудования.
        Если **fail** или **error** - ошибка сохранения, иначе сохранено
        """

        self.session.sendline("copy running-config startup-config")
        self.session.sendline("\n")
        if self.session.expect([r"fail|err", self.prompt, pexpect.TIMEOUT]) == 1:
            return self.SAVED_OK
        return self.SAVED_ERR

    @BaseDevice._lock
    @_validate_port(if_invalid_return=[])
    def get_mac(self, port: str) -> T_MACList:
        """
        ## Возвращаем список из VLAN и MAC-адреса для данного порта.

        Команда на оборудовании:

            # show mac address-table interface {port}

        :param port: Номер порта коммутатора
        :return: ```[ ('vid', 'mac'), ... ]```
        """

        output = self.send_command(f"show mac-address-table interface {port}")
        macs = re.findall(rf"({self.mac_format})\s+(\d+)", output)
        return [m[::-1] for m in macs]

    @BaseDevice._lock
    @_validate_port()
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

        self.lock = False
        s = self.save_config() if save_config else "Without saving"
        return s

    @BaseDevice._lock
    @_validate_port()
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

        self.lock = False
        s = self.save_config() if save_config else "Without saving"
        return r + s

    @_validate_port()
    @lru_cache
    @BaseDevice._lock
    def __get_port_info(self, port: str) -> str:
        """
        ## Возвращает информацию о порте.

            # show interfaces status {port}

        Если переданный порт неверный, то вернет ```"Неверный порт!"```

        :param port: Номер порта, для которого требуется получить информацию
        """

        return self.send_command(f"show interfaces status {port}")

    @_validate_port()
    def get_port_info(self, port: str) -> dict:
        """
        ## Возвращает информацию о порте

            # show interfaces status {port}

        Если переданный порт неверный, то вернет ```"Неверный порт!"```

        :param port: Номер порта, для которого требуется получить информацию
        """

        return {
            "type": "text",
            "data": self.__get_port_info(port).strip(),
        }

    @_validate_port()
    def get_port_type(self, port: str) -> str:
        """
        # Возвращает тип порта

        :param port: Порт для проверки
        :return: "SFP", "COPPER", "COMBO-SFP", "COMBO-COPPER"
        """
        port_type_result = ""
        # Нахождение режима комбо.
        combo_mode = self.find_or_empty(
            "Combo forced mode: (.+)", self.__get_port_info(port)
        )

        if combo_mode != "None":
            # Код проверяет, является ли тип порта комбинированным портом.
            port_type_result += "COMBO-"

        # Получение типа порта.
        port_type = self.find_or_empty(r"Port type: (\S+)", self.__get_port_info(port))

        if "SFP" in port_type:
            port_type_result += "SFP"
        else:
            port_type_result += "COPPER"

        return port_type_result

    @BaseDevice._lock
    @_validate_port()
    def get_port_config(self, port: str) -> str:
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
            if piece.startswith(port.lower()):
                # Удаление "!" из переменной port_config.
                port_config = "\n".join(
                    [
                        line
                        for line in piece.split("\n")
                        if not line.strip().startswith("!") and line
                    ]
                )
                return "interface " + port_config
        return ""

    @BaseDevice._lock
    @_validate_port()
    def get_port_errors(self, port: str) -> str:
        """
        ## Выводим ошибки на порту

        Используем команду:

            # show interfaces counters {port}

        :param port: Порт для проверки на наличие ошибок
        """

        output = self.send_command(f"show interfaces counters {port}").split("\n")
        for line in output:
            if "Error" in line:
                return line

        return ""

    @BaseDevice._lock
    @_validate_port()
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
        self.session.sendline(f"interface {port}")

        if (
            desc == ""
        ):  # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            res = self.send_command("no description", expect_command=False)

        else:  # В другом случае, меняем описание на оборудовании
            res = self.send_command(f"description {desc}", expect_command=False)

        self.session.sendline("end")  # Выходим из режима редактирования
        if "Invalid parameter value/range" in res:
            return "Max length:64"  # По умолчанию у Edge-Core 64

        self.lock = False
        # Возвращаем строку с результатом работы и сохраняем конфигурацию
        return f'Description has been {"changed" if desc else "cleared"}. {self.save_config()}'

    def get_device_info(self) -> dict:
        pass
