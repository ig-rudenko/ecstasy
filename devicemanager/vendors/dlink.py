import re
from time import sleep
import pexpect
import textfsm
from .base import BaseDevice, TEMPLATE_FOLDER, range_to_numbers


class Dlink(BaseDevice):
    """
    Для оборудования от производителя D-Link

    Проверено для:
     - DES-1228
     - DES-3028
     - DES-3200
     - DES-3526
     - DGS-1210
     - DGS-3420
    """

    prompt = r'\S+#'
    space_prompt = None
    mac_format = r'\S\S-'*5+r'\S\S'
    vendor = 'D-Link'

    def __init__(self, session: pexpect, ip: str, auth: dict, model: str = ''):
        super().__init__(session, ip, auth, model)

        status = True
        self.session.sendline('enable admin')  # Повышает уровень привилегий до уровня администратора
        if not session.expect(
                [
                    "[Pp]ass",  # 0 - ввод пароля
                    r"You already have"  # 1 - уже администратор
                ]
        ):
            self.session.sendline(self.auth['privilege_mode_password'])  # Вводим пароль администратора
        while self.session.expect([self.prompt, 'Fail!']):
            self.session.sendline('\n')
            print(self.ip, 'privilege_mode_password wrong!')
            status = False
        if status:
            self.session.sendline('disable clipaging')  # отключение режима постраничного вывода
            self.session.expect(self.prompt)

        # Уровень администратора
        self._admin_status: bool = status

        # Смотрим характеристики устройства
        version = self.send_command('show switch')
        self.mac = self.find_or_empty(r'MAC Address\s+:\s+(\S+-\S+-\S+-\S+-\S+-\S+)', version)
        self.model = self.model or self.find_or_empty(r'Device Type\s+:\s+(\S+)\s', version)
        self.serialno = self.find_or_empty(r'Serial Number\s+:\s+(\S+)', version)

    def save_config(self):
        self.session.sendline('save')
        if self.session.expect([self.prompt, r'[Ss]uccess|[Dd]one']):
            return self.SAVED_OK
        return self.SAVED_ERR

    def send_command(self, command: str, before_catch: str = None, expect_command=False, num_of_expect=10,
                     space_prompt=None, prompt=None, pages_limit=None):
        return super().send_command(
            command,
            before_catch=before_catch or command, expect_command=expect_command, num_of_expect=num_of_expect,
            space_prompt=space_prompt, prompt=prompt, pages_limit=pages_limit
        )

    def get_interfaces(self) -> list:
        self.session.sendline("show ports des")
        self.session.expect('#')
        output = self.session.before.decode('utf-8')
        with open(f'{TEMPLATE_FOLDER}/interfaces/d-link.template', 'r', encoding='utf-8') as template_file:
            int_des_ = textfsm.TextFSM(template_file)
            result = int_des_.ParseText(output)  # Ищем интерфейсы
        return [
            [
                line[0],  # interface
                re.sub(r'Link\s*?Down', 'down', line[2]) if 'Enabled' in line[1] else 'admin down',  # status
                line[3]  # desc
            ]
            for line in result
        ]

    def get_vlans(self) -> list:

        interfaces = self.get_interfaces()

        self.session.sendline('show vlan')
        self.session.expect(self.prompt, timeout=20)
        output = self.session.before.decode('utf-8')
        with open(f'{TEMPLATE_FOLDER}/vlans_templates/d-link.template', 'r', encoding='utf-8') as template_file:
            vlan_templ = textfsm.TextFSM(template_file)
            result_vlan = vlan_templ.ParseText(output)
        # сортируем и выбираем уникальные номера портов из списка интерфейсов
        port_num = set(sorted([int(re.findall(r'\d+', p[0])[0]) for p in interfaces]))

        # Создаем словарь, где ключи это кол-во портов, а значениями будут вланы на них
        ports_vlan = {str(num): [] for num in range(1, len(port_num) + 1)}

        for vlan in result_vlan:
            for port in range_to_numbers(vlan[2]):
                # Добавляем вланы на порты
                ports_vlan[str(port)].append(vlan[0])
        interfaces_vlan = []  # итоговый список (интерфейсы и вланы)
        for line in interfaces:
            interfaces_vlan.append(line + [ports_vlan.get(line[0], '')])
        return interfaces_vlan

    def get_mac(self, port) -> list:
        port = self.validate_port(port)

        if port is None:
            return []

        mac_str = self.send_command(f'show fdb port {port}', expect_command=False)
        return re.findall(rf'(\d+)\s+\S+\s+({self.mac_format})\s+\d+\s+\S+', mac_str)

    @staticmethod
    def validate_port(port: str) -> (str, None):
        """ Проверяем порт на валидность """

        port = port.strip()
        if re.findall(r'^\d/\d+$', port):
            # Если порт представлен в виде "1/2"
            port = re.sub(r'^\d/', '', port)  # Оставляем только "2"
        elif re.findall(r'\d+|\d+\s*\([FC]\)', port):
            port = re.sub(r'\D', '', port)
        else:
            port = ''
        if port.isdigit():
            return port

        return None

    def reload_port(self, port, save_config=True) -> str:
        if 'F' in port:
            media_type = ' medium_type fiber'
        elif 'C' in port:
            media_type = ' medium_type copper'
        else:
            media_type = ''

        port = self.validate_port(port)
        if port is None:
            return 'Неверный порт'

        r1 = self.send_command(f'config ports {port} {media_type} state disable')
        sleep(1)
        r2 = self.send_command(f'config ports {port} {media_type} state enable')
        s = self.save_config() if save_config else 'Without saving'
        return r1 + r2 + s

    def get_port_errors(self, port):
        port = self.validate_port(port)
        if port is None:
            return 'Неверный порт'
        self.session.sendline(f'show error ports {port}')

        # Если не удалось отключить clipaging
        if self.session.expect([self.prompt, 'Previous Page']):
            self.session.sendline('q')

        return self.session.before.decode()

    def set_port(self, port, status, save_config=True) -> str:
        if 'F' in port:
            media_type = 'medium_type fiber'
        elif 'C' in port:
            media_type = 'medium_type copper'
        else:
            media_type = ''

        port = self.validate_port(port)

        if port is None:
            return 'Неверный порт'

        if status == 'up':
            state = 'enable'
        elif status == 'down':
            state = 'disable'
        else:
            state = ''

        r = self.send_command(f'config ports {port} {media_type} state {state}')
        s = self.save_config() if save_config else 'Without saving'
        return r + s

    def set_description(self, port: str, desc: str) -> str:

        port = self.validate_port(port)
        if port is None:
            return 'Неверный порт'

        desc = self.clear_description(desc)  # Очищаем описание от лишних символов

        if desc == '':  # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            status = self.send_command(f'config ports {port} clear_description', expect_command=False, before_catch='desc')

        else:  # В другом случае, меняем описание на оборудовании
            status = self.send_command(f'config ports {port} description {desc}', expect_command=False, before_catch='desc')

        if 'Next possible completions' in status:
            # Если длина описания больше чем доступно на оборудовании
            return 'Max length:' + self.find_or_empty(r'<desc (\d+)>', status)

        if 'Success' in status:  # Успешно поменяли описание
            # Возвращаем строку с результатом работы и сохраняем конфигурацию
            return f'Description has been {"changed" if desc else "cleared"}. {self.save_config()}'

        # Уникальный случай
        return status

    def virtual_cable_test(self, port: str) -> dict:
        port = self.validate_port(port)
        if port is None:
            return {}

        diag_output = self.send_command(f'cable_diag ports {port}', expect_command=False)

        if 'Available commands' in diag_output:
            return {}

        result = {
            'len': '-',  # Length
            'status': '',  # Up, Down
            'pair1': {
                'status': '',  # Open, Short
                'len': ''  # Length
            },
            'pair2': {
                'status': '',
                'len': ''
            }
        }

        if 'No Cable' in diag_output:
            # Нет кабеля
            result['status'] = 'Empty'
            del result['pair1']
            del result['pair2']
            return result

        if re.findall(r'Link (Up|Down)\s+OK', diag_output):
            # Если статус OK
            match = self.find_or_empty(r'\s+\d+\s+\S+\s+Link (Up|Down)\s+OK\s+(\S+)', diag_output)
            if len(match) == 2:
                result['len'] = match[1]  # Длина
                result['status'] = match[0]  # Up или Down
                del result['pair1']
                del result['pair2']
        else:
            # C ошибкой
            result['status'] = self.find_or_empty(r'\s+\d+\s+\S+\s+Link (Up|Down)', diag_output)
            pair1 = self.find_or_empty(r'Pair1 (\S+)\s+at (\d+)', diag_output)
            pair2 = self.find_or_empty(r'Pair2 (\S+)\s+at (\d+)', diag_output)
            # Пара 1
            if pair1:
                result['pair1']['status'] = pair1[0].lower()  # Open, Short
                result['pair1']['len'] = pair1[1]  # Длина
            else:
                del result['pair1']

            # Пара 2
            if pair2:
                result['pair2']['status'] = pair2[0].lower()  # Open, Short
                result['pair2']['len'] = pair2[1]  # Длина
            else:
                del result['pair2']

        return result
