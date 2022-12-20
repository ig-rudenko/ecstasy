import re
from time import sleep
from functools import lru_cache, wraps
import textfsm
from .base import BaseDevice, TEMPLATE_FOLDER, InterfaceList, InterfaceVLANList, MACList


class Qtech(BaseDevice):
    """
    # Для оборудования от производителя Q-Tech

    Проверено для:
     - QSW-8200
    """

    prompt = r"\S+#$"
    space_prompt = "--More--"
    mac_format = r"\S\S-" * 5 + r"\S\S"
    vendor = "Q-Tech"

    def get_interfaces(self) -> InterfaceList:
        """
        ## Возвращаем список всех интерфейсов на устройстве

        Команда на оборудовании:

            # show interface ethernet status

        :return: ```[ ('name', 'status', 'desc'), ... ]```
        """

        output = self.send_command(
            command="show interface ethernet status", expect_command=False
        )
        output = re.sub(r"[\W\S]+\nInterface", "\nInterface", output)
        with open(
            f"{TEMPLATE_FOLDER}/interfaces/q-tech.template", "r", encoding="utf-8"
        ) as template_file:
            int_des_ = textfsm.TextFSM(template_file)
            result = int_des_.ParseText(output)  # Ищем интерфейсы
        return [
            (line[0], line[1].lower().replace("a-", "admin "), line[2])
            for line in result
        ]

    def get_vlans(self) -> InterfaceVLANList:
        """
        ## Возвращаем список всех интерфейсов и его VLAN на коммутаторе.

        Для начала получаем список всех интерфейсов через метод **get_interfaces()**

        Затем для каждого интерфейса смотрим конфигурацию

            # show running-config interface ethernet {port}

        И выбираем строчки, в которых указаны VLAN:

         - ```vlan {vid},{vid},...{vid}```
         - ```vlan add {vid},{vid},...{vid}```

        :return: ```[ ('name', 'status', 'desc', ['{vid}', '{vid},{vid},...{vid}', ...] ), ... ]```
        """

        result = []
        for line in self.get_interfaces():
            if not line[0].startswith("V"):
                output = self.send_command(
                    command=f"show running-config interface ethernet {line[0]}"
                )
                vlans_group = re.findall(
                    r"vlan [ad ]*(\S*\d)", output
                )  # Строчки вланов
                vlans = []
                for v in vlans_group:
                    vlans += v.split(";")
                result.append((line[0], line[1], line[2], vlans))

        return result

    def _validate_port(self=None, if_invalid_return=None):
        """
        ## Декоратор для проверки правильности порта Q-Tech

        valid ports:

            "1/2/1"
            "1/1/21"

        invalid ports:

            "23"
            "port12"

        :param if_invalid_return: что нужно вернуть, если порт неверный
        """

        if if_invalid_return is None:
            if_invalid_return = "Неверный порт"

        def validate(func):
            @wraps(func)
            def wrapper(self, port: str, *args, **kwargs):
                port = port.strip()
                if not re.match(r"^\d+/\d+/\d+$", port):
                    # Неверный порт
                    if isinstance(if_invalid_return, str):
                        return f"{if_invalid_return} {port}"
                    else:
                        return if_invalid_return

                # Вызываем метод
                return func(self, port, *args, **kwargs)

            return wrapper

        return validate

    @_validate_port(if_invalid_return=[])
    def get_mac(self, port: str) -> list:
        """
        ## Возвращаем список из VLAN и MAC-адреса для данного порта.

        Команда на оборудовании:

            # show mac-address-table interface ethernet {port}

        :param port: Номер порта коммутатора
        :return: ```[ ('vid', 'mac'), ... ]```
        """

        output = self.send_command(f"show mac-address-table interface ethernet {port}")
        macs = re.findall(rf"(\d+)\s+({self.mac_format})", output)
        return macs

    @_validate_port()
    def reload_port(self, port: str, save_config=True) -> str:
        """
        ## Перезагружает порт

        Переходим в режим конфигурирования:

            # config terminal

        Переходим к интерфейсу:

            (config)# interface ethernet {port}

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
        self.session.sendline(f"interface ethernet {port}")
        self.session.expect(self.prompt)
        self.session.sendline("shutdown")
        sleep(1)
        self.session.sendline("no shutdown")
        self.session.expect(self.prompt)
        self.session.sendline("end")

        r = self.session.before.decode(errors="ignore")
        s = self.save_config() if save_config else "Without saving"
        return r + s

    @_validate_port()
    def set_port(self, port, status, save_config=True):
        """
        ## Устанавливает статус порта на коммутаторе **up** или **down**

        Переходим в режим конфигурирования:
            # config terminal

        Переходим к интерфейсу:
            (config)# interface ethernet {port}

        Меняем состояние порта:
            (config-if)# {shutdown|no shutdown}

        Выходим из режима конфигурирования:
            (config-if)# end

        :param port: Порт
        :param status: "up" или "down"
        :param save_config: Если True, конфигурация будет сохранена на устройстве, defaults to True (optional)
        """

        self.session.sendline("config terminal")
        self.session.expect(self.prompt)
        self.session.sendline(f"interface ethernet {port}")
        self.session.expect(self.prompt)
        if status == "up":
            self.session.sendline("no shutdown")
        elif status == "down":
            self.session.sendline("shutdown")
        self.session.sendline("end")
        self.session.expect(self.prompt)

        self.session.before.decode(errors="ignore")
        s = self.save_config() if save_config else "Without saving"
        return s

    def save_config(self):
        """
        ## Сохраняем конфигурацию оборудования командой:

            # write
            Y

        Ожидаем ответа от оборудования **successful**,
        если нет, то ошибка сохранения
        """

        self.session.sendline("write")
        self.session.sendline("Y")
        if self.session.expect([self.prompt, "successful"]):
            return self.SAVED_OK
        return self.SAVED_ERR

    @lru_cache
    def __get_port_info(self, port):
        """Общая информация о порте"""

        port_type = self.send_command(f"show interface ethernet{port}")
        return f"<p>{port_type}</p>"

    @_validate_port()
    def get_port_info(self, port):
        """
        ## Возвращаем информацию о порте.

        Через команду:

            # show interface ethernet{port}

        :param port: Номер порта, для которого требуется получить информацию
        :return: Информация о порте или ```"Неверный порт {port}"```
        """

        return "<br>".join(self.__get_port_info(port).split("\n")[:10])

    @_validate_port(if_invalid_return="?")
    def get_port_type(self, port):
        """
        ## Возвращает тип порта

        :param port: Порт для проверки
        :return: "SFP", "COPPER" или "Неверный порт {port}"
        """

        port_type = self.find_or_empty(r"Hardware is (\S+)", self.__get_port_info(port))
        if "SFP" in port_type:
            return "SFP"

        return "COPPER"

    @_validate_port()
    def get_port_errors(self, port):
        """
        ## Выводим ошибки на порту

        :param port: Порт для проверки на наличие ошибок
        """

        result = []
        for line in self.__get_port_info(port).split("\n"):
            if "error" in line:
                result.append(line)

        return "\n".join(result)

    @_validate_port()
    def get_port_config(self, port):
        """
        ## Выводим конфигурацию порта

        Используем команду:

            # show running-config interface ethernet {port}
        """

        return self.send_command(f"show running-config interface ethernet {port}")

    @_validate_port()
    def set_description(self, port: str, desc: str) -> str:
        """
        ## Устанавливаем описание для порта предварительно очистив его от лишних символов

        Если длина описания больше допустимой, то вернется ```"Max length:{max_length}"```

        Переходим в режим конфигурирования:

            # config terminal

        Переходим к интерфейсу:

            (config)# interface ethernet {port}

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
        self.session.sendline("config terminal")
        self.session.expect(self.prompt)
        self.session.sendline(f"interface ethernet {port}")
        self.session.expect(self.prompt)

        if desc == "":
            # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            status = self.send_command("no description", expect_command=False)

        else:  # В другом случае, меняем описание на оборудовании
            status = self.send_command(f"description {desc}", expect_command=False)

        self.session.sendline("end")  # Выходим из режима редактирования

        if "is too large" in status:
            # Если длина описания больше чем доступно на оборудовании
            output = self.send_command("description ?")
            return "Max length:" + self.find_or_empty(r"<1-(\d+)>", output)

        # Возвращаем строку с результатом работы и сохраняем конфигурацию
        return f'Description has been {"changed" if desc else "cleared"}. {self.save_config()}'
