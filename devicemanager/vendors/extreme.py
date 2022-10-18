import re
from time import sleep
import pexpect
import textfsm
from .base import BaseDevice, TEMPLATE_FOLDER, _range_to_numbers


class Extreme(BaseDevice):
    """
    Для оборудования от производителя Extreme

    Проверено для:
     - X460
     - X670
    """

    prompt = r'\S+\s*#\s*$'
    space_prompt = "Press <SPACE> to continue or <Q> to quit:"
    mac_format = r'\S\S:' * 5 + r'\S\S'
    vendor = 'Extreme'

    def __init__(self, session: pexpect, ip: str, auth: dict, model=''):
        super().__init__(session, ip, auth, model)
        system = self.send_command('show switch')
        self.mac = self.find_or_empty(r'System MAC:\s+(\S+)', system)
        self.model = self.find_or_empty(r'System Type:\s+(\S+)', system)
        version = self.send_command('show version')
        self.serialno = self.find_or_empty(r'Switch\s+: \S+ (\S+)', version)

    def save_config(self):
        self.session.sendline('save')
        self.session.sendline('y')
        if self.session.expect([self.prompt, r'successfully']):
            return self.SAVED_OK
        return self.SAVED_ERR

    def get_interfaces(self) -> list:
        # LINKS
        output_links = self.send_command('show ports information')
        with open(f'{TEMPLATE_FOLDER}/interfaces/extreme_links.template', 'r') as template_file:
            int_des_ = textfsm.TextFSM(template_file)
            result_port_state = int_des_.ParseText(output_links)  # Ищем интерфейсы
        for position, line in enumerate(result_port_state):
            if result_port_state[position][1].startswith('D'):
                result_port_state[position][1] = 'Disable'
            elif result_port_state[position][1].startswith('E'):
                result_port_state[position][1] = 'Enable'
            else:
                result_port_state[position][1] = 'None'

        # DESC
        output_des = self.send_command('show ports description')

        with open(f'{TEMPLATE_FOLDER}/interfaces/extreme_des.template', 'r') as template_file:
            int_des_ = textfsm.TextFSM(template_file)
            result_des = int_des_.ParseText(output_des)  # Ищем desc

        result = [result_port_state[n] + result_des[n] for n in range(len(result_port_state))]
        return [
            [
                line[0],  # interface
                line[2].replace('ready', 'down').replace('active', 'up') if 'Enable' in line[1] else 'admin down',
                # status
                line[3]  # desc
            ]
            for line in result
        ]

    def get_vlans(self):
        """Смотрим интерфейсы и VLAN на них"""

        interfaces = self.get_interfaces()

        for i, line in enumerate(interfaces, start=1):
            print(i, line)

        output_vlans = self.send_command('show configuration "vlan"', before_catch=r'Module vlan configuration\.')

        with open(f'{TEMPLATE_FOLDER}/vlans_templates/extreme.template', 'r') as template_file:
            vlan_templ = textfsm.TextFSM(template_file)
            result_vlans = vlan_templ.ParseText(output_vlans)

        # Создаем словарь, где ключи это порты, а значениями будут вланы на них
        ports_vlan = {num: [] for num in range(1, len(interfaces) + 1)}

        print(ports_vlan)

        for vlan in result_vlans:
            print('--------------', vlan)
            for port in _range_to_numbers(vlan[1]):
                print('++++', port)
                # Добавляем вланы на порты
                ports_vlan[port].append(vlan[0])

        interfaces_vlan = []  # итоговый список (интерфейсы и вланы)
        for line in interfaces:
            interfaces_vlan.append(line + [ports_vlan.get(int(line[0]), '')])

        return interfaces_vlan

    @staticmethod
    def validate_port(port: str):
        """
        Проверяем правильность полученного порта
        Для Extreme порт должен быть числом
        """

        port = port.strip()
        if port.isdigit():
            return port

    def get_mac(self, port: str) -> list:
        """
        Смотрим MAC'и на порту и отдаем в виде списка

        [ ["vlan", "mac"],  ... ]
        """
        port = self.validate_port(port)
        if port is None:
            return []

        output = self.send_command(f'show fdb ports {port}', expect_command=False)
        macs = re.findall(rf'({self.mac_format})\s+v(\d+)', output)

        res = []
        print(macs)
        for m in macs:
            res.append(m[::-1])
        return res

    def get_port_errors(self, port: str):
        """Смотрим ошибки на порту"""

        port = self.validate_port(port)
        if port is None:
            return ''
        rx_errors = self.send_command(f'show ports {port} rxerrors no-refresh')
        tx_errors = self.send_command(f'show ports {port} txerrors no-refresh')

        return rx_errors + '\n' + tx_errors

    def reload_port(self, port) -> str:
        """Перезагружаем порт и сохраняем конфигурацию"""

        if not self.validate_port(port):
            return f'Неверный порт! {port}'

        self.session.sendline(f'disable ports {port}')
        self.session.expect(self.prompt)
        sleep(1)
        self.session.sendline(f'enable ports {port}')
        self.session.expect(self.prompt)
        r = self.session.before.decode(errors='ignore')
        s = self.save_config()
        return r + s

    def set_port(self, port: str, status: str) -> str:
        """Меням состояние порта и сохраняем конфигурацию"""

        if not self.validate_port(port):
            return f'Неверный порт! {port}'

        if status == 'up':
            cmd = 'enable'
        elif status == 'down':
            cmd = 'disable'
        else:
            cmd = ''

        self.session.sendline(f'{cmd} ports {port}')
        self.session.expect(self.prompt)
        r = self.session.before.decode(errors='ignore')
        s = self.save_config()
        return r + s

    def port_type(self, port):
        """Определяем тип порта: медь, оптика или комбо"""

        port = self.validate_port(port)
        if port is None:
            return f'Неверный порт'

        if 'Media Type' in self.send_command(f'show ports {port} transceiver information detail | include Media'):
            return 'SFP'
        else:
            return 'COPPER'

    def set_description(self, port: str, desc: str) -> str:
        port = self.validate_port(port)
        if port is None:
            return 'Неверный порт'

        desc = self.clear_description(desc)  # Очищаем описание от лишних символов

        if desc == '':  # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            self.send_command(f'unconfigure ports 11 description-string', expect_command=False)

        else:  # В другом случае, меняем описание на оборудовании
            self.send_command(f'configure ports {port} description-string {desc}', expect_command=False)

        # Возвращаем строку с результатом работы и сохраняем конфигурацию
        return f'Description has been {"changed" if desc else "cleared"}. {self.save_config()}'
