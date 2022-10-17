import re
import pexpect
from .vendors import *


class DeviceFactory:
    """
    Подключение к оборудованию, определение вендора и возврат соответствующего класса
    """

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

    def send_command(self, command: str):
        """ Простой метод для отправки команды с постраничной записью вывода результата """

        self.session.sendline(command)
        version = ''
        while True:
            m = self.session.expect(
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
            if m == 1:
                self.session.send(' ')
            elif m == 4:
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
        elif ' ZTE Corporation:' in version:
            model = BaseDevice.find_or_empty(r'Module 0:\s*(\S+\s\S+);\s*fasteth', version)
            return ZTE(self.session, self.ip, auth, model=model)

        # HUAWEI
        elif 'Unrecognized command' in version:
            version = self.send_command('display version')
            if 'huawei' in version.lower():
                if 'CX600' in version:
                    model = BaseDevice.find_or_empty(r'HUAWEI (\S+) uptime', version, flags=re.IGNORECASE)
                    return HuaweiCX600(self.session, self.ip, auth, model=model)
                elif 'quidway':
                    return Huawei(self.session, self.ip, auth)

        # CISCO
        elif 'cisco' in version.lower():
            model = BaseDevice.find_or_empty(r'Model number\s*:\s*(\S+)', version)
            return Cisco(self.session, self.ip, auth, model=model)

        # D-LINK
        elif 'Next possible completions:' in version:
            return Dlink(self.session, self.ip, auth)

        # Edge Core
        elif 'Hardware version' in version:
            return EdgeCore(self.session, self.ip, auth)

        # Eltex
        elif 'Active-image:' in version or 'Boot version:' in version:
            d = EltexBase(self.session, self.ip, self.privilege_mode_password)
            if 'MES' in d.model:
                return EltexMES(d.session, self.ip, auth, model=d.model, mac=d.mac)
            elif 'ESR' in d.model:
                return EltexESR(d.session, self.ip, auth, model=d.model, mac=d.mac)

        # Extreme
        elif 'ExtremeXOS' in version:
            return Extreme(self.session, self.ip, auth)

        # Q-Tech
        elif 'QTECH' in version:
            model = BaseDevice.find_or_empty(r'\s+(\S+)\s+Device', version)
            return Qtech(self.session, self.ip, auth, model=model)

        # ISKRATEL CONTROL
        elif 'ISKRATEL' in version:
            return IskratelControl(self.session, self.ip, auth, model='ISKRATEL Switching')

        # ISKRATEL mBAN>
        elif 'IskraTEL' in version:
            model = BaseDevice.find_or_empty(r'CPU: IskraTEL \S+ (\S+)', version)
            return IskratelMBan(self.session, self.ip, auth, model=model)

        elif 'JUNOS' in version:
            model = BaseDevice.find_or_empty(r'Model: (\S+)', version)
            return Juniper(self.session, self.ip, auth, model)

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
            if re.findall(r'VERSION : MA5600', version):
                model = BaseDevice.find_or_empty(r'VERSION : (MA5600\S+)', version)
                return HuaweiMA5600T(self.session, self.ip, auth, model=model)

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
            return Juniper(self.session, self.ip, auth)

        else:
            return 'Не удалось распознать оборудование'

    def __enter__(self, algorithm: str = '', cipher: str = '', timeout: int = 30):
        connected = False
        if self.protocol == 'ssh':
            algorithm_str = f' -oKexAlgorithms=+{algorithm}' if algorithm else ''
            cipher_str = f' -c {cipher}' if cipher else ''

            for login, password in zip(self.login + ['admin'], self.password + ['admin']):

                self.session = pexpect.spawn(f'ssh {login}@{self.ip}{algorithm_str}{cipher_str}')

                while not connected:
                    login_stat = self.session.expect(
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
                    if login_stat == 0:
                        self.session.expect(pexpect.EOF)
                        algorithm = re.findall(r'Their offer: (\S+)', self.session.before.decode('utf-8'))
                        if algorithm:
                            algorithm_str = f' -oKexAlgorithms=+{algorithm[0]}'
                            self.session = pexpect.spawn(
                                f'ssh {login}@{self.ip}{algorithm_str}{cipher_str}'
                            )
                    elif login_stat == 1:
                        self.session.expect(pexpect.EOF)
                        cipher = re.findall(r'Their offer: (\S+)', self.session.before.decode('utf-8'))
                        if cipher:
                            cipher_str = f' -c {cipher[0].split(",")[-1]}'
                            self.session = pexpect.spawn(
                                f'ssh {login}@{self.ip}{algorithm_str}{cipher_str}'
                            )
                    elif login_stat == 2:
                        self.session.sendline('yes')
                    elif login_stat == 3:
                        self.session.sendline(password)
                        if self.session.expect(['[Pp]assword:', r'[#>\]]\s*$']):
                            connected = True
                            break
                        else:
                            break  # Пробуем новый логин/пароль
                    elif login_stat == 4:
                        connected = True
                    elif login_stat == 6:
                        self.session.sendline('N')

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
                                r'Timeout or some unexpected error happened on server host',  # 8 - Ошибка радиуса
                                r'The password needs to be changed'  # 9
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
                        elif login_stat == 9:
                            self.session.sendline('N')
                            continue

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
