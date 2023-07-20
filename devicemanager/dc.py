"""
# Модуль для подключения к оборудованию через SSH, TELNET
"""
import re
import threading
import time
from dataclasses import dataclass
from threading import Thread
from typing import List

import pexpect
from .vendors import *
from .exceptions import (
    TelnetConnectionError,
    DeviceLoginError,
    UnknownDeviceError,
    SSHConnectionError,
)
from .session_control import DEVICE_SESSIONS


@dataclass
class SimpleAuthObject:
    login: str
    password: str
    secret: str = ""


class DeviceFactory:
    """
    # Подключение к оборудованию, определение вендора и возврат соответствующего экземпляра класса
    """

    prompt_expect = r"[#>\]]\s*$"

    login_input_expect = (
        r"[Ll]ogin(?![-\siT]).*:\s*$|[Uu]ser\s(?![lfp]).*:\s*$|User:$|[Nn]ame.*:\s*$"
    )
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
        self, ip: str, protocol: str, auth_obj, make_session_global: bool = True, pool_size: int = 1
    ):
        self.ip = ip
        self.session = None
        self.protocol = protocol
        self._session_global = make_session_global
        if not make_session_global:
            self.pool_size = 1
        else:
            self.pool_size = pool_size

        if isinstance(auth_obj, list):
            self.login = []
            self.password = []
            # Список объектов
            for auth in auth_obj:
                self.login.append(auth.login)
                self.password.append(auth.password)
                self.privilege_mode_password = auth.secret

        else:
            # Один объект
            self.login = [auth_obj.login]
            self.password = [auth_obj.password]
            self.privilege_mode_password = auth_obj.secret

    def __enter__(self, algorithm: str = "", cipher: str = "", timeout: int = 30) -> BaseDevice:
        """
        ## При входе в контекстный менеджер подключаемся к оборудованию.
        """

        start_time = time.perf_counter()

        if DEVICE_SESSIONS.has_pool(device_ip=self.ip):
            # Проверяем, что имеется пул, а если он еще создается, то необходимо подождать.
            # Иначе будет множественное создание пулов.
            # Ожидаем 30 сек.
            while (
                not DEVICE_SESSIONS.pool_is_created(self.ip)
                and time.perf_counter() - start_time < 30.0
            ):
                print("waiting for pool creation")
                time.sleep(0.5)

        if self._session_global and DEVICE_SESSIONS.has_connection(self.ip):
            print("GLOBAL")
            return DEVICE_SESSIONS.get_connection(self.ip)

        DEVICE_SESSIONS.add_pool(device_ip=self.ip, pool_size=self.pool_size)

        connections: List[BaseDevice] = []
        threads = []
        for i in range(self.pool_size):
            print("START THREAD")
            new_thread = Thread(
                target=lambda: connections.append(
                    self._get_device_session(algorithm, cipher, timeout)
                ),
                name=f"Get session for ip {self.ip} - {i}",
            )
            threads.append(new_thread)
            new_thread.start()

        for i in range(len(threads)):
            threads[i].join()

        print("GOT CONNECTIONS")

        if self._session_global:
            # Сохраняем новые сессии, если было указано хранение глобально.
            # Но для начала очистим пул от возможных не сброшенных подключений.
            DEVICE_SESSIONS.clear_pool(self.ip)
            DEVICE_SESSIONS.add_connections_to_pool(self.ip, connections)
        else:
            self.session = connections[0]

        return connections[0]

    def _get_device_session(self, algorithm: str = "", cipher: str = "", timeout: int = 30):
        connected = False

        if self.protocol == "ssh":
            algorithm_str = f" -oKexAlgorithms=+{algorithm}" if algorithm else ""
            cipher_str = f" -c {cipher}" if cipher else ""
            last_cipher_index = -1
            cipher_list = []

            for login, password in zip(self.login + ["admin"], self.password + ["admin"]):

                session = pexpect.spawn(
                    f"ssh {login}@{self.ip}{algorithm_str}{cipher_str}", timeout=15
                )

                while not connected:
                    expect_index = session.expect(
                        [
                            r"no matching key exchange method found",  # 0
                            r"no matching cipher found|Unknown cipher",  # 1
                            r"Are you sure you want to continue connecting",  # 2
                            self.password_input_expect,  # 3
                            self.prompt_expect,  # 4
                            self.send_N_key,  # 5
                            r"Connection closed",  # 6
                            r"Incorrect login",  # 7
                            pexpect.EOF,  # 8
                        ],
                        timeout=timeout,
                    )

                    if expect_index == 0:
                        session.expect(pexpect.EOF)
                        algorithm = re.findall(
                            r"Their offer: (\S+)", session.before.decode("utf-8")
                        )
                        if algorithm:
                            algorithm_str = f" -oKexAlgorithms=+{algorithm[0]}"
                            session = pexpect.spawn(
                                f"ssh {login}@{self.ip}{algorithm_str}{cipher_str}"
                            )

                    elif expect_index == 1:
                        session.expect(pexpect.EOF)
                        if not cipher_list:
                            cipher_output = re.findall(
                                r"Their offer: (\S+)", session.before.decode("utf-8")
                            )
                            if cipher_output:
                                cipher_list = cipher_output[0].split(",")

                        if cipher_list:
                            last_cipher_index += 1
                            cipher_str = f" -c {cipher_list[last_cipher_index]}"
                            session = pexpect.spawn(
                                f"ssh {login}@{self.ip}{algorithm_str}{cipher_str}"
                            )

                    elif expect_index == 2:
                        session.sendline("yes")

                    elif expect_index == 3:
                        session.send(password + "\r")
                        # if session.expect(["[Pp]assword:", r"[#>\]]\s*$"]):
                        #     connected = True

                        # break  # Пробуем новый логин/пароль

                    elif expect_index == 4:
                        connected = True

                    elif expect_index == 5:
                        session.send("N\r")

                    elif expect_index == 7:
                        print(session.before)
                        raise DeviceLoginError(
                            "Неверный Логин/Пароль (подключение SSH)", ip=self.ip
                        )

                    elif expect_index in {6, 8}:
                        print(session.before)
                        raise SSHConnectionError("SSH недоступен", ip=self.ip)

                if connected:
                    self.login = login
                    self.password = password
                    break

        # TELNET
        else:
            session = pexpect.spawn(f"telnet {self.ip}", timeout=10)

            pre_set_index = None  # По умолчанию стартуем без начального индекса
            status = "Не был передал логин/пароль"
            for login, password in zip(self.login, self.password):

                status = self.__login_to_by_telnet(session, login, password, timeout, pre_set_index)

                if status == "Connected":
                    # Сохраняем текущие введенные логин и пароль, они являются верными
                    self.login = login
                    self.password = password
                    break

                if "Неверный логин или пароль" in status:
                    pre_set_index = 0  # Следующий ввод будет логином
                    continue

            else:
                raise DeviceLoginError(status, ip=self.ip)

        return self.get_device(session)

    def get_device(self, session: pexpect.spawn) -> BaseDevice:
        """
        # После подключения динамически определяем вендора оборудования и его модель

        Отправляем команду:

            # show version

        Ищем в выводе команды строчки, которые указывают на определенный вендор

        |           Вендор            |     Строка для определения    |
        |:----------------------------|:------------------------------|
        |             ZTE             |      " ZTE Corporation:"      |
        |           Huawei            |     "Unrecognized command"    |
        |            Cisco            |           "cisco"             |
        |          D-Link             |  "Next possible completions:" |
        |          Edge-Core          |      "Hardware version"       |
        |          Extreme            |          "ExtremeXOS"         |
        |           Q-Tech            |            "QTECH"            |
        |          Iskratel           |   "ISKRATEL" или "IskraTEL"   |
        |           Juniper           |            "JUNOS"            |
        |          ProCurve           |         "Image stamp:"        |

        """

        auth = {
            "login": self.login,
            "password": self.password,
            "privilege_mode_password": self.privilege_mode_password,
        }

        version = self.send_command(session, "show version")

        if "bad command name show" in version:
            version = self.send_command(session, "system resource print")

        # Mikrotik
        if "mikrotik" in version.lower():
            return MikroTik(session, self.ip, auth)

        # ProCurve
        if "Image stamp:" in version:
            return ProCurve(session, self.ip, auth)

        # ZTE
        if " ZTE Corporation:" in version:
            model = BaseDevice.find_or_empty(r"Module 0:\s*(\S+\s\S+);\s*fasteth", version)
            return ZTE(session, self.ip, auth, model=model)

        # HUAWEI
        if "Unrecognized command" in version:
            version = self.send_command(session, "display version")
            if "huawei" in version.lower():
                if "CX600" in version:
                    model = BaseDevice.find_or_empty(
                        r"HUAWEI (\S+) uptime", version, flags=re.IGNORECASE
                    )
                    return HuaweiCX600(session, self.ip, auth, model=model)
                if "quidway" in version.lower():
                    return Huawei(session, self.ip, auth)

            # Если снова 'Unrecognized command', значит недостаточно прав, пробуем Huawei
            if "Unrecognized command" in version:
                return Huawei(session, self.ip, auth)

        # CISCO
        if "cisco" in version.lower():
            model = BaseDevice.find_or_empty(r"Model number\s*:\s*(\S+)", version)
            return Cisco(session, self.ip, auth, model=model)

        # D-LINK
        if "Next possible completions:" in version:
            return Dlink(session, self.ip, auth)

        # Edge Core
        if "Hardware version" in version:
            return EdgeCore(session, self.ip, auth)

        # Eltex LTP
        if "Eltex LTP" in version:
            model = BaseDevice.find_or_empty(r"Eltex (\S+[^:\s])", version)
            if re.match(r"LTP-[48]X", model):
                return EltexLTP(session, self.ip, auth, model=model)
            if "LTP-16N" in model:
                return EltexLTP16N(session, self.ip, auth, model=model)

        # Eltex MES, ESR
        if "Active-image:" in version or "Boot version:" in version:
            eltex_device = EltexBase(session, self.ip, self.privilege_mode_password)
            if "MES" in eltex_device.model:
                return EltexMES(
                    eltex_device.session,
                    self.ip,
                    auth,
                    model=eltex_device.model,
                    mac=eltex_device.mac,
                )
            if "ESR" in eltex_device.model:
                return EltexESR(
                    eltex_device.session,
                    self.ip,
                    auth,
                    model=eltex_device.model,
                    mac=eltex_device.mac,
                )

        # Extreme
        if "ExtremeXOS" in version:
            return Extreme(session, self.ip, auth)

        # Q-Tech
        if "QTECH" in version:
            model = BaseDevice.find_or_empty(r"\s+(\S+)\s+Device", version)
            return Qtech(session, self.ip, auth, model=model)

        # ISKRATEL CONTROL
        if "ISKRATEL" in version:
            return IskratelControl(session, self.ip, auth, model="ISKRATEL Switching")

        # ISKRATEL mBAN>
        if "IskraTEL" in version:
            model = BaseDevice.find_or_empty(r"CPU: IskraTEL \S+ (\S+)", version)
            return IskratelMBan(session, self.ip, auth, model=model)

        if "JUNOS" in version:
            model = BaseDevice.find_or_empty(r"Model: (\S+)", version)
            return Juniper(session, self.ip, auth, model)

        if "% Unknown command" in version:
            session.sendline("display version")
            while True:
                match = session.expect([r"]$", "---- More", r">$", r"#", pexpect.TIMEOUT, "{"])
                if match == 5:
                    session.expect(r"\}:")
                    session.sendline("\n")
                    continue
                version += str(session.before.decode("utf-8"))
                if match == 1:
                    session.sendline(" ")
                elif match == 4:
                    session.sendcontrol("C")
                else:
                    break
            if re.findall(r"VERSION : MA5600", version):
                model = BaseDevice.find_or_empty(r"VERSION : (MA5600\S+)", version)
                return HuaweiMA5600T(session, self.ip, auth, model=model)

        if "show: invalid command, valid commands are" in version:
            session.sendline("sys info show")
            while True:
                match = session.expect([r"]$", "---- More", r">\s*$", r"#\s*$", pexpect.TIMEOUT])
                version += str(session.before.decode("utf-8"))
                if match == 1:
                    session.sendline(" ")
                if match == 4:
                    session.sendcontrol("C")
                else:
                    break

        if "unknown keyword show" in version:
            return Juniper(session, self.ip, auth)

        raise UnknownDeviceError("Модель оборудования не была распознана", ip=self.ip)

    def __login_to_by_telnet(
        self, session: pexpect.spawn, login: str, password: str, timeout: int, pre_expect_index=None
    ) -> str:

        login_try = 1

        while True:
            # Ловим команды
            if pre_expect_index is not None:
                expect_index = pre_expect_index
                pre_expect_index = None

            else:
                expect_index = session.expect(self.telnet_authentication_expect, timeout=timeout)

            # Login
            if expect_index == 0:

                if login_try > 1:
                    # Если это вторая попытка ввода логина, то предыдущий был неверный
                    return f"Неверный логин или пароль (подключение telnet)"

                session.send(login + "\r")  # Вводим логин
                login_try += 1
                continue

            # Password
            if expect_index == 1:
                session.send(password + "\r")  # Вводим пароль
                continue

            # PROMPT
            if expect_index == 2:  # Если был поймал символ начала ввода команды
                return "Connected"

            # TELNET FAIL
            if expect_index == 3:
                raise TelnetConnectionError(f"Telnet недоступен", ip=self.ip)

            # Press any key to continue
            if expect_index == 4:  # Если необходимо нажать любую клавишу, чтобы продолжить
                session.send(" ")
                session.send(login + "\r")  # Вводим логин
                session.send(password + "\r")  # Вводим пароль
                session.expect(r"[#>\]]\s*")

            # Timeout or some unexpected error happened on server host' - Ошибка радиуса
            elif expect_index == 5:
                login_try = 1
                continue  # Вводим те же данные еще раз

            # The password needs to be changed
            if expect_index == 6:
                session.send("N\r")  # Не меняем пароль, когда спрашивает
                continue

            break

    @staticmethod
    def send_command(session: pexpect.spawn, command: str) -> str:
        """
        # Простой метод для отправки команды с постраничной записью вывода результата
        """

        session.send(command + "\r")
        version = ""
        while True:
            match = session.expect(
                [
                    r"]$",  # 0
                    r"-More-|-+\(more.*?\)-+",  # 1
                    r">\s*$",  # 2
                    r"#\s*",  # 3
                    pexpect.TIMEOUT,  # 4
                ],
                timeout=3,
            )

            version += str(session.before.decode("utf-8"))
            if match == 1:
                session.send(" ")
            elif match == 4:
                session.sendcontrol("C")
            else:
                break
        return version

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        ## При выходе из контекстного менеджера завершаем сессию
        """

        if not self._session_global and self.session:
            self.session.close()
            del self
