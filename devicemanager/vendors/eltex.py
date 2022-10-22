import re
from time import sleep
from functools import lru_cache
import pexpect
import textfsm
from .base import BaseDevice, TEMPLATE_FOLDER, _range_to_numbers, _interface_normal_view


class EltexBase(BaseDevice):
    """
    Для оборудования от производителя Eltex
    Промежуточный класс, используется, чтобы определить модель оборудования
    """

    prompt = r'\S+#\s*'
    space_prompt = r"More: <space>,  Quit: q or CTRL\+Z, One line: <return> |" \
                   r"More\? Enter - next line; Space - next page; Q - quit; R - show the rest\."
    vendor = 'Eltex'

    def __init__(self, session: pexpect, ip: str, auth: dict, model=''):
        super().__init__(session, ip, auth, model)
        system = self.send_command('show system')
        self.mac = self.find_or_empty(r'System MAC [Aa]ddress:\s+(\S+)', system)
        self.model = self.find_or_empty(r'System Description:\s+(\S+)|System type:\s+Eltex (\S+)', system)
        self.model = self.model[0] or self.model[1]

    def save_config(self):
        pass

    def get_mac(self, port) -> list:
        pass

    def get_interfaces(self) -> list:
        pass

    def get_vlans(self) -> list:
        pass

    def reload_port(self, port: str) -> str:
        pass

    def set_port(self, port: str, status: str) -> str:
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

    prompt = r'\S+#\s*'
    space_prompt = r"More: <space>,  Quit: q or CTRL\+Z, One line: <return> |" \
                   r"More\? Enter - next line; Space - next page; Q - quit; R - show the rest\."
    _template_name = 'eltex-mes'
    mac_format = r'\S\S:' * 5 + r'\S\S'
    vendor = 'Eltex'

    def __init__(self, session: pexpect, ip: str, auth: dict, model='', mac=''):
        super().__init__(session, ip, auth, model)
        self.mac = mac
        inv = self.send_command('show inventory')
        self.serialno = self.find_or_empty(r'SN: (\S+)', inv)

    def save_config(self):
        self.session.sendline('end')
        self.session.expect(self.prompt)
        for _ in range(3):  # Пробуем 3 раза, если ошибка
            self.session.sendline('write')
            self.session.expect('write')
            status = self.send_command('Y', expect_command=False)
            if 'succeed' in status:
                return self.SAVED_OK

        return self.SAVED_ERR

    def get_interfaces(self) -> list:
        self.session.sendline("show int des")
        self.session.expect("show int des")
        output = ''
        while True:
            match = self.session.expect([self.prompt, self.space_prompt, pexpect.TIMEOUT])
            output += self.session.before.decode('utf-8').strip()
            if 'Ch       Port Mode (VLAN)' in output:
                self.session.sendline('q')
                self.session.expect(self.prompt)
                break
            if match == 0:
                break
            elif match == 1:
                self.session.send(" ")
            else:
                print(self.ip, "Ошибка: timeout")
                break
        with open(f'{TEMPLATE_FOLDER}/interfaces/{self._template_name}.template', 'r') as template_file:
            int_des_ = textfsm.TextFSM(template_file)
            result = int_des_.ParseText(output)  # Ищем интерфейсы
        return [
            [
                line[0],  # interface
                line[2].lower() if 'up' in line[1].lower() else 'admin down',  # status
                line[3]  # desc
            ]
            for line in result if not line[0].startswith('V')
        ]

    def get_vlans(self) -> list:
        result = []
        interfaces = self.get_interfaces()
        for line in interfaces:
            if not line[0].startswith('V'):
                output = self.send_command(
                    f'show running-config interface {_interface_normal_view(line[0])}', expect_command=False
                )
                vlans_group = re.findall(r'vlan [ad ]*(\S*\d)', output)  # Строчки вланов
                port_vlans = []
                if vlans_group:
                    for v in vlans_group:
                        port_vlans += _range_to_numbers(v)
                result.append(line + [port_vlans])
        return result

    def get_mac(self, port) -> list:
        mac_str = self.send_command(f'show mac address-table interface {_interface_normal_view(port)}')
        return re.findall(rf'(\d+)\s+({self.mac_format})\s+\S+\s+\S+', mac_str)

    def reload_port(self, port) -> str:
        self.session.sendline('configure terminal')
        self.session.expect(r'#')
        self.session.sendline(f'interface {_interface_normal_view(port)}')
        self.session.sendline('shutdown')
        sleep(1)
        self.session.sendline('no shutdown')
        self.session.sendline('exit')
        self.session.expect(r'#')
        r = self.session.before.decode(errors='ignore')
        s = self.save_config()
        return r + s

    def set_port(self, port, status):
        self.session.sendline('configure terminal')
        self.session.expect(r'\(config\)#')
        self.session.sendline(f'interface {_interface_normal_view(port)}')
        if status == 'up':
            self.session.sendline('no shutdown')
        elif status == 'down':
            self.session.sendline('shutdown')
        self.session.sendline('end')

        self.session.expect(r'#')
        self.session.sendline('write')
        self.session.sendline('Y')
        self.session.expect(r'#', timeout=15)
        r = self.session.before.decode(errors='ignore')
        s = self.save_config()
        return r + s

    @lru_cache
    def get_port_info(self, port):
        """Общая информация о порте"""

        info = self.send_command(f'show interfaces advertise {_interface_normal_view(port)}').split('\n')
        html = ''
        for line in info:
            if 'Preference' in line:
                break
            html += f'<p>{line}</p>'

        return html

    def port_type(self, port):
        """Определяем тип порта: медь, оптика или комбо"""

        port_type = self.find_or_empty(r'Type: (\S+)', self.get_port_info(port))
        if 'Fiber' in port_type:
            return 'SFP'
        elif 'Copper' in port_type:
            return 'COPPER'
        elif 'Combo-F' in port_type:
            return 'COMBO-FIBER'
        elif 'Combo-C' in port_type:
            return 'COMBO-COPPER'

    def port_config(self, port):
        """Конфигурация порта"""
        return self.send_command(f'show running-config interface {_interface_normal_view(port)}').strip()

    def set_description(self, port: str, desc: str) -> str:
        desc = self.clear_description(desc)  # Очищаем описание

        # Переходим к редактированию порта
        self.session.sendline('configure terminal')
        self.session.expect(self.prompt)
        self.session.sendline(f'interface {_interface_normal_view(port)}')
        self.session.expect(self.prompt)

        if desc == '':  # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            res = self.send_command(f'no description', expect_command=False)

        else:  # В другом случае, меняем описание на оборудовании
            res = self.send_command(f'description {desc}', expect_command=False)

        if 'bad parameter value' in res:
            # Если длина описания больше чем доступно на оборудовании
            output = self.send_command('description ?')
            return 'Max length:' + self.find_or_empty(r' Up to (\d+) characters', output)

        # Возвращаем строку с результатом работы и сохраняем конфигурацию
        return f'Description has been {"changed" if desc else "cleared"}. {self.save_config()}'


class EltexESR(EltexMES):
    _template_name = 'eltex-esr'

    def __init__(self, session: pexpect, ip: str, auth: dict, model='', mac=''):
        super().__init__(session, ip, auth, model)
        system = self.send_command('show system')
        self.mac = mac
        self.serialno = self.find_or_empty(r'serial number:\s+(\S+)', system)

