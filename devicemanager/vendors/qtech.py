import re
from time import sleep
from functools import lru_cache
import textfsm
from .base import BaseDevice, TEMPLATE_FOLDER


class Qtech(BaseDevice):
    """
    Для оборудования от производителя Q-Tech

    Проверено для:
     - QSW-8200
    """

    prompt = r'\S+#$'
    space_prompt = "--More--"
    mac_format = r'\S\S-'*5 + r'\S\S'
    vendor = 'Q-Tech'

    def get_interfaces(self) -> list:
        output = self.send_command(
            command='show interface ethernet status',
            expect_command=False
        )
        output = re.sub(r'[\W\S]+\nInterface', '\nInterface', output)
        with open(f'{TEMPLATE_FOLDER}/interfaces/q-tech.template', 'r') as template_file:
            int_des_ = textfsm.TextFSM(template_file)
            result = int_des_.ParseText(output)  # Ищем интерфейсы
        return [
            [
                line[0],
                line[1].lower().replace('a-', 'admin '),
                line[2]
            ]
            for line in result
        ]

    def get_vlans(self) -> list:
        result = []
        for line in self.get_interfaces():
            if not line[0].startswith('V'):
                output = self.send_command(
                    command=f"show running-config interface ethernet {line[0]}"
                )
                vlans_group = re.findall(r'vlan [ad ]*(\S*\d)', output)  # Строчки вланов
                vlans = []
                for v in vlans_group:
                    vlans += v.split(';')
                # switchport_mode = re.findall(r'switchport mode (\S+)', output)  # switchport mode

                result.append(line + [vlans])

        return result

    @staticmethod
    def validate_port(port: str):
        port = port.strip()
        if bool(re.findall(r'^\d+/\d+/\d+$', port)):
            return port

    def get_mac(self, port: str) -> list:
        """
        Поиск маков на порту
        :return: [ ('vid', 'mac'), ... ]
        """
        port = self.validate_port(port)
        if port is None:
            return []

        output = self.send_command(f'show mac-address-table interface ethernet {port}')
        macs = re.findall(rf'(\d+)\s+({self.mac_format})', output)
        return macs

    def reload_port(self, port: str) -> str:
        port = self.validate_port(port)
        if port is None:
            return f'Неверный порт {port}'

        self.session.sendline('configure terminal')
        self.session.expect(self.prompt)
        self.session.sendline(f'interface ethernet {port}')
        self.session.expect(self.prompt)
        self.session.sendline('shutdown')
        sleep(1)
        self.session.sendline('no shutdown')
        self.session.expect(self.prompt)
        self.session.sendline('end')

        r = self.session.before.decode(errors='ignore')
        s = self.save_config()
        return r + s

    def set_port(self, port, status):
        port = self.validate_port(port)
        if port is None:
            return f'Неверный порт {port}'

        self.session.sendline('config terminal')
        self.session.expect(self.prompt)
        self.session.sendline(f'interface ethernet {port}')
        self.session.expect(self.prompt)
        if status == 'up':
            self.session.sendline('no shutdown')
        elif status == 'down':
            self.session.sendline('shutdown')
        self.session.sendline('end')
        self.session.expect(self.prompt)

        self.session.before.decode(errors='ignore')
        s = self.save_config()
        return s

    def save_config(self):
        self.session.sendline('write')
        self.session.sendline('Y')
        if self.session.expect([self.prompt, 'successful']):
            return self.SAVED_OK
        return self.SAVED_ERR

    @lru_cache
    def __get_port_info(self, port):
        """Общая информация о порте"""

        port_type = self.send_command(f'show interface ethernet{port}')
        return f'<p>{port_type}</p>'

    def get_port_info(self, port):
        """Общая информация о порте"""
        port = self.validate_port(port)
        if port is None:
            return f'Неверный порт {port}'

        return '<br>'.join(self.__get_port_info(port).split('\n')[:10])

    def port_type(self, port):
        """Определяем тип порта: медь или оптика"""

        port = self.validate_port(port)
        if port is None:
            return f'Неверный порт {port}'

        port_type = self.find_or_empty(r'Hardware is (\S+)', self.__get_port_info(port))
        if 'SFP' in port_type:
            return 'SFP'

        return 'COPPER'

    def get_port_errors(self, port):

        port = self.validate_port(port)
        if port is None:
            return f'Неверный порт {port}'

        result = []
        for line in self.__get_port_info(port).split('\n'):
            if 'error' in line:
                result.append(line)

        return '\n'.join(result)

    def port_config(self, port):
        """Конфигурация порта"""

        port = self.validate_port(port)
        if port is None:
            return f'Неверный порт {port}'

        return self.send_command(f'show running-config interface ethernet {port}')

    def set_description(self, port: str, desc: str) -> str:
        pass