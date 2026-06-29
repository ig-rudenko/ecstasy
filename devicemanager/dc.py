"""
# Модуль для подключения к оборудованию через SSH, TELNET
"""

import os
import re
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime

import pexpect

from .connection_ports import normalize_connection_ports
from .device_connector.ssh_host_keys import SSHKnownHostsStore
from .exceptions import (
    DeviceException,
    DeviceLoginError,
    SSHConnectionError,
    TelnetConnectionError,
)
from .multifactory import DeviceMultiFactory
from .session_spawner import SessionSpawner
from .vendors.base.device import BaseDevice
from .vendors.base.types import SimpleAuthObjectProtocol

TRUE_VALUES = {"1", "true", "yes", "on"}


@dataclass
class SimpleAuthObject:
    login: str
    password: str
    secret: str = ""


class SSHSpawn:
    def __init__(self, ip, login, port: int = 22):
        self.ip = ip
        self.login = login
        self.port = port
        self.kex_algorithms = ""
        self.host_key_algorithms = ""
        self.ciphers = ""
        self.macs = ""

    @staticmethod
    def _get_supported_algorithms(query: str) -> set[str] | None:
        """Вернуть алгоритмы указанного типа, поддерживаемые локальным OpenSSH."""

        try:
            result = subprocess.run(
                ["ssh", "-Q", query],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            return None
        if result.returncode != 0:
            return None
        return {algorithm.strip() for algorithm in result.stdout.splitlines() if algorithm.strip()}

    @classmethod
    def _get_algorithm(cls, output: str, query: str) -> str:
        """Вернуть первый предложенный алгоритм, поддерживаемый локальным OpenSSH."""

        algorithms = re.findall(r"Their offer: (\S+)", output)
        if not algorithms:
            return ""

        offered_algorithms = algorithms[0].split(",")
        supported_algorithms = cls._get_supported_algorithms(query)
        if supported_algorithms is None:
            return offered_algorithms[0]
        for algorithm in offered_algorithms:
            if algorithm in supported_algorithms:
                return algorithm
        return ""

    def get_kex_algorithms(self, output: str):
        self.kex_algorithms = self._get_algorithm(output, "kex")

    def get_host_key_algorithms(self, output: str):
        self.host_key_algorithms = self._get_algorithm(output, "key")

    def get_ciphers(self, output: str):
        self.ciphers = self._get_algorithm(output, "cipher")

    def get_macs(self, output: str):
        """Сохранить поддерживаемый MAC из предложения SSH-сервера."""

        self.macs = self._get_algorithm(output, "mac")

    def get_spawn_string(self) -> str:
        base = f"ssh -p {self.port} {self.login}@{self.ip}"

        if self.kex_algorithms:
            base += f" -oKexAlgorithms=+{self.kex_algorithms}"

        if self.host_key_algorithms:
            base += f" -oHostKeyAlgorithms=+{self.host_key_algorithms}"

        if self.ciphers:
            base += f" -c {self.ciphers}"

        if self.macs:
            base += f" -oMACs=+{self.macs}"

        return base

    def get_session(self):
        return SessionSpawner(self.get_spawn_string(), ip=self.ip, timeout=15)

    def accept_changed_host_key(self, ssh_output: str) -> None:
        """Atomically trust the SSH key reported by this connection."""

        SSHKnownHostsStore().accept_changed(
            self.ip,
            self.port,
            datetime.now(UTC),
            ssh_output,
        )


class DeviceRemoteConnector:
    """
    # Подключение к оборудованию, определение вендора и возврат соответствующего экземпляра класса
    """

    prompt_expect = "|".join(
        [
            r"[#>\]]\s*$",  # Normal prompt
            r"[#>\]]\s*\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])|\x08$",  # ANSI escape sequence
        ]
    )

    login_input_expect = "|".join(
        [
            r"[Ll]ogin(?![-\siT]).*:\s*$",
            r"[Uu]ser\s(?![Alfp]).*:\s*$",
            r"User:$",
            r"[Nn]ame.*:\s*$",
            r"Enter Login Name",
        ]
    )
    password_input_expect = "|".join(
        [
            r"[Pp]ass.*:\s*$",
            r"Please Enter Password",
        ]
    )

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
        "The user has been locked",  # 7
    ]

    def __init__(
        self,
        ip: str,
        protocol: str,
        snmp_community: str,
        auth_obj: SimpleAuthObjectProtocol,
        telnet_port: int | None = None,
        ssh_port: int | None = None,
        snmp_port: int | None = None,
    ):
        ports = normalize_connection_ports(
            telnet_port=telnet_port,
            ssh_port=ssh_port,
            snmp_port=snmp_port,
        )
        self.ip = ip
        self.session: SessionSpawner | None = None
        self.snmp_community = snmp_community
        self.snmp_port = ports.snmp_port
        self.telnet_port = ports.telnet_port
        self.ssh_port = ports.ssh_port
        self.protocol = protocol

        self.login = str(auth_obj.login)
        self.password = str(auth_obj.password)
        self.privilege_mode_password = str(auth_obj.secret)

    def get_session(self) -> BaseDevice:
        return self._get_device_session()

    def __enter__(self) -> BaseDevice:
        """
        ## При входе в контекстный менеджер подключаемся к оборудованию.
        """
        return self._get_device_session()

    def _get_device_session(self) -> BaseDevice:
        if self.protocol == "telnet":
            session = self._connect_by_telnet()
        elif self.protocol == "ssh":
            session = self._connect_by_ssh()
        else:
            raise DeviceException(f"Unknown protocol: {self.protocol!r}")

        self.session = session

        device = DeviceMultiFactory.get_device(
            session,
            ip=self.ip,
            auth={
                "login": self.login,
                "password": self.password,
                "privilege_mode_password": self.privilege_mode_password,
            },
            snmp_community=self.snmp_community,
            snmp_port=self.snmp_port,
        )
        device.connection_protocol = self.protocol
        return device

    def _connect_by_ssh(self) -> SessionSpawner:
        connected = False
        session = None
        negotiation_restarts = 0
        max_negotiation_restarts = 4
        host_key_restarts = 0

        try:
            ssh_spawn = SSHSpawn(ip=self.ip, login=self.login, port=self.ssh_port)
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
                        r"HOST IDENTIFICATION HAS CHANGED",  # 11
                        r"no matching MAC found",  # 12
                    ],
                    timeout=30,
                )
                session.save_before()

                if expect_index == 0:
                    # KexAlgorithms
                    session.expect(pexpect.EOF)
                    ssh_spawn.get_kex_algorithms(session.before.decode("utf-8", errors="ignore"))
                    negotiation_restarts += 1
                    self._validate_ssh_negotiation(
                        ssh_spawn.kex_algorithms,
                        "KexAlgorithms",
                        negotiation_restarts,
                        max_negotiation_restarts,
                    )
                    session = ssh_spawn.get_session()

                elif expect_index == 1:
                    # HostKeyAlgorithms
                    session.expect(pexpect.EOF)
                    ssh_spawn.get_host_key_algorithms(session.before.decode("utf-8", errors="ignore"))
                    negotiation_restarts += 1
                    self._validate_ssh_negotiation(
                        ssh_spawn.host_key_algorithms,
                        "HostKeyAlgorithms",
                        negotiation_restarts,
                        max_negotiation_restarts,
                    )
                    session = ssh_spawn.get_session()

                elif expect_index == 2:
                    # Cipher
                    session.expect(pexpect.EOF)
                    ssh_spawn.get_ciphers(session.before.decode("utf-8", errors="ignore"))
                    negotiation_restarts += 1
                    self._validate_ssh_negotiation(
                        ssh_spawn.ciphers,
                        "cipher",
                        negotiation_restarts,
                        max_negotiation_restarts,
                    )
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
                        "SSH недоступен" + session.before.decode("utf-8", errors="ignore"),
                        ip=self.ip,
                    )
                elif expect_index == 10:
                    session.send(self.login + "\r")  # Login
                elif expect_index == 11:
                    warning_parts = [session.before, session.after]
                    session.expect(pexpect.EOF)
                    warning_parts.append(session.before)
                    ssh_output = "".join(
                        part.decode("utf-8", errors="ignore") if isinstance(part, bytes) else str(part)
                        for part in warning_parts
                    )
                    session.close()
                    auto_accept_host_key = (
                        os.getenv("DEVICE_CONNECTOR_AUTO_ACCEPT_CHANGED_SSH_HOST_KEY", "0").lower()
                        in TRUE_VALUES
                    )
                    if not auto_accept_host_key or host_key_restarts >= 1:
                        raise SSHConnectionError(
                            "SSH HOST IDENTIFICATION HAS CHANGED",
                            ip=self.ip,
                            ssh_output=ssh_output,
                        )
                    host_key_restarts += 1
                    try:
                        ssh_spawn.accept_changed_host_key(ssh_output)
                    except Exception as exc:
                        raise SSHConnectionError(
                            "SSH HOST IDENTIFICATION HAS CHANGED",
                            ip=self.ip,
                            ssh_output=ssh_output,
                        ) from exc
                    session = ssh_spawn.get_session()
                elif expect_index == 12:
                    session.expect(pexpect.EOF)
                    ssh_spawn.get_macs(session.before.decode("utf-8", errors="ignore"))
                    negotiation_restarts += 1
                    self._validate_ssh_negotiation(
                        ssh_spawn.macs,
                        "MAC",
                        negotiation_restarts,
                        max_negotiation_restarts,
                    )
                    session = ssh_spawn.get_session()

        except Exception as exc:
            if session is not None and session.isalive():
                session.close()
            raise exc

        session.save_before()
        return session

    def _validate_ssh_negotiation(
        self,
        algorithm: str,
        algorithm_type: str,
        restart_count: int,
        max_restarts: int,
    ) -> None:
        """Остановить SSH negotiation при нераспознанном ответе или цикле."""

        if not algorithm:
            raise SSHConnectionError(
                f"Не найден поддерживаемый SSH {algorithm_type} из предложения сервера",
                ip=self.ip,
            )
        if restart_count > max_restarts:
            raise SSHConnectionError(
                "Превышено число попыток согласования SSH-алгоритмов",
                ip=self.ip,
            )

    def _connect_by_telnet(self) -> SessionSpawner:
        session = None
        timeout = 20
        try:
            session = SessionSpawner(f"telnet {self.ip} {self.telnet_port}", ip=self.ip, timeout=timeout)

            status = self.__login_to_by_telnet(session, self.login, self.password, timeout)

            if status != "Connected":
                session.close()
                raise DeviceLoginError(status, ip=self.ip)

        except Exception as exc:
            if session is not None and session.isalive():
                session.close()
            raise exc

        session.save_before()
        return session

    def __login_to_by_telnet(self, session, login: str, password: str, timeout: int) -> str:
        login_try = 1

        while True:
            expect_index = session.expect(self.telnet_authentication_expect, timeout=timeout)
            session.save_before()

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

            if expect_index == 7:
                raise DeviceLoginError("Пользователь заблокирован", ip=self.ip)

            break

        return ""

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        ## При выходе из контекстного менеджера завершаем сессию
        """

        if self.session and self.session.isalive():
            self.session.close()
