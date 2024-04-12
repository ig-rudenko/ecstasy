"""
# Модуль для подключения к оборудованию через SSH, TELNET
"""
import re
from dataclasses import dataclass

import pexpect

from .exceptions import (
    TelnetConnectionError,
    DeviceLoginError,
    SSHConnectionError,
)
from .multifactory import DeviceMultiFactory
from .vendors.base.device import BaseDevice


@dataclass
class SimpleAuthObject:
    login: str
    password: str
    secret: str = ""


class SSHSpawn:
    def __init__(self, ip, login):
        self.ip = ip
        self.login = login
        self.kex_algorithms = ""
        self.host_key_algorithms = ""
        self.ciphers = ""

    @staticmethod
    def _get_algorithm(output: str) -> str:
        algorithms = re.findall(r"Their offer: (\S+)", output)
        if algorithms:
            return algorithms[0]
        return ""

    def get_kex_algorithms(self, output: str):
        self.kex_algorithms = self._get_algorithm(output)

    def get_host_key_algorithms(self, output: str):
        self.host_key_algorithms = self._get_algorithm(output)

    def get_ciphers(self, output: str):
        self.ciphers = self._get_algorithm(output)

    def get_spawn_string(self) -> str:
        base = f"ssh -p 22 {self.login}@{self.ip}"

        if self.kex_algorithms:
            base += f" -oKexAlgorithms=+{self.kex_algorithms}"

        if self.host_key_algorithms:
            base += f" -oHostKeyAlgorithms=+{self.host_key_algorithms}"

        if self.ciphers:
            base += f" -c {self.ciphers}"

        return base

    def get_session(self):
        return pexpect.spawn(self.get_spawn_string(), timeout=15)


class DeviceRemoteConnector:
    """
    # Подключение к оборудованию, определение вендора и возврат соответствующего экземпляра класса
    """

    prompt_expect = r"[#>\]]\s*$"

    login_input_expect = r"[Ll]ogin(?![-\siT]).*:\s*$|[Uu]ser\s(?![lfp]).*:\s*$|User:$|[Nn]ame.*:\s*$"
    password_input_expect = r"[Pp]ass.*:\s*$"

    # Совпадения, после которых надо нажать `N` (no)
    send_N_key = r"The password needs to be changed|Do you want to see the software license"

    # Не доступен telnet
    telnet_unavailable = r"Connection closed|Unable to connect"

    telnet_authentication_expect = [
        login_input_expect,  # 0
        password_input_expect,  # 1
        prompt_expect,  # 2
        telnet_unavailable,  # 3
        r"Press any key to continue",  # 4
        r"Timeout or some unexpected error happened on server host",  # 5 - Ошибка радиуса
        send_N_key,  # 6 Нажать `N`
    ]

    def __init__(
        self,
        ip: str,
        protocol: str,
        snmp_community: str,
        auth_obj,
    ):
        self.ip = ip
        self.session = None
        self.snmp_community = snmp_community
        self.protocol = protocol

        self.login: str = auth_obj.login
        self.password: str = auth_obj.password
        self.privilege_mode_password: str = auth_obj.secret

    def get_session(self) -> BaseDevice:
        return self._get_device_session()

    def __enter__(self) -> BaseDevice:
        """
        ## При входе в контекстный менеджер подключаемся к оборудованию.
        """
        return self._get_device_session()

    def _get_device_session(self) -> BaseDevice:
        if self.protocol == "ssh":
            self.session = self._connect_by_ssh()
        else:
            self.session = self._connect_by_telnet()

        return DeviceMultiFactory.get_device(
            self.session,
            ip=self.ip,
            auth={
                "login": self.login,
                "password": self.password,
                "privilege_mode_password": self.privilege_mode_password,
            },
            snmp_community=self.snmp_community,
        )

    def _connect_by_ssh(self):
        connected = False
        session = None

        try:
            ssh_spawn = SSHSpawn(ip=self.ip, login=self.login)
            session = ssh_spawn.get_session()

            while not connected:
                expect_index = session.expect(
                    [
                        r"no matching key exchange method found",  # 0
                        r"no matching host key type found",  # 1
                        r"no matching cipher found|Unknown cipher",  # 2
                        r"Are you sure you want to continue connecting",  # 3
                        self.password_input_expect,  # 4
                        self.prompt_expect,  # 5
                        self.send_N_key,  # 6
                        r"Connection closed",  # 7
                        r"Incorrect login",  # 8
                        pexpect.EOF,  # 9,
                        self.login_input_expect,  # 10
                    ],
                    timeout=30,
                )

                if expect_index == 0:
                    # KexAlgorithms
                    session.expect(pexpect.EOF)
                    ssh_spawn.get_kex_algorithms(session.before.decode("utf-8"))
                    session = ssh_spawn.get_session()

                elif expect_index == 1:
                    # HostKeyAlgorithms
                    session.expect(pexpect.EOF)
                    ssh_spawn.get_host_key_algorithms(session.before.decode("utf-8"))
                    session = ssh_spawn.get_session()

                elif expect_index == 2:
                    # Cipher
                    session.expect(pexpect.EOF)
                    ssh_spawn.get_ciphers(session.before.decode("utf-8"))
                    session = ssh_spawn.get_session()

                elif expect_index == 3:
                    # Continue connection?
                    session.sendline("yes")

                elif expect_index == 4:
                    session.send(self.password + "\r")

                elif expect_index == 5:
                    # Got prompt
                    connected = True

                elif expect_index == 6:
                    session.send("N\r")

                elif expect_index == 8:
                    session.close()
                    raise DeviceLoginError("Неверный Логин/Пароль (подключение SSH)", ip=self.ip)

                elif expect_index in (7, 9):
                    session.close()
                    raise SSHConnectionError(
                        "SSH недоступен" + session.before.decode("utf-8"),
                        ip=self.ip,
                    )
                elif expect_index == 10:
                    session.send(self.login + "\r")  # Login

        except Exception as exc:
            if session is not None and session.isalive():
                session.close()
            raise exc

        return session

    def _connect_by_telnet(self):
        session = None
        timeout = 20
        try:
            session = pexpect.spawn(f"telnet {self.ip}", timeout=timeout)

            status = self.__login_to_by_telnet(session, self.login, self.password, timeout)

            if status != "Connected":
                session.close()
                raise DeviceLoginError(status, ip=self.ip)

        except Exception as exc:
            if session is not None and session.isalive():
                session.close()
            raise exc

        return session

    def __login_to_by_telnet(self, session, login: str, password: str, timeout: int) -> str:
        login_try = 1

        while True:
            expect_index = session.expect(self.telnet_authentication_expect, timeout=timeout)

            # Login
            if expect_index == 0:
                if login_try > 1:
                    # Если это вторая попытка ввода логина, то предыдущий был неверный
                    return "Неверный логин или пароль (подключение telnet)"

                session.send(login + "\r")  # Вводим логин
                login_try += 1
                continue

            # Password
            if expect_index == 1:
                session.send(password + "\r")  # Вводим пароль
                continue

            # PROMPT
            if expect_index == 2:  # Если был пойман символ начала ввода команды
                return "Connected"

            # TELNET FAIL
            if expect_index == 3:
                raise TelnetConnectionError("Telnet недоступен", ip=self.ip)

            # Press any key to continue
            if expect_index == 4:
                # Если необходимо нажать любую клавишу, чтобы продолжить
                session.send(" ")
                session.send(login + "\r")  # Вводим логин
                session.send(password + "\r")  # Вводим пароль
                session.expect(r"[#>\]]\s*")
                return "Connected"

            # Timeout or some unexpected error happened on server host' - Ошибка радиуса
            if expect_index == 5:
                login_try = 1
                continue  # Вводим те же данные еще раз

            # The password needs to be changed
            if expect_index == 6:
                session.send("N\r")  # Не меняем пароль, когда спрашивает
                continue

            break

        return ""

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        ## При выходе из контекстного менеджера завершаем сессию
        """

        if self.session and self.session.isalive():
            self.session.close()
