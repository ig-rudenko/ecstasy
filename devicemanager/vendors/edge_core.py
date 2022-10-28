import re
from time import sleep
from functools import lru_cache
import pexpect
import textfsm
from .base import BaseDevice, TEMPLATE_FOLDER, _interface_normal_view


class EdgeCore(BaseDevice):
    """
    Для оборудования от производителя Edge-Core
    """

    prompt = r'\S+#$'
    space_prompt = '---More---'
    vendor = 'Edge-Core'
    mac_format = r'\S\S-'*5+r'\S\S'

    def get_interfaces(self) -> list:
        output = self.send_command('show interfaces status')
        with open(f'{TEMPLATE_FOLDER}/interfaces/edge_core.template', 'r', encoding='utf-8') as template_file:
            int_des_ = textfsm.TextFSM(template_file)
        result = int_des_.ParseText(output)  # Ищем интерфейсы
        return [
            [
                line[0],  # interface
                line[2].lower() if 'Up' in line[1].lower() else line[1].lower(),  # status
                line[3]  # desc
            ]
            for line in result if not line[0].startswith('V')
        ]

    def get_vlans(self) -> list:
        running_config = self.send_command('show running-config')
        interfaces = self.get_interfaces()
        split_config = running_config.split('interface ')
        int_vlan = {}
        for piece in split_config:
            if piece.startswith('ethernet'):
                vlans = []

                for v in re.findall(r'VLAN[ad ]*([\d,]*)', piece):
                    vlans.extend(v.split(','))

                int_vlan[self.find_or_empty(r'^ethernet \d+/\d+', piece)] = sorted(list(set(vlans)))

        for line in interfaces:
            line.append(int_vlan[_interface_normal_view(line[0]).lower()])

        return interfaces

    def save_config(self):
        self.session.sendline('copy running-config startup-config')
        self.session.sendline('\n')
        if self.session.expect([r'fail|err', self.prompt, pexpect.TIMEOUT]) == 1:
            return self.SAVED_OK
        return self.SAVED_ERR

    @staticmethod
    def validate_port(port: str):
        port = port.strip()
        if re.findall(r'^\S+ \d+/\d+$', port):
            return _interface_normal_view(port)

        return None

    def get_mac(self, port: str) -> list:
        port = self.validate_port(port)
        if port is None:
            return []

        output = self.send_command(f'show mac-address-table interface {port}')
        macs = re.findall(rf'({self.mac_format})\s+(\d+)', output)
        return [m[::-1] for m in macs]

    def reload_port(self, port: str, save_config=True) -> str:
        port = self.validate_port(port)
        if port is None:
            return 'Неверный порт!'

        self.session.sendline('configure')
        self.session.expect(self.prompt)
        self.session.sendline(f'interface {port}')
        self.session.sendline('shutdown')
        self.session.expect(self.prompt)
        sleep(1)
        self.session.sendline('no shutdown')
        self.session.expect(self.prompt)
        self.session.sendline('end')
        self.session.expect(self.prompt)

        s = self.save_config() if save_config else 'Without saving'
        return s

    def set_port(self, port: str, status: str, save_config=True) -> str:
        port = self.validate_port(port)
        if port is None:
            return 'Неверный порт!'

        self.session.sendline('configure')
        self.session.expect(self.prompt)
        self.session.sendline(f'interface {port}')
        self.session.expect(self.prompt)
        if status == 'up':
            self.session.sendline('no shutdown')
        elif status == 'down':
            self.session.sendline('shutdown')
        self.session.sendline('end')
        self.session.expect(self.prompt)

        r = self.session.before.decode(errors='ignore')
        s = self.save_config() if save_config else 'Without saving'
        return r + s

    @lru_cache
    def __get_port_info(self, port: str) -> str:
        port = self.validate_port(port)
        if port is None:
            return 'Неверный порт!'

        return self.send_command(f'show interfaces status {port}')

    def port_type(self, port: str) -> str:
        if self.find_or_empty(r'Port type: (\S+)', self.__get_port_info(port)) == 'SFP':
            return 'SFP'
        return 'COPPER'

    def port_config(self, port: str) -> str:
        running_config = self.send_command('show running-config')
        split_config = running_config.split('interface ')
        for piece in split_config:
            if piece.startswith(_interface_normal_view(port).lower()):
                return piece
        return ''

    def get_port_errors(self, port: str) -> str:
        port = self.validate_port(port)
        if port is None:
            return 'Неверный порт!'

        output = self.send_command(f'show interfaces counters {port}').split('\n')
        for line in output:
            if re.findall('Error', line):
                return line

        return ''

    def set_description(self, port: str, desc: str) -> str:
        desc = self.clear_description(desc)  # Очищаем описание

        # Переходим к редактированию порта
        self.session.sendline('configure')
        self.session.sendline(f'interface {_interface_normal_view(port)}')

        if desc == '':  # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            res = self.send_command('no description', expect_command=False)

        else:  # В другом случае, меняем описание на оборудовании
            res = self.send_command(f'description {desc}', expect_command=False)

        self.session.sendline('end')  # Выходим из режима редактирования
        if 'Invalid parameter value/range' in res:
            return 'Max length:64'  # По умолчанию у Edge-Core 64

        # Возвращаем строку с результатом работы и сохраняем конфигурацию
        return f'Description has been {"changed" if desc else "cleared"}. {self.save_config()}'
