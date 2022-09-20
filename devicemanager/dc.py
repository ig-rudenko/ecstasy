import re
import time

import pexpect
import os
import textfsm
from re import findall, sub, match
from abc import ABC, abstractmethod
from functools import lru_cache

TEMPLATE_FOLDER = os.path.split(os.path.abspath(__file__))[0]


__all__ = [
    'ProCurve',
    'ZTE',
    'Huawei',
    'Cisco',
    'AlcatelSAS',
    'Dlink',
    'Alcatel',
    'EdgeCore',
    'EltexMES',
    'EltexESR',
    'Extreme',
    'Qtech',
    'HuaweiMA5600T',
    'Juniper',
    'DeviceFactory'
]


COOPER_TYPES = [
    'T', 'TX', 'VG', 'CX', 'CR'
]

FIBER_TYPES = [
    'FOIRL', 'F', 'FX', 'SX', 'LX', 'BX', 'EX', 'ZX', 'SR', 'ER', 'SW', 'LW', 'EW', 'LRM', 'PR', 'LR', 'ER', 'FR'
]


def _interface_normal_view(interface) -> str:
    """
    Приводит имя интерфейса к виду принятому по умолчанию для коммутаторов\n
    Например: Eth 0/1 -> Ethernet0/1
              GE1/0/12 -> GigabitEthernet1/0/12\n
    :param interface:   Интерфейс в сыром виде (raw)
    :return:            Интерфейс в общепринятом виде
    """
    interface_number = findall(r'(\d+([/\\]?\d*)*)', str(interface))
    if match(r'^[Ee]t', interface):
        return f"Ethernet {interface_number[0][0]}"
    elif match(r'^[Ff]a', interface):
        return f"FastEthernet {interface_number[0][0]}"
    elif match(r'^[Gg][ieE]', interface):
        return f"GigabitEthernet {interface_number[0][0]}"
    elif match(r'^\d+', interface):
        return findall(r'^\d+', interface)[0]
    elif match(r'^[Tt]e', interface):
        return f'TenGigabitEthernet {interface_number[0][0]}'
    else:
        return ''


def _range_to_numbers(ports_string: str) -> list:
    ports_split = []
    if 'to' in ports_string:
        # Если имеется формат "trunk,1 to 7 12 to 44"
        vv = [list(range(int(v[0]), int(v[1]) + 1)) for v in
              [range_ for range_ in findall(r'(\d+)\s*to\s*(\d+)', ports_string)]]
        for v in vv:
            ports_split += v
        return sorted(ports_split)
    elif ',' in ports_string:
        ports_split = ports_string.replace(' ', '').split(',')
    else:
        ports_split = ports_string.split()

    res_ports = []
    for p in ports_split:
        try:
            if '-' in p:
                port_range = list(range(int(p.split('-')[0]), int(p.split('-')[1]) + 1))
                for pr in port_range:
                    res_ports.append(int(pr))
            else:
                res_ports.append(int(p))
        except:
            pass

    return sorted(res_ports)


class BaseDevice(ABC):
    prompt: str  # Регулярное выражение, которое указывает на приглашение для ввода следующей команды

    # Регулярное выражение, которое указывает на ожидание ввода клавиши, для последующего отображения информации
    space_prompt: str
    mac_format = ''  # Регулярное выражение, которое определяет отображение МАС адреса
    SAVED_OK = 'Saved OK'  # Конфигурация была сохранена
    SAVED_ERR = 'Saved Error'  # Ошибка при сохранении конфигурации

    def __init__(self, session: pexpect, ip: str, auth: dict, model: str = '', vendor: str = ''):
        self.session: pexpect.spawn = session
        self.ip = ip
        self.model: str = model
        self.auth: dict = auth
        self.mac: str = ''
        self.serialno: str = ''
        self.os: str = ''
        self.os_version: str = ''
        self.vendor: str = vendor

    @staticmethod
    def find_or_empty(pattern, string):
        """Используя pattern ищет в строке совпадения, если нет, то возвращает пустую строку"""

        m = findall(pattern, string)
        if m:
            return m[0]
        else:
            return ''

    def send_command(self, command: str, before_catch: str = None, expect_command=True, num_of_expect=10,
                     space_prompt=None, prompt=None, pages_limit=None) -> str:
        """
        Отправляет команду на оборудование и считывает её вывод

        Вывод будет содержать в себе строки от момента ввода команды, до (prompt: str), указанного в классе

        :param command: Команда, которую необходимо выполнить на оборудовании
        :param before_catch: Регулярное выражение, указывающее начало
        :param expect_command: Не вносить текст команды в вывод
        :param num_of_expect: Кол-во символов с конца команды, по которым необходимо её находить
        :param space_prompt: Регулярное выражение, которое указывает на ожидание ввода клавиши,
                             для последующего отображения информации
        :param prompt: Регулярное выражение, которое указывает на приглашение для ввода следующей команды
        :param pages_limit: Кол-во страниц, если надо, которые будут выведены при постраничном отображении
        :return: Строка с результатом команды
        """

        if space_prompt is None:
            space_prompt = self.space_prompt
        if prompt is None:
            prompt = self.prompt

        output = ''
        self.session.sendline(command)  # Отправляем команду

        if expect_command:
            self.session.expect(command[-num_of_expect:])  # Считываем введенную команду с поправкой по длине символов
        if before_catch:
            self.session.expect(before_catch)

        if space_prompt:  # Если необходимо постранично считать данные, то создаем цикл
            while pages_limit is None or pages_limit > 0:
                match = self.session.expect(
                    [
                        prompt,  # 0 - конец
                        space_prompt,  # 1 - далее
                        pexpect.TIMEOUT  # 2
                    ],
                    timeout=20
                )
                output += self.session.before.decode(errors='ignore')  # Убираем лишние символы
                if match == 0:
                    break
                elif match == 1:
                    self.session.send(" ")  # Отправляем символ пробела, для дальнейшего вывода
                    output += '\n'
                else:
                    print(f'{self.ip} - timeout во время выполнения команды "{command}"')
                    break

                # Если задано кол-во страниц
                if pages_limit:
                    pages_limit -= 1

        else:  # Если вывод команды выдается полностью, то пропускаем цикл
            try:
                self.session.expect(prompt)
            except pexpect.TIMEOUT:
                pass
            output = self.session.before.decode('utf-8')
        return output

    @abstractmethod
    def get_interfaces(self) -> list:
        """
        Интерфейсы на оборудовании
        :return: [ ['name', 'status', 'desc'], ... ]
        """
        pass

    @abstractmethod
    def get_vlans(self) -> list:
        """
        Интерфейсы и VLAN на оборудовании
        :return: [ ['name', 'status', 'desc', 'vlans'], ... ]
        """
        pass

    @abstractmethod
    def get_mac(self, port: str) -> list:
        """
        Поиск маков на порту
        :return: [ ('vid', 'mac'), ... ]
        """
        pass

    @abstractmethod
    def reload_port(self, port: str) -> str:
        """Перезагрузка порта"""
        pass

    @abstractmethod
    def set_port(self, port: str, status: str) -> str:
        """Изменение состояния порта"""
        pass

    @abstractmethod
    def save_config(self):
        """"""


class ProCurve(BaseDevice):
    prompt = r"\S+#"
    space_prompt = r"-- MORE --, next page: Space, next line: Enter, quit: Control-C"

    def __init__(self, session: pexpect, ip: str, auth: dict, model='', vendor=''):
        super(ProCurve, self).__init__(session, ip, auth, model, vendor)
        sys_info = self.send_command('show system-information', before_catch='General System Information', expect_command=False)
        self.model = self.find_or_empty(r'Base MAC Addr\s+: (\S+)', sys_info)
        self.serialno = self.find_or_empty(r'Serial Number\s+: (\S+)', sys_info)
        self.os_version = self.find_or_empty(r'Software revision\s+: (\S+)', sys_info)

    def get_interfaces(self) -> list:
        result = []
        raw_intf_status = self.send_command('show interfaces brief', expect_command=False)
        with open(f'{TEMPLATE_FOLDER}/templates/interfaces/procurve_status.template') as template_file:
            int_des_ = textfsm.TextFSM(template_file)
        intf_status = int_des_.ParseText(raw_intf_status)  # Ищем интерфейсы
        for line in intf_status:
            port = self.find_or_empty(r'[ABCD]*\d+', line[0])
            port_output = self.send_command(f'show interfaces ethernet {port}', expect_command=False)
            descr = findall(r'Name\s*(:\s*\S*)\W+Link', port_output)
            result.append(
                [
                    line[0],
                    line[2].lower() if line[1] == "Yes" else "admin down",
                    descr[0][1:] if descr else ''
                ]
            )
        return result

    def get_vlans(self) -> list:
        pass


class ZTE(BaseDevice):
    prompt = r'\S+\(cfg\)#|\S+>'
    space_prompt = "----- more -----"
    mac_format = r'\S\S\.' * 5 + r'\S\S'  # e1.3f.45.d6.23.53

    def __init__(self, session: pexpect, ip: str, auth: dict, model='', vendor=''):
        super().__init__(session, ip, auth, model, vendor)
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

        with open(f'{TEMPLATE_FOLDER}/templates/interfaces/zte.template') as template_file:
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

        with open(f'{TEMPLATE_FOLDER}/templates/vlans_templates/zte_vlan.template', 'r') as template_file:
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
        for i in findall(rf'({self.mac_format})\s+(\d+)', output_macs):
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
        time.sleep(1)
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


class Huawei(BaseDevice):
    prompt = r'<\S+>$|\[\S+\]$|Unrecognized command'
    space_prompt = r"---- More ----"
    mac_format = r'\S\S\S\S-\S\S\S\S-\S\S\S\S'

    def __init__(self, session: pexpect, ip: str, auth: dict, model='', vendor=''):
        super().__init__(session, ip, auth, model, vendor)
        self.session.sendline('super')
        v = session.expect(
            [
                'Unrecognized command|Now user privilege is 3 level',  # 0 - huawei-2326
                '[Pp]ass',  # 1 - huawei-2403 повышение уровня привилегий
                'User privilege level is'  # 2 - huawei-2403 уже привилегированный
            ]
        )
        if v == 1:
            self.session.sendline(self.auth['privilege_mode_password'])

        if self.session.expect(
                [
                    r'<\S+>',  # 0 - режим просмотра
                    r'\[\S+\]'  # 1 - режим редактирования
                ]
        ):  # Если находимся в режиме редактирования, то понижаем до режима просмотра
            self.session.sendline('quit')
            self.session.expect(r'<\S+>$')

        version = self.send_command('display version')
        self.model = self.find_or_empty(r'Quidway (\S+) [Routing Switch]*uptime', version)

        if 'S2403' in self.model:
            manuinfo = self.send_command('display device manuinfo')
            self.mac = self.find_or_empty(r'MAC ADDRESS\s+:\s+(\S+)', manuinfo)
            self.serialno = self.find_or_empty(r'DEVICE SERIAL NUMBER\s+:\s+(\S+)', manuinfo)

        elif 'S2326' in self.model:
            mac = self.send_command('display bridge mac-address')
            self.mac = self.find_or_empty(r'System Bridge Mac Address\s+:\s+(\S+)\.', mac)

            elabel = self.send_command('display elabel')
            self.serialno = self.find_or_empty(r'BarCode=(\S+)', elabel)

    def save_config(self):
        self.session.sendline('save')
        self.session.expect(r'[Aa]re you sure.*\[Y\/N\]')
        self.session.sendline('Y')
        self.session.sendline('\n')
        if self.session.expect([self.prompt, r'successfully'], timeout=20):
            return self.SAVED_OK
        return self.SAVED_ERR

    def get_interfaces(self):
        output = ''
        if 'S2403' in self.model:
            ht = 'huawei-2403'
            output = self.send_command('display brief interface')
        elif 'S2326' in self.model:
            ht = 'huawei-2326'
            output = self.send_command('display interface description')
        else:
            ht = 'huawei'

        with open(f'{TEMPLATE_FOLDER}/templates/interfaces/{ht}.template', 'r') as template_file:
            int_des_ = textfsm.TextFSM(template_file)
            result = int_des_.ParseText(output)  # Ищем интерфейсы
        return [
            [
                line[0],  # interface
                line[1].lower().replace('adm', 'admin').replace('*', 'admin '),  # status
                line[2]  # desc
            ]
            for line in result if not line[0].startswith('NULL') and not line[0].startswith('V')
        ]

    def get_vlans(self) -> list:
        interfaces = self.get_interfaces()
        result = []
        for line in interfaces:
            if not line[0].startswith('V') and not line[0].startswith('NU') and not line[0].startswith('A'):
                output = self.send_command(f"display current-configuration interface {_interface_normal_view(line[0])}", expect_command=False)

                vlans_group = sub(r'(?<=undo).+vlan (.+)', '', output)  # Убираем строчки, где есть "undo"
                vlans_group = list(set(findall(r'vlan (.+)', vlans_group)))  # Ищем строчки вланов, без повторений
                port_vlans = []
                for v in vlans_group:
                    port_vlans = _range_to_numbers(v)
                result.append(line + [port_vlans])

        return result

    def get_mac(self, port) -> list:
        """
        Поиск маков на порту
        :param port:
        :return: [ ('vid', 'mac'), ... ]
        """

        mac_list = []

        if '2403' in self.model:
            mac_str = self.send_command(f'display mac-address interface {_interface_normal_view(port)}')
            for i in findall(rf'({self.mac_format})\s+(\d+)\s+\S+\s+\S+\s+\S+', mac_str):
                mac_list.append(i[::-1])

        elif '2326' in self.model:
            mac_str = self.send_command(f'display mac-address {_interface_normal_view(port)}')
            for i in findall(rf'({self.mac_format})\s+(\d+)/\S+\s+\S+\s+\S+', mac_str):
                mac_list.append(i[::-1])

        return mac_list

    @lru_cache
    def __port_info(self, port):
        return self.send_command(f'display interface {_interface_normal_view(port)}')

    def port_type(self, port) -> str:
        res = self.__port_info(port)

        type_ = self.find_or_empty(r'Port hardware type is (\S+)|Port Mode: (.*)', res)
        print(f'{type_=}')
        if type_:

            type_ = type_[0] if type_[0] else type_[1]

            if "COMBO" in type_:
                return 'COMBO-' + self.find_or_empty(r'Current Work Mode: (\S+)', res)

            elif "FIBER" in type_ or 'SFP' in type_:
                return 'SFP'

            elif "COPPER" in type_:
                return 'COPPER'

            else:
                sub_type = self.find_or_empty(r'\d+_BASE_(\S+)', type_)
                if sub_type in COOPER_TYPES:
                    return 'COPPER'
                elif sub_type in FIBER_TYPES:
                    return 'FIBER'
                else:
                    return ''
        else:
            return ''

    def get_port_errors(self, port):
        return self.__port_info(port)

    def reload_port(self, port) -> str:
        self.session.sendline('system-view')
        self.session.sendline(f'interface {_interface_normal_view(port)}')
        self.session.sendline('shutdown')
        time.sleep(1)
        self.session.sendline('undo shutdown')
        self.session.sendline('quit')
        self.session.expect(r'\[\S+\]')
        self.session.sendline('quit')
        self.session.expect(r'\[\S+\]')
        r = self.session.before.decode(errors='ignore')
        s = self.save_config()
        return r + s

    def set_port(self, port, status) -> str:
        self.session.sendline('system-view')
        self.session.sendline(f'interface {_interface_normal_view(port)}')
        if status == 'up':
            self.session.sendline('undo shutdown')
        elif status == 'down':
            self.session.sendline('shutdown')
        self.session.expect(r'\[\S+\]')
        self.session.sendline('quit')
        self.session.expect(r'\[\S+\]')
        self.session.sendline('quit')
        self.session.expect(r'\[\S+\]')
        r = self.session.before.decode(errors='ignore')
        s = self.save_config()
        return r + s

    def port_config(self, port):
        config = self.send_command(
            f'display current-configuration interface {_interface_normal_view(port)}',
            expect_command=False, before_catch=r'#'
        )
        return config


class Cisco(BaseDevice):
    prompt = r'\S+#$'
    space_prompt = r' --More-- '
    mac_format = r'\S\S\S\S\.\S\S\S\S\.\S\S\S\S'  # 0018.e7d3.1d43

    def __init__(self, session: pexpect, ip: str, auth: dict, model: str = '', vendor=''):
        super(Cisco, self).__init__(session, ip, auth, model, vendor)
        version = self.send_command('show version')
        self.serialno = self.find_or_empty(r'System serial number\s+: (\S+)', version)
        self.mac = self.find_or_empty(r'[MACmac] [Aa]ddress\s+: (\S+)', version)

    def save_config(self):
        for _ in range(3):  # Пробуем 3 раза, если ошибка
            self.session.sendline('write')
            # self.session.expect(r'Building configuration')
            if self.session.expect([self.prompt, r'\[OK\]']):
                return self.SAVED_OK
        return self.SAVED_ERR

    def get_logs(self):
        logs = self.send_command('show logging').replace('', '')
        logs = '\n'.join(reversed(logs.split('\n')))
        return logs

    def get_interfaces(self) -> list:
        output = self.send_command('show int des')
        output = sub('.+\nInterface', 'Interface', output)
        with open(f'{TEMPLATE_FOLDER}/templates/interfaces/cisco.template', 'r') as template_file:
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
                vlans_group = findall(r'(?<=access|llowed) vlan [ad\s]*(\S*\d)', output)  # Строчки вланов
                result.append(line + [vlans_group])

        return result

    def get_mac(self, port) -> list:
        mac_str = self.send_command(f'show mac address-table interface {_interface_normal_view(port)}', expect_command=False)
        return findall(rf'(\d+)\s+({self.mac_format})\s+\S+\s+\S+', mac_str)

    def reload_port(self, port) -> str:
        self.session.sendline('configure terminal')
        self.session.expect(self.prompt)
        self.session.sendline(f'interface {_interface_normal_view(port)}')
        self.session.expect(self.prompt)
        self.session.sendline('shutdown')
        time.sleep(1)
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

        port_type = self.send_command(f'show interfaces {_interface_normal_view(port)} | include media')
        return f'<p>{port_type}</p>'

    def port_type(self, port):
        """Определяем тип порта: медь или оптика"""

        port_type = self.find_or_empty(r'[Bb]ase(\S{1,2})', self.get_port_info(port))
        if 'SFP' in self.get_port_info(port) or port_type in FIBER_TYPES:
            return 'SFP'

        return 'COPPER'

    def get_port_errors(self, port):
        return self.send_command(f'show interfaces {_interface_normal_view(port)} | include error')

    def port_config(self, port):
        """Конфигурация порта"""

        config = self.send_command(
            f'show running-config interface {_interface_normal_view(port)}',
            before_catch=r'Current configuration.+?\!'
        )
        return config


class AlcatelSAS(BaseDevice):
    prompt = r'\S+#\s*$'
    space_prompt = r'Press any key to continue \(Q to quit\)'


class Dlink(BaseDevice):
    prompt = r'\S+#'
    space_prompt = None
    mac_format = r'\S\S-'*5+r'\S\S'

    def __init__(self, session: pexpect, ip: str, auth: dict, model: str = '', vendor=''):
        super().__init__(session, ip, auth, model, vendor)

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
        with open(f'{TEMPLATE_FOLDER}/templates/interfaces/d-link.template', 'r') as template_file:
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
        with open(f'{TEMPLATE_FOLDER}/templates/vlans_templates/d-link.template', 'r') as template_file:
            vlan_templ = textfsm.TextFSM(template_file)
            result_vlan = vlan_templ.ParseText(output)
        # сортируем и выбираем уникальные номера портов из списка интерфейсов
        port_num = set(sorted([int(findall(r'\d+', p[0])[0]) for p in interfaces]))

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
        port = sub(r'\D', '', port)

        mac_str = self.send_command(f'show fdb port {port}')
        return findall(rf'(\d+)\s+\S+\s+({self.mac_format})\s+\d+\s+\S+', mac_str)

    @staticmethod
    def validate_port(port: str):
        port = port.strip()
        if findall(r'^\d/\d+$', port):
            port = sub(r'^\d/', '', port)
        elif findall(r'\d+|\d+\s*\([FC]\)', port):
            port = sub(r'\D', '', port)
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
        time.sleep(1)
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


class Alcatel(BaseDevice):
    prompt = r'\S+#\s*$'
    space_prompt = r'More: <space>,  Quit: q, One line: <return> '

    def get_interfaces(self) -> list:
        pass

    def get_vlans(self) -> list:
        pass

    def get_mac(self, port: str) -> list:
        pass

    def reload_port(self, port: str) -> str:
        pass

    def set_port(self, port: str, status: str) -> str:
        pass


class EdgeCore(BaseDevice):
    prompt = r'\S+#$'
    space_prompt = '---More---'

    def get_interfaces(self) -> list:
        pass

    def get_vlans(self) -> list:
        pass

    def get_mac(self, port: str) -> list:
        pass

    def reload_port(self, port: str) -> str:
        pass

    def set_port(self, port: str, status: str) -> str:
        pass


class _Eltex(BaseDevice):
    prompt = r'\S+#\s*'
    space_prompt = r"More: <space>,  Quit: q or CTRL\+Z, One line: <return> |" \
                   r"More\? Enter - next line; Space - next page; Q - quit; R - show the rest\."

    def __init__(self, session: pexpect, ip: str, auth: dict, model='', vendor=''):
        super().__init__(session, ip, auth, model, vendor)
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


class EltexMES(BaseDevice):
    prompt = r'\S+#\s*'
    space_prompt = r"More: <space>,  Quit: q or CTRL\+Z, One line: <return> |" \
                   r"More\? Enter - next line; Space - next page; Q - quit; R - show the rest\."
    _template_name = 'eltex-mes'
    mac_format = r'\S\S:' * 5 + r'\S\S'

    def __init__(self, session: pexpect, ip: str, auth: dict, model='', vendor='', mac=''):
        super(EltexMES, self).__init__(session, ip, auth, model, vendor)
        self.mac = mac
        inv = self.send_command('show inventory')
        self.serialno = self.find_or_empty(r'SN: (\S+)', inv)

    def save_config(self):
        self.session.sendline('end')
        self.session.expect(self.prompt)
        for _ in range(3):  # Пробуем 3 раза, если ошибка
            self.session.sendline('write')
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
        with open(f'{TEMPLATE_FOLDER}/templates/interfaces/{self._template_name}.template', 'r') as template_file:
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
                vlans_group = findall(r'vlan [ad ]*(\S*\d)', output)  # Строчки вланов
                port_vlans = []
                if vlans_group:
                    for v in vlans_group:
                        port_vlans += _range_to_numbers(v)
                result.append(line + [port_vlans])
        return result

    def get_mac(self, port) -> list:
        mac_str = self.send_command(f'show mac address-table interface {_interface_normal_view(port)}')
        return findall(rf'(\d+)\s+({self.mac_format})\s+\S+\s+\S+', mac_str)

    def reload_port(self, port) -> str:
        self.session.sendline('configure terminal')
        self.session.expect(r'#')
        self.session.sendline(f'interface {_interface_normal_view(port)}')
        self.session.sendline('shutdown')
        time.sleep(1)
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


class EltexESR(EltexMES):
    _template_name = 'eltex-esr'

    def __init__(self, session: pexpect, ip: str, auth: dict, model='', vendor='', mac=''):
        super(EltexESR, self).__init__(session, ip, auth, model, vendor)
        system = self.send_command('show system')
        self.mac = mac
        self.serialno = self.find_or_empty(r'serial number:\s+(\S+)', system)


class Extreme(BaseDevice):
    prompt = r'\S+\s*#\s*$'
    space_prompt = "Press <SPACE> to continue or <Q> to quit:"
    mac_format = r'\S\S:' * 5 + r'\S\S'

    def __init__(self, session: pexpect, ip: str, auth: dict, model='', vendor=''):
        super(Extreme, self).__init__(session, ip, auth, model, vendor)
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

    def get_logs(self, lines=5):
        logs = self.send_command(f'show log', pages_limit=lines)
        return logs

    def get_interfaces(self) -> list:
        # LINKS
        output_links = self.send_command('show ports information')
        with open(f'{TEMPLATE_FOLDER}/templates/interfaces/extreme_links.template', 'r') as template_file:
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

        with open(f'{TEMPLATE_FOLDER}/templates/interfaces/extreme_des.template', 'r') as template_file:
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

        with open(f'{TEMPLATE_FOLDER}/templates/vlans_templates/extreme.template', 'r') as template_file:
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
        macs = findall(rf'({self.mac_format})\s+v(\d+)', output)

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
        time.sleep(1)
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


class Qtech(BaseDevice):
    prompt = r'\S+#$'
    space_prompt = "--More--"


class HuaweiMA5600T(BaseDevice):
    prompt = r'config\S+#|\S+#'
    space_prompt = r'---- More \( Press \'Q\' to break \) ----'
    mac_format = r'\S\S\S\S-\S\S\S\S-\S\S\S\S'

    def __init__(self, session: pexpect, ip: str, auth: dict, model='', vendor=''):
        super(HuaweiMA5600T, self).__init__(session, ip, auth, model, vendor)
        self.session.sendline('enable')
        self.session.expect(r'\S+#')

    def save_config(self):
        pass

    def split_port(self, port: str) -> tuple:
        """
        Разделяет строку порта на тип интерфейса и плата, слот, порт

        ADSL 0/2/4 -> "adsl", ["0", "2", "4"]

        Смотрит платы

            # display board

            #-------------------------------------------------------------------------
            SlotID  BoardName  Status         SubType0 SubType1    Online/Offline
            #-------------------------------------------------------------------------
            0
            1
            2       H808ADLF   Normal
            3       H808ADLF   Normal
            4       H808ADLF   Normal
            5       H808ADLF   Normal
            6       H808ADLF   Normal
            7
            8       H805ADPD   Normal
            9       H801SCUB   Active_normal


        ethernet0/9/2 -> "scu", ["0", "9", "2"]

        """

        port = port.lower().strip()
        type_ = self.find_or_empty(r'^ethernet|^adsl|^gpon', port)
        indexes = re.sub(r'^[a-z]+', '', port).split('/')
        if type_ == 'ethernet':
            board_info = self.send_command(f'display board {indexes[0]}')
            print(board_info)
            board_list = self.find_or_empty(rf'\s+({indexes[1]})\s+(\S+)\s+\S+', board_info)
            if board_list:
                if 'SCU' in board_list[1]:
                    return 'scu', indexes
                elif 'GI' in board_list[1]:
                    return 'giu', indexes

            return 'eth', indexes

        return type_, indexes

    def port_info_parser(self, info: str):
        """
        Преобразовываем информацию о порте для отображения на странице
        """

        def color(val: float, s: str) -> str:
            """ Определяем цвета в зависимости от числовых значений показателя """
            if 'channel SNR margin' in s:
                gradient = [5, 7, 10, 20]
            elif 'channel attenuation' in s:
                gradient = [-60, -50, -40, -20]
                val = -val
            elif 'total output power' in s:
                return '#95e522' if val >= 10 else '#e5a522'
            else:
                return ''
            # проверяем значения по градиенту
            if val <= gradient[0]:
                return '#e55d22'
            if val <= gradient[1]:
                return '#e5a522'
            if val <= gradient[2]:
                return '#dde522'
            if val <= gradient[3]:
                return '#95e522'
            else:
                return '#22e536'

        lines = info.strip().split('\n')  # Построчно создаем список
        html = '<div class="row"><div class="col-4">'  # Создаем ряд и начало первой колонки
        table = """
            <div class="col-8">
                <table class="table">
                  <thead>
                    <tr>
                      <th></th>
                      <th scope="col" style="text-align: center;">Downstream</th>
                      <th scope="col" style="text-align: center;">Upstream</th>
                    </tr>
                  </thead>
                  <tbody>
                """
        table_dict = {
            'Do': [],
            'Up': []
        }
        for line in lines:  # Построчно смотрим данные
            line = line.strip()

            if line.startswith('-' * 10):  # Прерываем, если дошли до строки с разделителем ------------
                break

            if not findall(r'^[DU].+?(-?\d+\.?\d*)', line):
                html += f'<p>{line}</p>'  # Записываем в первую колонку данные
            else:
                value = self.find_or_empty(r'-?\d+\.?\d*', line)  # Числовое значение
                if value:
                    line_new = f'<td style="text-align: center; background-color: {color(float(value), line)};">{value}</td>'
                else:  # Если нет значения - ошибка
                    line_new = f'<td style="text-align: center; background-color: #e55d22;">0</td>'

                table_dict[line[:2]].append(line_new)  # Обновляем ключ Do или Up

        names = ['Фактическая скорость передачи данных (Кбит/с)', 'Максимальная скорость передачи данных (Кбит/с)',
                 'Сигнал/Шум (дБ)', 'Interleaved channel delay (ms)', 'Затухание линии (дБ)', 'Общая выходная мощность (dBm)']

        # Наполняем таблицу
        for line in zip(names, table_dict['Do'], table_dict['Up']):
            table += f"""
            <tr>
                <td style="text-align: right";>{line[0]}</td>
                {line[1]}
                {line[2]}
            </tr>
            """
        else:
            table += "</tbody></table></div>"  # Закрываем таблицу

        html += '</div>'  # Закрываем первую колонку
        html += table     # Добавляем вторую колонку - таблицу
        html += '</div>'  # Закрываем ряд
        return html

    def get_port_info(self, port: str):
        """Смотрим информацию на порту"""

        type_, indexes = self.split_port(port)

        if not type_ or len(indexes) != 3:
            return f'Неверный порт! ({port})'

        self.session.sendline('config')
        self.session.sendline(f'interface {type_} {indexes[0]}/{indexes[1]}')
        self.session.expect(r'\S+#')
        self.session.sendline(f'display line operation {indexes[2]}')
        if self.session.expect([r'Are you sure to continue', 'Unknown command']):
            return ''
        output = self.send_command('y', expect_command=True, before_catch=r'Failure|------[-]+')

        if 'is not activated' in output:  # У данного порта нет таких команд
            return ''

        profile_output = self.send_command(f'display port state {indexes[2]}')
        profile_index = self.find_or_empty(rf'\s+\d+\s+\S+\s+(\d+)', profile_output)
        profile_output = self.send_command(f'display adsl line-profile {profile_index}')
        profile_name = f'Profile name: <strong>' + self.find_or_empty(r"Name:\s+(\S+)", profile_output) + '</strong>\n'

        return self.port_info_parser(profile_name + output)

    def get_mac(self, port) -> list:
        """
        Смотрим MAC'и на порту и отдаем в виде списка

        [ ["vlan", "mac"],  ... ]
        """

        type_, indexes = self.split_port(port)

        if len(indexes) != 3:  # Неверный порт
            return []

        self.session.sendline(f'display mac-address port {"/".join(indexes)}')
        com = self.send_command('\n', expect_command=False, before_catch='display mac-address')
        macs1 = findall(rf'\s+\S+\s+\S+\s+\S+\s+({self.mac_format})\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+.+?\s+(\d+)', com)

        # Попробуем еще одну команду
        self.session.sendline(f'display security bind mac {"/".join(indexes)}')
        com = self.send_command('\n', expect_command=False, before_catch='display security')
        macs2 = findall(rf'\s+\S+\s+({self.mac_format})\s+\S+\s+\S+\s+\S+\s+\S+\s+(\d+)', com)

        res = []
        print(macs1+macs2)
        for m in macs1+macs2:
            res.append(m[::-1])
        return res

    @staticmethod
    def _up_down_command(port_type: str, status: str):
        """В зависимости от типа порта возвращает команды для управления его статусом"""
        if port_type == 'scu' or port_type == 'giu':
            if status == 'down':
                return 'shutdown'
            if status == 'up':
                return 'undo shutdown'

        if port_type == 'adsl':
            if status == 'down':
                return 'deactivate'
            if status == 'up':
                return 'activate'

    def reload_port(self, port) -> str:
        """Перезагружаем порт"""

        type_, indexes = self.split_port(port)
        if not type_ or len(indexes) != 3:
            return f'Неверный порт! ({port})'

        self.session.sendline('config')
        self.session.sendline(f'interface {type_} {indexes[0]}/{indexes[1]}')
        self.session.expect(r'\S+#')

        cmd = f"{self._up_down_command(type_, 'down')} {indexes[2]}"  # Выключить порт
        self.session.sendline(cmd)
        self.session.expect(cmd)
        self.session.sendline('\n')
        time.sleep(1)  # Пауза

        cmd = f"{self._up_down_command(type_, 'up')} {indexes[2]}"  # Включить порт
        self.session.sendline(cmd)
        self.session.expect(cmd)

        s = self.session.before.decode()

        self.session.sendline('\n')
        self.session.expect(r'\S+#$')

        s += self.session.before.decode()
        return s

    def set_port(self, port, status) -> str:
        type_, indexes = self.split_port(port)
        if not type_ or len(indexes) != 3:
            return f'Неверный порт! ({port})'

        self.session.sendline('config')
        self.session.sendline(f'interface {type_} {indexes[0]}/{indexes[1]}')
        self.session.expect(r'\S+#')

        # Выключаем или включаем порт, в зависимости от типа будут разные команды
        s = self.send_command(f'{self._up_down_command(type_, status)} {indexes[2]}', expect_command=False)
        self.send_command('\n', expect_command=False)

        return s

    def get_interfaces(self) -> list:
        pass

    def get_vlans(self) -> list:
        pass


class IskratelControl(BaseDevice):
    prompt = r'\(\S+\)\s*#'
    space_prompt = r'--More-- or \(q\)uit'
    mac_format = r'\S\S:'*5+r'\S\S'

    def __init__(self, session: pexpect, ip: str, auth: dict, model='', vendor=''):
        super(IskratelControl, self).__init__(session, ip, auth, model, vendor)

    def save_config(self):
        pass

    def get_mac(self, port) -> list:
        """
        Смотрим MAC'и на порту и отдаем в виде списка

        [ ["vlan", "mac"],  ... ]
        """

        if not findall(r'\d+/\d+', port):  # Неверный порт
            return []

        output = self.send_command(f'show mac-addr-table interface {port}')
        macs = findall(rf'({self.mac_format})\s+(\d+)', output)

        res = []
        for m in macs:
            res.append(m[::-1])
        return res

    def get_interfaces(self) -> list:
        pass

    def get_vlans(self) -> list:
        pass

    def reload_port(self, port) -> str:
        pass

    def set_port(self, port: str, status: str) -> str:
        pass


class IskratelMBan(BaseDevice):
    prompt = r'mBAN>\s'
    space_prompt = r'Press any key to continue or Esc to stop scrolling\.'
    mac_format = r'\S\S:'*5+r'\S\S'

    def __init__(self, session: pexpect, ip: str, auth: dict, model='', vendor=''):
        super(IskratelMBan, self).__init__(session, ip, auth, model, vendor)

    def save_config(self):
        pass

    @property
    def get_service_ports(self):
        return ['1_32', '1_33', '1_40']

    def port_info_parser(self, info: str) -> str:

        def color(val: str, s: str) -> str:
            if not val:
                return ''
            val = float(val)

            """ Определяем цвета в зависимости от числовых значений показателя """
            if 'Сигнал/Шум' in s:
                gradient = [5, 7, 10, 20]
            elif 'Затухание линии' in s:
                gradient = [-60, -50, -40, -20]
                val = -val
            elif 'total output power' in s:
                return '#95e522' if val >= 10 else '#e5a522'
            else:
                return ''
            # проверяем значения по градиенту
            if val <= gradient[0]:
                return '#e55d22'
            if val <= gradient[1]:
                return '#e5a522'
            if val <= gradient[2]:
                return '#dde522'
            if val <= gradient[3]:
                return '#95e522'
            else:
                return '#22e536'

        html = '<div class="row"><div class="col-4">'  # Создаем ряд и начало первой колонки
        table = """
            <div class="col-8">
                <table class="table">
                  <thead>
                    <tr>
                      <th></th>
                      <th scope="col" style="text-align: center;">Downstream</th>
                      <th scope="col" style="text-align: center;">Upstream</th>
                    </tr>
                  </thead>
                  <tbody>
                """
        names = ['Фактическая скорость передачи данных (Кбит/с)', 'Максимальная скорость передачи данных (Кбит/с)',
                 'Сигнал/Шум (дБ)', 'Interleaved channel delay (ms)', 'Затухание линии (дБ)']

        oper_state = self.find_or_empty(r'Operational State\s+(\S+)\/', info)
        if self.find_or_empty(r'Equipment\s+Unequipped', info):
            html += '<p style="color: red">Порт - ADMIN DOWN</p>'
        elif oper_state == 'Down':
            html += '<p>Порт - DOWN</p>'
        elif oper_state == 'Up':
            html += '<p style="color: green">Порт - UP</p>'

        html += f'<p>'+self.find_or_empty(r"Type .*", info)+'</p>'
        html += f'<p>'+self.find_or_empty(r"Profile Name\s+\S+", info)+'</p>'

        # Данные для таблицы
        data_rate = findall(r'DS Data Rate AS0\s+(\d+) kbit/s\s+US Data Rate LS0\s+(\d+) kbit', info) or [('', '')]
        max_rate = [(self.find_or_empty(r'Maximum DS attainable aggregate rate\s+(\d+) kbit', info),
                    self.find_or_empty(r'Maximum US attainable aggregate rate\s+(\d+) kbit', info))]

        snr = findall(r'DS SNR Margin\s+(\d+) dB\s+US SNR Margin\s+(\d+)', info) or [('', '')]
        intl = findall(r'DS interleaved delay\s+(\d+) ms\s+US interleaved delay\s+(\d+)', info) or [('', '')]
        att = findall(r'DS Attenuation\s+(\d+) dB\s+US Attenuation\s+(\d+)', info) or [('', '')]

        # Наполняем таблицу
        for line in zip(names, data_rate + max_rate + snr + intl + att):
            table += f"""
            <tr>
                <td style="text-align: right";>{line[0]}</td>
                <td style="text-align: center; background-color: {color(line[1][0], line[0])};">{line[1][0]}</td>
                <td style="text-align: center; background-color: {color(line[1][1], line[0])};">{line[1][1]}</td>
            </tr>
            """
        else:
            table += "</tbody></table></div>"  # Закрываем таблицу

        html += '</div>'  # Закрываем первую колонку
        html += table     # Добавляем вторую колонку - таблицу
        html += '</div>'  # Закрываем ряд
        return html

    def get_port_info(self, port: str):
        port = port.strip()
        # Верные порты: port1, fasteth3, adsl2:1_40
        if not findall(r'^port\d+$|^fasteth\d+$|^dsl\d+:\d+_\d+$', port):
            return ''

        if 'port' in port:  # Если указан физический adsl порт
            cmd = f'show dsl port {port[4:]} detail'
            before_catch = r'Name\s+\S+'
        else:
            cmd = f'show interface {port}'
            before_catch = r'\[Enabled Connected Bridging\]'

        output = self.send_command(cmd, expect_command=False, before_catch=before_catch)
        return self.port_info_parser(output)

    def get_mac(self, port: str) -> list:
        """
        Смотрим MAC'и на порту и отдаем в виде списка

        [ ["vlan", "mac"],  ... ]
        """

        port = port.strip()
        macs = []  # Итоговый список маков

        # Верные порты: port1, fasteth3, dsl2:1_40, ISKRATEL:sv-263-3443 atm 2/1
        if not findall(r'^port\d+$|^fasteth\d+$|^dsl\d+:\d+_\d+$|^ISKRATEL.*atm \d+/\d+$', port):
            return []

        if 'fasteth' in port or 'adsl' in port:
            output = self.send_command(f'show bridge mactable interface {port}', expect_command=False)
            macs = findall(rf'(\d+)\s+({self.mac_format})', output)
            return macs

        elif 'port' in port:  # Если указан физический adsl порт
            port = port[4:]  # убираем слово port, оставляя только номер

        elif 'ISKRATEL' in port:
            port = self.find_or_empty(r'\d+$', port)
            if not port:
                return []

        for sp in self.get_service_ports:  # смотрим маки на сервис портах
            output = self.send_command(f'show bridge mactable interface dsl{port}:{sp}', expect_command=False)
            macs.extend(findall(rf'(\d*)\s+({self.mac_format})', output))

        return macs

    def reload_port(self, port: str) -> str:
        port = port.strip()
        index = findall(r'^port(\d+)$', port)
        if not index:
            return f'Порт ({port}) нельзя перезагрузить'

        s1 = self.send_command(f'set dsl port {index[0]} port_equp unequipped', expect_command=False)
        time.sleep(1)
        s2 = self.send_command(f'set dsl port {index[0]} port_equp equipped', expect_command=False)

        return s1 + s2

    def set_port(self, port: str, status: str):
        port = port.strip()
        index = findall(r'^port(\d+)$', port)
        if not index:
            return f'Порт ({port}) нельзя перезагрузить'

        # Меняем состояние порта
        return self.send_command(
            f'set dsl port {index[0]} port_equp {"equipped" if status == "up" else "unequipped"}',
            expect_command=False
        )

    def get_interfaces(self) -> list:
        output = self.send_command(f'show dsl port', expect_command=False)
        res = []
        for line in output.split('\n'):
            interface = findall(r'(\d+)\s+(\S+)\s+\S+\s+(Equipped|Unequipped)\s+(Up|Down|)', line)
            if interface:
                res.append([
                    interface[0][0],    # name
                    interface[0][3].lower() if interface[0][2] == 'Equipped' else 'admin down',
                    interface[0][1],    # desc
                ])

        return res

    def get_vlans(self) -> list:
        return self.get_interfaces()


class Juniper(BaseDevice):
    prompt = r'-> $'
    space_prompt = '--- more --- '


class DeviceFactory:
    """Подключение к оборудованию, определение вендора и возврат соответствующего класса"""
    def __init__(self, ip: str, protocol: str, auth_obj=None):
        self.ip = ip

        self.protocol = protocol
        self.login = []
        self.password = []
        self.privilege_mode_password = 'enable'

        if isinstance(auth_obj, list):
            # Список объектов
            for auth_ in auth_obj:
                self.login.append(auth_.login)
                self.password.append(auth_.password)
                self.privilege_mode_password = auth_.secret or 'enable'

        else:
            # Один объект
            self.login = [auth_obj.login] or ['admin']
            self.password = [auth_obj.password] or ['admin']
            self.privilege_mode_password = auth_obj.secret or 'enable'

    def __get_device(self):
        auth = {
            'login': self.login,
            'password': self.password,
            'privilege_mode_password': self.privilege_mode_password
        }

        self.session.sendline('show version')
        version = ''
        while True:
            m = self.session.expect(
                [
                    r']$',
                    r'-More-|--\(more\)--',
                    r'>\s*$',
                    r'#\s*',
                    pexpect.TIMEOUT
                ],
                timeout=3
            )
            version += str(self.session.before.decode('utf-8'))
            if m == 1:
                self.session.send(' ')
            elif m == 4:
                self.session.sendcontrol('C')
            else:
                break

        # ProCurve
        if 'Image stamp:' in version:
            return ProCurve(self.session, self.ip, auth)

        # ZTE
        elif ' ZTE Corporation:' in version:
            model = BaseDevice.find_or_empty(r'Module 0:\s*(\S+\s\S+);\s*fasteth', version)
            return ZTE(self.session, self.ip, auth, model=model, vendor='ZTE')

        # HUAWEI
        elif 'Unrecognized command' in version:
            return Huawei(self.session, self.ip, auth, vendor='Huawei')

        # CISCO
        elif 'cisco' in version.lower():
            model = BaseDevice.find_or_empty(r'Model number\s*:\s*(\S+)', version)
            return Cisco(self.session, self.ip, auth, model=model, vendor='Cisco')

        # ALCATEL
        elif 'alcatel sas' in version.lower():
            model = BaseDevice.find_or_empty(r'(ALCATEL.+) COPYRIGHT \(C\)', version.upper())
            return AlcatelSAS(self.session, self.ip, auth, model=model, vendor='Alcatel')

        # D-LINK
        elif 'Next possible completions:' in version:
            return Dlink(self.session, self.ip, auth, vendor='D-Link')

        # Edge Core
        elif 'Hardware version' in version:
            return EdgeCore(self.session, self.ip, auth)

        # Eltex
        elif 'Active-image:' in version or 'Boot version:' in version:
            d = _Eltex(self.session, self.ip, self.privilege_mode_password)
            if 'MES' in d.model:
                return EltexMES(d.session, self.ip, auth, model=d.model, vendor='Eltex', mac=d.mac)
            elif 'ESR' in d.model:
                return EltexESR(d.session, self.ip, auth, model=d.model, vendor='Eltex', mac=d.mac)

        # Extreme
        elif 'ExtremeXOS' in version:
            return Extreme(self.session, self.ip, auth, vendor='Extreme')

        elif 'QTECH' in version:
            return Qtech(self.session, self.ip, auth, vendor='Q-Tech')

        # ISKRATEL CONTROL
        elif 'ISKRATEL' in version:
            return IskratelControl(self.session, self.ip, auth, model='ISKRATEL Switching', vendor='Iskratel')

        # ISKRATEL mBAN>
        elif 'IskraTEL' in version:
            model = BaseDevice.find_or_empty(r'CPU: IskraTEL \S+ (\S+)', version)
            return IskratelMBan(self.session, self.ip, auth, model=model, vendor='Iskratel')

        elif '% Unknown command' in version:
            self.session.sendline('display version')
            while True:
                m = self.session.expect([r']$', '---- More', r'>$', r'#', pexpect.TIMEOUT, '{'])
                if m == 5:
                    self.session.expect(r'\}:')
                    self.session.sendline('\n')
                    continue
                version += str(self.session.before.decode('utf-8'))
                if m == 1:
                    self.session.sendline(' ')
                if m == 4:
                    self.session.sendcontrol('C')
                else:
                    break
            if findall(r'VERSION : MA5600', version):
                model = BaseDevice.find_or_empty(r'VERSION : (MA5600\S+)', version)
                return HuaweiMA5600T(self.session, self.ip, auth, model=model, vendor='Huawei')

        elif 'show: invalid command, valid commands are' in version:
            self.session.sendline('sys info show')
            while True:
                m = self.session.expect([r']$', '---- More', r'>\s*$', r'#\s*$', pexpect.TIMEOUT])
                version += str(self.session.before.decode('utf-8'))
                if m == 1:
                    self.session.sendline(' ')
                if m == 4:
                    self.session.sendcontrol('C')
                else:
                    break
            if 'ZyNOS version' in version:
                pass

        elif 'unknown keyword show' in version:
            return Juniper(self.session, self.ip, auth, vendor='Juniper')

        else:
            return 'Не удалось распознать оборудование'

    def __enter__(self, algorithm: str = '', cipher: str = '', timeout: int = 30):
        connected = False
        if self.protocol == 'ssh':
            algorithm_str = f' -oKexAlgorithms=+{algorithm}' if algorithm else ''
            cipher_str = f' -c {cipher}' if cipher else ''

            for login, password in zip(self.login + ['admin'], self.password + ['admin']):

                with pexpect.spawn(f'ssh {login}@{self.ip}{algorithm_str}{cipher_str}') as self.session:

                    while not connected:
                        login_stat = self.session.expect(
                            [
                                r'no matching key exchange method found',  # 0
                                r'no matching cipher found',  # 1
                                r'Are you sure you want to continue connecting',  # 2
                                r'[Pp]assword:',  # 3
                                r'[#>\]]\s*$',  # 4
                                r'Connection closed'  # 5
                            ],
                            timeout=timeout
                        )
                        if login_stat == 0:
                            self.session.expect(pexpect.EOF)
                            algorithm = findall(r'Their offer: (\S+)', self.session.before.decode('utf-8'))
                            if algorithm:
                                algorithm_str = f' -oKexAlgorithms=+{algorithm[0]}'
                                self.session = pexpect.spawn(
                                    f'ssh {login}@{self.ip}{algorithm_str}{cipher_str}'
                                )
                        if login_stat == 1:
                            self.session.expect(pexpect.EOF)
                            cipher = findall(r'Their offer: (\S+)', self.session.before.decode('utf-8'))
                            if cipher:
                                cipher_str = f' -c {cipher[0].split(",")[-1]}'
                                self.session = pexpect.spawn(
                                    f'ssh {login}@{self.ip}{algorithm_str}{cipher_str}'
                                )
                        if login_stat == 2:
                            self.session.sendline('yes')
                        if login_stat == 3:
                            self.session.sendline(password)
                            if self.session.expect(['[Pp]assword:', r'[#>\]]\s*$']):
                                connected = True
                                break
                            else:
                                break  # Пробуем новый логин/пароль
                        if login_stat == 4:
                            connected = True
                    if connected:
                        self.login = login
                        self.password = password
                        break

        if self.protocol == 'telnet':
            self.session = pexpect.spawn(f'telnet {self.ip}')
            try:
                for login, password in zip(self.login, self.password):
                    while not connected:  # Если не авторизировались
                        login_stat = self.session.expect(
                            [
                                r"[Ll]ogin(?![-\siT]).*:\s*$",  # 0
                                r"[Uu]ser\s(?![lfp]).*:\s*$|User:$",  # 1
                                r"[Nn]ame.*:\s*$",  # 2
                                r'[Pp]ass.*:\s*$',  # 3
                                r'Connection closed',  # 4
                                r'Unable to connect',  # 5
                                r'[#>\]]\s*$',  # 6
                                r'Press any key to continue',  # 7
                                r'Timeout or some unexpected error happened on server host'  # 8 - Ошибка радиуса
                            ],
                            timeout=timeout
                        )
                        if login_stat == 7:  # Если необходимо нажать любую клавишу, чтобы продолжить
                            self.session.send(' ')
                            self.session.sendline(login)  # Вводим логин
                            self.session.sendline(password)  # Вводим пароль
                            self.session.expect(r'[#>\]]\s*')

                        if login_stat < 3:
                            self.session.sendline(login)  # Вводим логин
                            continue

                        elif 4 <= login_stat <= 5:
                            return f'Telnet недоступен! ({self.ip})'

                        elif login_stat == 3:
                            self.session.sendline(password)  # Вводим пароль
                            # Сохраняем текущие введенные логин и пароль, в надежде, что они являются верными
                            self.login = login
                            self.password = password
                            continue

                        elif login_stat == 6:  # Если был поймал символ начала ввода команды
                            connected = True  # Подключились
                        elif login_stat == 8:
                            continue  # Если ошибка радиуса, то вводим те же данные еще раз

                        break  # Выход из цикла

                    if connected:
                        break

                else:  # Если не удалось зайти под логинами и паролями из списка аутентификации
                    return f'Неверный логин или пароль! ({self.ip})'
            except pexpect.exceptions.TIMEOUT:
                return f'Login Error: Время ожидания превышено! ({self.ip})'

        return self.__get_device()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
        del self
