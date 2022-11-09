import re
from time import sleep
from functools import lru_cache
import pexpect
import textfsm
from .base import BaseDevice, TEMPLATE_FOLDER, range_to_numbers, _interface_normal_view


class EltexBase(BaseDevice):
    """
    Для оборудования от производителя Eltex
    Промежуточный класс, используется, чтобы определить модель оборудования
    """

    prompt = r"\S+#\s*"
    space_prompt = (
        r"More: <space>,  Quit: q or CTRL\+Z, One line: <return> |"
        r"More\? Enter - next line; Space - next page; Q - quit; R - show the rest\."
    )
    vendor = "Eltex"

    def __init__(self, session: pexpect, ip: str, auth: dict, model=""):
        super().__init__(session, ip, auth, model)
        system = self.send_command("show system")
        self.mac = self.find_or_empty(r"System MAC [Aa]ddress:\s+(\S+)", system)
        self.model = self.find_or_empty(
            r"System Description:\s+(\S+)|System type:\s+Eltex (\S+)", system
        )
        self.model = self.model[0] or self.model[1]

    def save_config(self):
        pass

    def get_mac(self, port) -> list:
        pass

    def get_interfaces(self) -> list:
        pass

    def get_vlans(self) -> list:
        pass

    def reload_port(self, port: str, save_config=True) -> str:
        pass

    def set_port(self, port: str, status: str, save_config=True) -> str:
        pass

    def set_description(self, port: str, desc: str) -> str:
        pass


class EltexMES(BaseDevice):
    """
    Для оборудования от производителя Eltex модель MES

    Проверено для:
     - 2324
     - 3324
    """

    prompt = r"\S+#\s*$"
    space_prompt = (
        r"More: <space>,  Quit: q or CTRL\+Z, One line: <return> |"
        r"More\? Enter - next line; Space - next page; Q - quit; R - show the rest\."
    )
    _template_name = "eltex-mes"
    mac_format = r"\S\S:" * 5 + r"\S\S"
    vendor = "Eltex"

    def __init__(self, session: pexpect, ip: str, auth: dict, model="", mac=""):
        super().__init__(session, ip, auth, model)
        self.mac = mac
        inv = self.send_command("show inventory", expect_command=False)
        self.serialno = self.find_or_empty(r"SN: (\S+)", inv)

    def save_config(self):
        self.session.sendline("end")
        self.session.expect(self.prompt)
        for _ in range(3):  # Пробуем 3 раза, если ошибка
            self.session.sendline("write")
            self.session.expect("write")
            status = self.send_command("Y", expect_command=False)
            if "succeed" in status:
                return self.SAVED_OK

        return self.SAVED_ERR

    def get_interfaces(self) -> list:
        self.session.sendline("show interfaces description")
        self.session.expect("show interfaces description")
        output = ""
        while True:
            match = self.session.expect(
                [self.prompt, self.space_prompt, pexpect.TIMEOUT]
            )
            output += self.session.before.decode("utf-8").strip()
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
        with open(
            f"{TEMPLATE_FOLDER}/interfaces/{self._template_name}.template",
            "r",
            encoding="utf-8",
        ) as template_file:

            int_des_ = textfsm.TextFSM(template_file)
            result = int_des_.ParseText(output)  # Ищем интерфейсы

        return [
            [
                line[0],  # interface
                line[2].lower() if "up" in line[1].lower() else "admin down",  # status
                line[3],  # desc
            ]
            for line in result
            if not line[0].startswith("V")
        ]

    def get_vlans(self) -> list:
        result = []
        interfaces = self.get_interfaces()
        for line in interfaces:
            if not line[0].startswith("V"):
                output = self.send_command(
                    f"show running-config interface {_interface_normal_view(line[0])}",
                    expect_command=False,
                )
                vlans_group = re.findall(
                    r"vlan [ad ]*(\S*\d)", output
                )  # Строчки вланов
                port_vlans = []
                if vlans_group:
                    for v in vlans_group:
                        port_vlans += range_to_numbers(v)
                result.append(line + [port_vlans])
        return result

    def get_mac(self, port) -> list:
        mac_str = self.send_command(
            f"show mac address-table interface {_interface_normal_view(port)}"
        )
        return re.findall(rf"(\d+)\s+({self.mac_format})\s+\S+\s+\S+", mac_str)

    def reload_port(self, port, save_config=True) -> str:
        self.session.sendline("configure terminal")
        self.session.expect(r"#")
        self.session.sendline(f"interface {_interface_normal_view(port)}")
        self.session.sendline("shutdown")
        sleep(1)
        self.session.sendline("no shutdown")
        self.session.sendline("exit")
        self.session.expect(r"#")
        r = self.session.before.decode(errors="ignore")
        s = self.save_config() if save_config else "Without saving"
        return r + s

    def set_port(self, port, status, save_config=True):
        self.session.sendline("configure terminal")
        self.session.expect(r"\(config\)#")
        self.session.sendline(f"interface {_interface_normal_view(port)}")
        if status == "up":
            self.session.sendline("no shutdown")
        elif status == "down":
            self.session.sendline("shutdown")
        self.session.sendline("end")

        self.session.expect(r"#")
        self.session.sendline("write")
        self.session.sendline("Y")
        self.session.expect(r"#", timeout=15)
        r = self.session.before.decode(errors="ignore")
        s = self.save_config() if save_config else "Without saving"
        return r + s

    @lru_cache
    def get_port_info(self, port):
        """Общая информация о порте"""

        info = self.send_command(
            f"show interfaces advertise {_interface_normal_view(port)}"
        ).split("\n")
        html = ""
        for line in info:
            if "Preference" in line:
                break
            html += f"<p>{line}</p>"

        return html

    @lru_cache
    def _get_port_stats(self, port):
        return self.send_command(
            f"show interfaces {_interface_normal_view(port)}"
        ).split("\n")

    def port_type(self, port) -> str:
        """Определяем тип порта: медь, оптика или комбо"""

        port_type = self.find_or_empty(r"Type: (\S+)", self.get_port_info(port))
        if "Fiber" in port_type:
            return "SFP"
        if "Copper" in port_type:
            return "COPPER"
        if "Combo-F" in port_type:
            return "COMBO-FIBER"
        if "Combo-C" in port_type:
            return "COMBO-COPPER"
        return "?"

    def port_config(self, port: str) -> str:
        """Конфигурация порта"""
        return self.send_command(
            f"show running-config interface {_interface_normal_view(port)}"
        ).strip()

    def get_port_errors(self, port: str) -> str:
        """Ошибки на порту"""

        port_info = self._get_port_stats(port)
        errors = []
        for line in port_info:
            if "error" in line:
                errors.append(line.strip())
        return "\n".join(errors)

    def set_description(self, port: str, desc: str) -> str:
        desc = self.clear_description(desc)  # Очищаем описание

        # Переходим к редактированию порта
        self.session.sendline("configure terminal")
        self.session.expect(self.prompt)
        self.session.sendline(f"interface {_interface_normal_view(port)}")
        self.session.expect(self.prompt)

        if desc == "":
            # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            res = self.send_command("no description", expect_command=False)

        else:  # В другом случае, меняем описание на оборудовании
            res = self.send_command(f"description {desc}", expect_command=False)

        if "bad parameter value" in res:
            # Если длина описания больше чем доступно на оборудовании
            output = self.send_command("description ?")
            return "Max length:" + self.find_or_empty(
                r" Up to (\d+) characters", output
            )

        # Возвращаем строку с результатом работы и сохраняем конфигурацию
        return f'Description has been {"changed" if desc else "cleared"}. {self.save_config()}'


class EltexESR(EltexMES):
    _template_name = "eltex-esr"

    def __init__(self, session: pexpect, ip: str, auth: dict, model="", mac=""):
        self.session: pexpect = session
        self.ip: str = ip
        self.auth: dict = auth
        self.model: str = model
        self.mac: str = mac
        system = self.send_command("show system")
        self.serialno: str = self.find_or_empty(r"serial number:\s+(\S+)", system)

    def save_config(self):
        """Для ESR необходимо сделать коммит конфигурации, а затем подтвердить её"""

        self.session.sendline("commit")
        if (
            self.session.expect(
                [
                    self.prompt,  # 0
                    "Configuration has been successfully applied",  # 1
                    "Unknown command",  # 2
                ]
            )
            == 2  # Если неверная команда
        ):
            # Выходим из режима редактирования конфигурации
            self.session.sendline("end")
            self.session.sendline("commit")
            self.session.expect(
                [self.prompt, "Configuration has been successfully applied"]
            )

        # Подтверждаем изменение
        status = self.send_command("confirm")
        if "Configuration has been confirmed" in status:
            return self.SAVED_OK
        return self.SAVED_ERR

    def port_type(self, port: str) -> str:
        if "SFP present" in self.send_command(
            f"show interfaces sfp {_interface_normal_view(port)}"
        ):
            return "SFP"
        return "COPPER"

    def get_port_info(self, port: str):
        return self.send_command(
            f"show interfaces status {_interface_normal_view(port)}",
            expect_command=False,
            before_catch=r"Description:.+",
        ).replace("\n", "<br>")

    def get_port_errors(self, port: str) -> str:
        port_stat = self.send_command(
            f"show interfaces counters {_interface_normal_view(port)}"
        ).split("\n")

        errors = ""
        for line in port_stat:
            if "errors" in line:
                errors += line.strip() + "\n"
        return errors
