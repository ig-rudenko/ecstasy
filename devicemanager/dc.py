"""
Модуль для подключения к оборудованию через SSH, TELNET
"""

import re
import pexpect
from .vendors import *


class DeviceFactory:
    """
    Подключение к оборудованию, определение вендора и возврат соответствующего класса
    """

    prompt_expect = r'[#>\]]\s*$'

    login_input_expect = r"[Ll]ogin(?![-\siT]).*:\s*$|[Uu]ser\s(?![lfp]).*:\s*$|User:$|[Nn]ame.*:\s*$"
    password_input_expect = r'[Pp]ass.*:\s*$'

    telnet_unavailable = r'Connection closed|Unable to connect'

    authentication_expect = [
        login_input_expect,  # 0
        password_input_expect,  # 1
        prompt_expect,  # 2
        telnet_unavailable,  # 3
        r'Press any key to continue',  # 4
        r'Timeout or some unexpected error happened on server host',  # 5 - Ошибка радиуса
        r'The password needs to be changed'  # 6
    ]

    def __init__(self, ip: str, protocol: str, auth_obj=None):
        self.ip = ip
        self.session: pexpect.spawn
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

    def send_command(self, command: str):
        """ Простой метод для отправки команды с постраничной записью вывода результата """

        self.session.sendline(command)
        version = ''
        while True:
            match = self.session.expect(
                [
                    r']$',
                    r'-More-|-+\(more.*?\)-+',
                    r'>\s*$',
                    r'#\s*',
                    pexpect.TIMEOUT
                ],
                timeout=3
            )

            version += str(self.session.before.decode('utf-8'))
            if match == 1:
                self.session.send(' ')
            elif match == 4:
                self.session.sendcontrol('C')
            else:
                break
        return version

    def __get_device(self):
        auth = {
            'login': self.login,
            'password': self.password,
            'privilege_mode_password': self.privilege_mode_password
        }

        version = self.send_command('show version')

        # ProCurve
        if 'Image stamp:' in version:
            return ProCurve(self.session, self.ip, auth)

        # ZTE
        if ' ZTE Corporation:' in version:
            model = BaseDevice.find_or_empty(r'Module 0:\s*(\S+\s\S+);\s*fasteth', version)
            return ZTE(self.session, self.ip, auth, model=model)

        # HUAWEI
        if 'Unrecognized command' in version:
            version = self.send_command('display version')
            if 'huawei' in version.lower():
                if 'CX600' in version:
                    model = BaseDevice.find_or_empty(r'HUAWEI (\S+) uptime', version, flags=re.IGNORECASE)
                    return HuaweiCX600(self.session, self.ip, auth, model=model)
                if 'quidway' in version.lower():
                    return Huawei(self.session, self.ip, auth)

            # Если снова 'Unrecognized command', значит недостаточно прав, пробуем Huawei
            if 'Unrecognized command' in version:
                return Huawei(self.session, self.ip, auth)

        # CISCO
        if 'cisco' in version.lower():
            model = BaseDevice.find_or_empty(r'Model number\s*:\s*(\S+)', version)
            return Cisco(self.session, self.ip, auth, model=model)

        # D-LINK
        if 'Next possible completions:' in version:
            return Dlink(self.session, self.ip, auth)

        # Edge Core
        if 'Hardware version' in version:
            return EdgeCore(self.session, self.ip, auth)

        # Eltex
        if 'Active-image:' in version or 'Boot version:' in version:
            eltex_device = EltexBase(self.session, self.ip, self.privilege_mode_password)
            if 'MES' in eltex_device.model:
                return EltexMES(eltex_device.session, self.ip, auth, model=eltex_device.model, mac=eltex_device.mac)
            if 'ESR' in eltex_device.model:
                return EltexESR(eltex_device.session, self.ip, auth, model=eltex_device.model, mac=eltex_device.mac)

        # Extreme
        if 'ExtremeXOS' in version:
            return Extreme(self.session, self.ip, auth)

        # Q-Tech
        if 'QTECH' in version:
            model = BaseDevice.find_or_empty(r'\s+(\S+)\s+Device', version)
            return Qtech(self.session, self.ip, auth, model=model)

        # ISKRATEL CONTROL
        if 'ISKRATEL' in version:
            return IskratelControl(self.session, self.ip, auth, model='ISKRATEL Switching')

        # ISKRATEL mBAN>
        if 'IskraTEL' in version:
            model = BaseDevice.find_or_empty(r'CPU: IskraTEL \S+ (\S+)', version)
            return IskratelMBan(self.session, self.ip, auth, model=model)

        if 'JUNOS' in version:
            model = BaseDevice.find_or_empty(r'Model: (\S+)', version)
            return Juniper(self.session, self.ip, auth, model)

        if '% Unknown command' in version:
            self.session.sendline('display version')
            while True:
                match = self.session.expect([r']$', '---- More', r'>$', r'#', pexpect.TIMEOUT, '{'])
                if match == 5:
                    self.session.expect(r'\}:')
                    self.session.sendline('\n')
                    continue
                version += str(self.session.before.decode('utf-8'))
                if match == 1:
                    self.session.sendline(' ')
                elif match == 4:
                    self.session.sendcontrol('C')
                else:
                    break
            if re.findall(r'VERSION : MA5600', version):
                model = BaseDevice.find_or_empty(r'VERSION : (MA5600\S+)', version)
                return HuaweiMA5600T(self.session, self.ip, auth, model=model)

        if 'show: invalid command, valid commands are' in version:
            self.session.sendline('sys info show')
            while True:
                match = self.session.expect([r']$', '---- More', r'>\s*$', r'#\s*$', pexpect.TIMEOUT])
                version += str(self.session.before.decode('utf-8'))
                if match == 1:
                    self.session.sendline(' ')
                if match == 4:
                    self.session.sendcontrol('C')
                else:
                    break
            if 'ZyNOS version' in version:
                pass  # TODO Для Zyxel

        if 'unknown keyword show' in version:
            return Juniper(self.session, self.ip, auth)

        return 'Не удалось распознать оборудование'

    def __login_to_by_telnet(self, login: str, password: str, timeout: int, pre_expect_index=None) -> str:

        login_try = 1

        try:
            while True:
                # Ловим команды
                if pre_expect_index is not None:
                    expect_index = pre_expect_index
                    pre_expect_index = None

                else:
                    expect_index = self.session.expect(
                        self.authentication_expect,
                        timeout=timeout
                    )

                print(expect_index)

                # Login
                if expect_index == 0:

                    if login_try > 1:
                        print('login ', login_try)
                        # Если это вторая попытка ввода логина, то предыдущий был неверный
                        return f'Неверный логин или пароль! ({self.ip})'

                    self.session.sendline(login)  # Вводим логин
                    login_try += 1
                    continue

                # Password
                if expect_index == 1:
                    self.session.sendline(password)  # Вводим пароль
                    continue

                # PROMPT
                if expect_index == 2:  # Если был поймал символ начала ввода команды
                    return 'Connected'

                # TELNET FAIL
                if expect_index == 3:
                    return f'Telnet недоступен! ({self.ip})'

                # Press any key to continue
                if expect_index == 4:  # Если необходимо нажать любую клавишу, чтобы продолжить
                    self.session.send(' ')
                    self.session.sendline(login)  # Вводим логин
                    self.session.sendline(password)  # Вводим пароль
                    self.session.expect(r'[#>\]]\s*')

                # Timeout or some unexpected error happened on server host' - Ошибка радиуса
                elif expect_index == 5:
                    continue  # Вводим те же данные еще раз

                # The password needs to be changed
                if expect_index == 6:
                    self.session.sendline('N')  # Не меняем пароль, когда спрашивает
                    continue

                break

        except pexpect.exceptions.TIMEOUT:
            return f'Login Error: Время ожидания превышено! ({self.ip})'

    def __enter__(self, algorithm: str = '', cipher: str = '', timeout: int = 30):
        connected = False
        if self.protocol == 'ssh':
            algorithm_str = f' -oKexAlgorithms=+{algorithm}' if algorithm else ''
            cipher_str = f' -c {cipher}' if cipher else ''

            for login, password in zip(self.login + ['admin'], self.password + ['admin']):

                self.session = pexpect.spawn(f'ssh {login}@{self.ip}{algorithm_str}{cipher_str}')

                while not connected:
                    expect_index = self.session.expect(
                        [
                            r'no matching key exchange method found',  # 0
                            r'no matching cipher found',  # 1
                            r'Are you sure you want to continue connecting',  # 2
                            r'[Pp]assword:',  # 3
                            r'[#>\]]\s*$',  # 4
                            r'Connection closed',  # 5
                            r'The password needs to be changed'  # 6
                        ],
                        timeout=timeout
                    )

                    if expect_index == 0:
                        self.session.expect(pexpect.EOF)
                        algorithm = re.findall(r'Their offer: (\S+)', self.session.before.decode('utf-8'))
                        if algorithm:
                            algorithm_str = f' -oKexAlgorithms=+{algorithm[0]}'
                            self.session = pexpect.spawn(
                                f'ssh {login}@{self.ip}{algorithm_str}{cipher_str}'
                            )

                    elif expect_index == 1:
                        self.session.expect(pexpect.EOF)
                        cipher = re.findall(r'Their offer: (\S+)', self.session.before.decode('utf-8'))
                        if cipher:
                            cipher_str = f' -c {cipher[0].split(",")[-1]}'
                            self.session = pexpect.spawn(
                                f'ssh {login}@{self.ip}{algorithm_str}{cipher_str}'
                            )

                    elif expect_index == 2:
                        self.session.sendline('yes')

                    elif expect_index == 3:
                        self.session.sendline(password)
                        if self.session.expect(['[Pp]assword:', r'[#>\]]\s*$']):
                            connected = True

                        break  # Пробуем новый логин/пароль

                    elif expect_index == 4:
                        connected = True

                    elif expect_index == 6:
                        self.session.sendline('N')

                if connected:
                    self.login = login
                    self.password = password
                    break

        if self.protocol == 'telnet':
            self.session = pexpect.spawn(f'telnet {self.ip}')

            pre_set_index = None  # По умолчанию стартуем без начального индекса
            status = 'Не был передал логин/пароль'
            for login, password in zip(self.login, self.password):

                status = self.__login_to_by_telnet(login, password, timeout, pre_set_index)

                if status == 'Connected':
                    # Сохраняем текущие введенные логин и пароль, они являются верными
                    self.login = login
                    self.password = password
                    break

                if 'Неверный логин или пароль' in status:
                    pre_set_index = 0  # Следующий ввод будет логином
                    continue

                if 'Telnet недоступен' in status or 'Время ожидания превышено' in status:
                    return status

            else:
                return status

        return self.__get_device()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
        del self
