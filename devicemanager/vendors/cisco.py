import re
from time import sleep
from functools import lru_cache
import pexpect
import textfsm
from .base import BaseDevice, TEMPLATE_FOLDER, FIBER_TYPES, _interface_normal_view


class Cisco(BaseDevice):
    """
    Для оборудования от производителя Cisco

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

    prompt = r'\S+#$'
    space_prompt = r' --More-- '
    mac_format = r'\S\S\S\S\.\S\S\S\S\.\S\S\S\S'  # 0018.e7d3.1d43
    vendor = 'Cisco'

    def __init__(self, session: pexpect, ip: str, auth: dict, model: str = ''):
        super().__init__(session, ip, auth, model)
        version = self.send_command('show version')
        self.serialno = self.find_or_empty(r'System serial number\s+: (\S+)', version)
        self.mac = self.find_or_empty(r'[MACmac] [Aa]ddress\s+: (\S+)', version)

    def save_config(self):
        for _ in range(3):  # Пробуем 3 раза, если ошибка
            self.session.sendline('write')
            print('write')
            # self.session.expect(r'Building configuration')
            if self.session.expect([self.prompt, r'\[OK\]']):
                return self.SAVED_OK
        return self.SAVED_ERR

    def get_interfaces(self) -> list:
        output = self.send_command('show int des')
        output = re.sub('.+\nInterface', 'Interface', output)
        with open(f'{TEMPLATE_FOLDER}/interfaces/cisco.template', 'r') as template_file:
            int_des_ = textfsm.TextFSM(template_file)
            result = int_des_.ParseText(output)  # Ищем интерфейсы
        return [
            [
                line[0],  # interface
                line[2].lower() if 'up' in line[1].lower() else line[1].lower(),  # status
                line[3]  # desc
            ]
            for line in result if not line[0].startswith('V')
        ]

    def get_vlans(self) -> list:
        result = []
        for line in self.get_interfaces():
            if not line[0].startswith('V'):
                output = self.send_command(
                    command=f"show running-config interface {_interface_normal_view(line[0])}",
                    before_catch="Building configuration",
                    expect_command=False
                )
                vlans_group = re.findall(r'(?<=access|llowed) vlan [ad\s]*(\S*\d)', output)  # Строчки вланов
                result.append(line + [vlans_group])

        return result

    def get_mac(self, port) -> list:
        mac_str = self.send_command(
            f'show mac address-table interface {_interface_normal_view(port)}',
            expect_command=False
        )
        return re.findall(rf'(\d+)\s+({self.mac_format})\s+\S+\s+\S+', mac_str)

    def reload_port(self, port) -> str:
        self.session.sendline('configure terminal')
        self.session.expect(self.prompt)
        self.session.sendline(f'interface {_interface_normal_view(port)}')
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
        self.session.sendline('configure terminal')
        self.session.expect(self.prompt)
        self.session.sendline(f'interface {_interface_normal_view(port)}')
        self.session.expect(self.prompt)
        if status == 'up':
            self.session.sendline('no shutdown')
        elif status == 'down':
            self.session.sendline('shutdown')
        self.session.sendline('end')
        self.session.expect(self.prompt)

        r = self.session.before.decode(errors='ignore')
        s = self.save_config()
        return r + s

    @lru_cache
    def get_port_info(self, port):
        """Общая информация о порте"""

        port_type = self.send_command(
            f'show interfaces {_interface_normal_view(port)}', expect_command=False
        ).split('\r\n')

        media_type = [line for line in port_type if 'media' in line]
        return f'<p>{"".join(media_type)}</p>'

    def port_type(self, port):
        """Определяем тип порта: медь или оптика"""

        port_type = self.find_or_empty(r'[Bb]ase(\S{1,2})', self.get_port_info(port))
        if 'SFP' in self.get_port_info(port) or port_type in FIBER_TYPES:
            return 'SFP'

        return 'COPPER'

    def get_port_errors(self, port):
        output = self.send_command(
            f'show interfaces {_interface_normal_view(port)} | include error', expect_command=False
        ).split('\r\n')

        media_type = [line for line in output if 'errors' in line]
        return "<p>" + "\n".join(media_type) + "</p>"

    def port_config(self, port):
        """Конфигурация порта"""

        config = self.send_command(
            f'show running-config interface {_interface_normal_view(port)}',
            before_catch=r'Current configuration.+?\!'
        ).strip()
        return config

    def search_mac(self, mac_address: str):

        formatted_mac = '{}{}{}{}.{}{}{}{}.{}{}{}{}'.format(*mac_address.lower())

        match = self.send_command(f'show arp | include {formatted_mac}')

        # Форматируем вывод
        with open(f'{TEMPLATE_FOLDER}/arp_format/{self.vendor.lower()}.template') as template_file:
            template = textfsm.TextFSM(template_file)
        formatted_result = template.ParseText(match)

        return formatted_result

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

        self.session.sendline('end')  # Выходим из режима редактирования
        if 'Invalid input detected' in res:
            return 'Invalid input detected'

        # Возвращаем строку с результатом работы и сохраняем конфигурацию
        return f'Description has been {"changed" if desc else "cleared"}. {self.save_config()}'
