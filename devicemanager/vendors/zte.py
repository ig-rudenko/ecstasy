import re
from time import sleep
import pexpect
import textfsm
from .base import BaseDevice, TEMPLATE_FOLDER, COOPER_TYPES, FIBER_TYPES, _range_to_numbers


class ZTE(BaseDevice):
    """
    Для оборудования от производителя ZTE

    Проверено для:
     - ZXR10 2928E
     - ZXR10 2936-FI
     - ZXR10 2952E

    """

    prompt = r'\S+\(cfg\)#|\S+>'
    space_prompt = "----- more -----"
    mac_format = r'\S\S\.' * 5 + r'\S\S'  # e1.3f.45.d6.23.53
    vendor = 'ZTE'

    def __init__(self, session: pexpect, ip: str, auth: dict, model=''):
        super().__init__(session, ip, auth, model)
        version = self.send_command('show version')
        self.mac = self.find_or_empty(r'Mac Address: (\S+)', version)

        # Turning on privileged mode
        self.session.sendline('enable')
        match_ = self.session.expect([self.prompt, r'password', r'[Ss]imultaneous'])  # Если ещё не привилегированный
        if match_ == 1:
            self.session.sendline(self.auth.get('privilege_mode_password'))  # send secret
            if self.session.expect([r'refused', r'\(cfg\)#']):
                self.__privileged = True
            else:
                self.__privileged = False
        elif match_ == 2:
            self.__privileged = False
        else:
            self.__privileged = True

    def get_interfaces(self) -> list:
        output = self.send_command('show port')

        with open(f'{TEMPLATE_FOLDER}/interfaces/zte.template') as template_file:
            int_des_ = textfsm.TextFSM(template_file)
            result = int_des_.ParseText(output)  # Ищем интерфейсы
        return [
            [
                line[0],  # interface
                line[2] if 'enabled' in line[1] else 'admin down',  # status
                line[3]  # desc
            ]
            for line in result
        ]

    def get_vlans(self):
        interfaces = self.get_interfaces()
        output = self.send_command('show vlan')

        with open(f'{TEMPLATE_FOLDER}/vlans_templates/zte_vlan.template', 'r') as template_file:
            vlan_templ = textfsm.TextFSM(template_file)
            result_vlan = vlan_templ.ParseText(output)

        vlan_port = {}
        for vlan in result_vlan:
            # Если не нашли влан, или он деактивирован, то пропускаем
            if not vlan[0] or vlan[4] == "disabled":
                continue
            # Объединяем тегированные вланы и нетегированные в один список
            vlan_port[int(vlan[0])] = _range_to_numbers(','.join([vlan[2], vlan[3]]))

        interfaces_vlan = []  # итоговый список (интерфейсы и вланы)

        for line in interfaces:
            vlans = []  # Строка со списком VLANов с переносами
            for vlan_id in vlan_port:
                if int(line[0]) in vlan_port[vlan_id]:
                    vlans.append(vlan_id)
            interfaces_vlan.append(line + [vlans])
        return interfaces_vlan

    @staticmethod
    def validate_port(port):
        """
        Проверяем правильность полученного порта
        Для ZTE порт должен быть числом
        """

        port = str(port).strip()
        if port.isdigit():
            return port

    def get_mac(self, port: str) -> list:
        """
        Поиск маков на порту
        :return: [ ('vid', 'mac'), ... ]
        """

        port = self.validate_port(port)
        if port is None:
            return []

        output_macs = self.send_command(f'show fdb port {port} detail')
        mac_list = []
        for i in re.findall(rf'({self.mac_format})\s+(\d+)', output_macs):
            mac_list.append(i[::-1])

        return mac_list

    def save_config(self):
        self.session.sendline('saveconfig')
        if self.session.expect([r'please wait a minute', 'Command not found']):
            self.session.sendline('write')
            self.session.expect(r'please wait a minute')

        if self.session.expect([self.prompt, r'[Dd]one']):
            return self.SAVED_OK
        return self.SAVED_ERR

    def reload_port(self, port: str) -> str:
        if not self.__privileged:
            return 'Не привилегированный. Операция отклонена!'

        port = self.validate_port(port)
        if port is None:
            return 'Неверный порт!'

        self.session.sendline(f'set port {port} disable')
        sleep(1)
        self.session.sendline(f'set port {port} enable')
        return f'reset port {port} ' + self.save_config()

    def set_port(self, port: str, status: str) -> str:
        if not self.__privileged:
            return 'Не привилегированный. Операция отклонена!'

        port = self.validate_port(port)
        if port is None:
            return 'Неверный порт!'

        if status == 'down':
            self.session.sendline(f'set port {port} disable')
        elif status == 'up':
            self.session.sendline(f'set port {port} enable')
        else:
            return f'Неверный статус {status}'

        return f'{status} port {port} ' + self.save_config()

    def port_config(self, port: str):
        port = self.validate_port(port)
        if port is None:
            return 'Неверный порт!'

        running_config = self.send_command('show running-config').split('\n')
        port_config = ''
        for line in running_config:
            s = self.find_or_empty(rf'.+port {port} .*', line)
            if s:
                port_config += s + '\n'

        return port_config

    def port_type(self, port: str):
        port = self.validate_port(port)
        if port is None:
            return 'Неверный порт!'

        output = self.send_command(f'show port {port} brief')
        type_ = self.find_or_empty(r'\d+\s+\d+Base(\S+)\s+', output)

        if type_ in COOPER_TYPES:
            return 'COPPER'
        elif type_ in FIBER_TYPES or type_ == 'X':
            return 'SFP'

    def get_port_errors(self, port: str):
        port = self.validate_port(port)
        if port is None:
            return 'Неверный порт!'

        return self.send_command(f'show port {port} statistics')

    def set_description(self, port: str, desc: str) -> str:
        if not self.__privileged:
            return 'Не привилегированный. Операция отклонена!'

        port = self.validate_port(port)
        if port is None:
            return 'Неверный порт!'

        desc = self.clear_description(desc)

        if desc == '':  # Если строка описания пустая, то необходимо очистить описание на порту оборудования
            status = self.send_command(f'clear port {port} description', expect_command=False)

        else:  # В другом случае, меняем описание на оборудовании
            status = self.send_command(f'set port {port} description {desc}', expect_command=False)

        if 'Parameter too long' in status:
            # Если длина описания больше чем доступно на оборудовании
            output = self.send_command(f'set port {port} description ?')
            return 'Max length:' + self.find_or_empty(r'maxsize:(\d+)', output)

        return f'Description has been {"changed" if desc else "cleared"}.' + self.save_config()