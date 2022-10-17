import re
from time import sleep
import pexpect
import textfsm
from .base import BaseDevice, TEMPLATE_FOLDER, _range_to_numbers


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
        if self.session.expect([self.prompt, r'[Ss]uccess']):
            return self.SAVED_OK
        return self.SAVED_ERR

    def send_command(self, command: str, before_catch: str = None, expect_command=False, num_of_expect=10,
                     space_prompt=None, prompt=None, pages_limit=None):
        return super(Dlink, self).send_command(
            command,
            before_catch=before_catch or command, expect_command=expect_command, num_of_expect=num_of_expect,
            space_prompt=space_prompt, prompt=prompt, pages_limit=pages_limit
        )

    def get_interfaces(self) -> list:
        self.session.sendline("show ports des")
        self.session.expect('#')
        output = self.session.before.decode('utf-8')
        with open(f'{TEMPLATE_FOLDER}/interfaces/d-link.template', 'r') as template_file:
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
        with open(f'{TEMPLATE_FOLDER}/vlans_templates/d-link.template', 'r') as template_file:
            vlan_templ = textfsm.TextFSM(template_file)
            result_vlan = vlan_templ.ParseText(output)
        # сортируем и выбираем уникальные номера портов из списка интерфейсов
        port_num = set(sorted([int(re.findall(r'\d+', p[0])[0]) for p in interfaces]))

        # Создаем словарь, где ключи это кол-во портов, а значениями будут вланы на них
        ports_vlan = {str(num): [] for num in range(1, len(port_num) + 1)}

        for vlan in result_vlan:
            for port in _range_to_numbers(vlan[2]):
                # Добавляем вланы на порты
                ports_vlan[str(port)].append(vlan[0])
        interfaces_vlan = []  # итоговый список (интерфейсы и вланы)
        for line in interfaces:
            interfaces_vlan.append(line + [ports_vlan.get(line[0], '')])
        return interfaces_vlan

    def get_mac(self, port) -> list:
        port = re.sub(r'\D', '', port)

        mac_str = self.send_command(f'show fdb port {port}', expect_command=False)
        return re.findall(rf'(\d+)\s+\S+\s+({self.mac_format})\s+\d+\s+\S+', mac_str)

    @staticmethod
    def validate_port(port: str):
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

    def reload_port(self, port) -> str:
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
        s = self.save_config()
        return r1 + r2 + s

    def get_port_errors(self, port):
        port = self.validate_port(port)
        if port is None:
            return 'Неверный порт'
        return self.send_command(f'show error ports {port}')

    def set_port(self, port, status) -> str:
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
        s = self.save_config()
        return r + s

    def set_description(self, port: str, desc: str) -> str:
        pass

