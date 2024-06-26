from django.test import SimpleTestCase

from devicemanager.vendors.eltex import EltexLTP, EltexLTP16N
from .base_factory_test import AbstractTestFactory


class TestEltexLTP4XFactory(AbstractTestFactory):
    @staticmethod
    def get_device_class():
        return EltexLTP

    @staticmethod
    def get_output_from_show_version_command() -> str:
        return "Eltex LTP-4X-rev.B software version 3.44.0 build 292 on 16.11.2021 15:45"


class TestEltexLTP8XFactory(AbstractTestFactory):
    @staticmethod
    def get_device_class():
        return EltexLTP

    @staticmethod
    def get_output_from_show_version_command() -> str:
        return "Eltex LTP-8X-rev.C software version 3.44.0 build 294 on 16.11.2021 15:48"


class TestEltexLTP16NFactory(AbstractTestFactory):
    @staticmethod
    def get_device_class():
        return EltexLTP16N

    @staticmethod
    def get_output_from_show_version_command() -> str:
        return "    Eltex LTP-16N: software version 1.4.0 build 784 on 21.06.2022 07:38"


class EltexLTP4XPexpectFaker:
    """
    ## Это класс создает имитацию сессии pexpect для обработки команд Eltex LTP 4X.
    """

    def __init__(self) -> None:
        self.before: bytes = b""
        self.sent_commands: list[str] = []
        self.expect_cmd = 0

    def send(self, command: str) -> None:
        """
        ## Обрабатывает команду

        :param command: Команда для отправки в оболочку
        :type command: str
        """
        self.sent_commands.append(command)

        if command == "show interfaces status 10G-front-port 0 - 1\r":
            self.before = b"""
 show interfaces status 10G-front-port 0 - 1
Interface           Status       Media   Speed        Duplex      Flow control
10G-front-port 0    down         none    1000M        full        no
10G-front-port 1    down         none    10G          full        no
            """
        elif command == "show interfaces status front-port 0 - 3\r":
            self.before = b"""
 show interfaces status front-port 0 - 3
Interface           Status       Media   Speed        Duplex      Flow control
front-port 0        up           copper  1000M        full        no
front-port 1        down         none    auto         auto        no
front-port 2        down         none    auto         auto        no
front-port 3        down         none    auto         auto        no
            """
        elif command == "show interface gpon-port 0-3 state\r":
            self.before = b"""
    Reading:  .....
    Gpon-ports status information:
        Gpon-port:                               0                1                  2                  3
        State:                                  OK               OK                 OK                 OK
        ONT count:                               7                1                 56                 54
        ONT autofind:                      enabled          enabled            enabled            enabled
        SFP vendor:                        Hisense          Hisense              BAZIS              BAZIS
        SFP product number:          LTE3680P-BC+2    LTE3680P-BC+2    BZ-SFP-GPON-C++    BZ-SFP-GPON-C++
        SFP vendor revision:                    11               11                                      
        SFP temperature [C]:                    39               39                 42                 43
        SFP voltage [V]:                      3.25             3.24               3.22               3.18
        SFP tx bias current [mA]:             8.23             7.95              11.65               8.00
        SFP tx power [dBm]:                   7.78             7.76               6.05               5.91
            """
        elif "show mac include interface" in command:
            self.before = b"""
   Mac table
   ~~~~~~~~~
VID    MAC address         Interface                                  Type
----   -----------------   ----------------------------------------   --------
1052   44:8a:5b:70:a7:bf   front-port 0                               Dynamic
688    e8:28:c1:f4:d6:88   front-port 0                               Dynamic
1052   94:04:9c:65:1d:8d   front-port 0                               Dynamic
            """
        else:
            self.before = b""

    def expect(self, *args, **kwargs):
        if self.expect_cmd != 0:
            # Если указан другой случай ожидания, то выдаем его и снова ставим по умолчанию `0`
            v = self.expect_cmd
            self.expect_cmd = 0
            return v

        return 0


class EltexLTP8XPexpectFaker:
    """
    ## Это класс создает имитацию сессии pexpect для обработки команд Eltex LTP 8X.
    """

    def __init__(self) -> None:
        self.before: bytes = b""
        self.sent_commands: list[str] = []
        self.expect_cmd = 0

    def send(self, command: str):
        """
        ## Обрабатывает команду

        :param command: Команда для отправки в оболочку
        :type command: str
        """
        self.sent_commands.append(command)

        if command == "show interfaces status 10G-front-port 0 - 1\r":
            self.before = b"""
 show interfaces status 10G-front-port 0 - 1
Interface           Status       Media   Speed        Duplex      Flow control
10G-front-port 0    down         none    1000M        full        no
10G-front-port 1    down         none    10G          full        no
            """
        elif command == "show interfaces status front-port 0 - 7\r":
            self.before = b"""
 show interfaces status front-port 0 - 7
Interface           Status       Media   Speed        Duplex      Flow control
front-port 0        up           copper  1000M        full        no
front-port 1        down         none    auto         auto        no
front-port 2        down         none    auto         auto        no
front-port 3        down         none    auto         auto        no
front-port 4        up           copper  1000M        full        no
front-port 5        down         none    auto         auto        no
front-port 6        down         none    auto         auto        no
front-port 7        down         none    auto         auto        no
            """
        elif command == "show interface gpon-port 0-7 state\r":
            self.before = b"""
    Reading:  ........
    Gpon-ports status information:
        Gpon-port:                               0                1                  2                  3                4                5                  6                  7
        State:                                  OK               OK                 OK                 OK               OK               OK                 OK                 OK
        ONT count:                               7                1                 56                 54                1                0                 38                 47
        ONT autofind:                      enabled          enabled            enabled            enabled          enabled          enabled            enabled            enabled
        SFP vendor:                        Hisense          Hisense              BAZIS              BAZIS          Hisense          Hisense              BAZIS              BAZIS
        SFP product number:          LTE3680P-BC+2    LTE3680P-BC+2    BZ-SFP-GPON-C++    BZ-SFP-GPON-C++    LTE3680P-BC+2    LTE3680P-BC+2    BZ-SFP-GPON-C++    BZ-SFP-GPON-C++
        SFP vendor revision:                    11               11                                                     11               11
        SFP temperature [C]:                    39               39                 43                 43               42               42                 41                 41
        SFP voltage [V]:                      3.25             3.24               3.21               3.18             3.25             3.23               3.22               3.22
        SFP tx bias current [mA]:             8.49             7.87              11.55               8.00             7.08             8.35               7.87              10.82
        SFP tx power [dBm]:                   7.78             7.76               6.06               5.90             7.74             7.68               7.07               7.06
            """
        elif "show mac include interface" in command:
            self.before = b"""
   Mac table
   ~~~~~~~~~
VID    MAC address         Interface                                  Type
----   -----------------   ----------------------------------------   --------
1052   44:8a:5b:70:a7:bf   front-port 0                               Dynamic
688    e8:28:c1:f4:d6:88   front-port 0                               Dynamic
1052   94:04:9c:65:1d:8d   front-port 0                               Dynamic
            """
        else:
            self.before = b""

    def expect(self, *args, **kwargs):
        if self.expect_cmd != 0:
            # Если указан другой случай ожидания, то выдаем его и снова ставим по умолчанию `0`
            v = self.expect_cmd
            self.expect_cmd = 0
            return v

        return 0


class TestEltexLTPInterfaces(SimpleTestCase):
    # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса eltex_esr.
    fake_session_4x = EltexLTP4XPexpectFaker()
    fake_session_8x = EltexLTP8XPexpectFaker()

    @classmethod
    def setUpClass(cls):
        """
        ## Функция `setUpClass` вызывается один раз перед всеми тестами в классе

        :param cls: Настраиваемый объект класса
        """
        # Создание объекта eltex_mes с fake_session, ip-адресом и авторизацией.
        cls.eltex_ltp_4x = EltexLTP(cls.fake_session_4x, "10.10.10.10", auth={}, model="LTP-4X")
        cls.eltex_ltp_8x = EltexLTP(cls.fake_session_8x, "10.10.10.10", auth={}, model="LTP-8X")

    def test_interfaces_ltp_4x(self):
        interfaces = self.eltex_ltp_4x.get_interfaces()
        self.assertEqual(
            interfaces,
            [
                ("10G-front-port 0", "down", ""),
                ("10G-front-port 1", "down", ""),
                ("front-port 0", "up", ""),
                ("front-port 1", "down", ""),
                ("front-port 2", "down", ""),
                ("front-port 3", "down", ""),
                ("pon-port 0", "up", ""),
                ("pon-port 1", "up", ""),
                ("pon-port 2", "up", ""),
                ("pon-port 3", "up", ""),
            ],
        )

    def test_interfaces_ltp_8x(self):
        interfaces = self.eltex_ltp_8x.get_interfaces()
        self.assertEqual(
            interfaces,
            [
                ("10G-front-port 0", "down", ""),
                ("10G-front-port 1", "down", ""),
                ("front-port 0", "up", ""),
                ("front-port 1", "down", ""),
                ("front-port 2", "down", ""),
                ("front-port 3", "down", ""),
                ("front-port 4", "up", ""),
                ("front-port 5", "down", ""),
                ("front-port 6", "down", ""),
                ("front-port 7", "down", ""),
                ("pon-port 0", "up", ""),
                ("pon-port 1", "up", ""),
                ("pon-port 2", "up", ""),
                ("pon-port 3", "up", ""),
                ("pon-port 4", "up", ""),
                ("pon-port 5", "up", ""),
                ("pon-port 6", "up", ""),
                ("pon-port 7", "up", ""),
            ],
        )


class TestEltexLTPMAC(SimpleTestCase):
    # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса eltex_esr.
    fake_session_4x = EltexLTP4XPexpectFaker()
    fake_session_8x = EltexLTP8XPexpectFaker()

    @classmethod
    def setUpClass(cls):
        """
        ## Функция `setUpClass` вызывается один раз перед всеми тестами в классе

        :param cls: Настраиваемый объект класса
        """

        # Создание объекта eltex_mes с fake_session, ip-адресом и авторизацией.
        cls.eltex_ltp_4x = EltexLTP(cls.fake_session_4x, "10.10.10.10", auth={}, model="LTP-4X")
        cls.eltex_ltp_8x = EltexLTP(cls.fake_session_8x, "10.10.10.10", auth={}, model="LTP-8X")

    def test_get_mac_front_port_LTP_4X(self):
        # front-port {n}
        macs = self.eltex_ltp_4x.get_mac("front-port 3")
        self.assertEqual(
            macs,
            [
                (1052, "44:8a:5b:70:a7:bf"),
                (688, "e8:28:c1:f4:d6:88"),
                (1052, "94:04:9c:65:1d:8d"),
            ],
        )
        macs = self.eltex_ltp_4x.get_mac("front-port 4")
        self.assertEqual(
            macs,
            [],
        )

        # front {n}
        macs = self.eltex_ltp_4x.get_mac("front 3")
        self.assertEqual(
            macs,
            [
                (1052, "44:8a:5b:70:a7:bf"),
                (688, "e8:28:c1:f4:d6:88"),
                (1052, "94:04:9c:65:1d:8d"),
            ],
        )
        macs = self.eltex_ltp_4x.get_mac("front 4")
        self.assertEqual(
            macs,
            [],
        )

        # front{n}
        macs = self.eltex_ltp_4x.get_mac("front3")
        self.assertEqual(
            macs,
            [
                (1052, "44:8a:5b:70:a7:bf"),
                (688, "e8:28:c1:f4:d6:88"),
                (1052, "94:04:9c:65:1d:8d"),
            ],
        )
        macs = self.eltex_ltp_4x.get_mac("front4")
        self.assertEqual(
            macs,
            [],
        )

    def test_get_mac_front_port_LTP_8X(self):
        # front-port {n}
        macs = self.eltex_ltp_8x.get_mac("front-port 7")
        self.assertEqual(
            macs,
            [
                (1052, "44:8a:5b:70:a7:bf"),
                (688, "e8:28:c1:f4:d6:88"),
                (1052, "94:04:9c:65:1d:8d"),
            ],
        )
        macs = self.eltex_ltp_8x.get_mac("front-port 8")
        self.assertEqual(
            macs,
            [],
        )

        # front {n}
        macs = self.eltex_ltp_8x.get_mac("front 7")
        self.assertEqual(
            macs,
            [
                (1052, "44:8a:5b:70:a7:bf"),
                (688, "e8:28:c1:f4:d6:88"),
                (1052, "94:04:9c:65:1d:8d"),
            ],
        )
        macs = self.eltex_ltp_8x.get_mac("front 8")
        self.assertEqual(
            macs,
            [],
        )

        # front{n}
        macs = self.eltex_ltp_8x.get_mac("front7")
        self.assertEqual(
            macs,
            [
                (1052, "44:8a:5b:70:a7:bf"),
                (688, "e8:28:c1:f4:d6:88"),
                (1052, "94:04:9c:65:1d:8d"),
            ],
        )
        macs = self.eltex_ltp_8x.get_mac("front8")
        self.assertEqual(
            macs,
            [],
        )

    def test_get_mac_10G_front_port_LTP_4X(self):
        # front-port {n}
        macs = self.eltex_ltp_4x.get_mac("10g-front-port 1")
        self.assertEqual(
            macs,
            [
                (1052, "44:8a:5b:70:a7:bf"),
                (688, "e8:28:c1:f4:d6:88"),
                (1052, "94:04:9c:65:1d:8d"),
            ],
        )
        macs = self.eltex_ltp_4x.get_mac("10G-front-port 2")
        self.assertEqual(
            macs,
            [],
        )

        # front {n}
        macs = self.eltex_ltp_4x.get_mac("10G-front 1")
        self.assertEqual(
            macs,
            [
                (1052, "44:8a:5b:70:a7:bf"),
                (688, "e8:28:c1:f4:d6:88"),
                (1052, "94:04:9c:65:1d:8d"),
            ],
        )
        macs = self.eltex_ltp_4x.get_mac("10G-front 2")
        self.assertEqual(
            macs,
            [],
        )

        # front{n}
        macs = self.eltex_ltp_4x.get_mac("10G-front0")
        self.assertEqual(
            macs,
            [
                (1052, "44:8a:5b:70:a7:bf"),
                (688, "e8:28:c1:f4:d6:88"),
                (1052, "94:04:9c:65:1d:8d"),
            ],
        )
        macs = self.eltex_ltp_4x.get_mac("10g-front3")
        self.assertEqual(
            macs,
            [],
        )

    def test_get_mac_10G_front_port_LTP_8X(self):
        # front-port {n}
        macs = self.eltex_ltp_8x.get_mac("10g-front-port 1")
        self.assertEqual(
            macs,
            [
                (1052, "44:8a:5b:70:a7:bf"),
                (688, "e8:28:c1:f4:d6:88"),
                (1052, "94:04:9c:65:1d:8d"),
            ],
        )
        macs = self.eltex_ltp_8x.get_mac("10G-front-port 2")
        self.assertEqual(
            macs,
            [],
        )

        # front {n}
        macs = self.eltex_ltp_8x.get_mac("10G-front 1")
        self.assertEqual(
            macs,
            [
                (1052, "44:8a:5b:70:a7:bf"),
                (688, "e8:28:c1:f4:d6:88"),
                (1052, "94:04:9c:65:1d:8d"),
            ],
        )
        macs = self.eltex_ltp_8x.get_mac("10G-front 2")
        self.assertEqual(
            macs,
            [],
        )

        # front{n}
        macs = self.eltex_ltp_8x.get_mac("10G-front0")
        self.assertEqual(
            macs,
            [
                (1052, "44:8a:5b:70:a7:bf"),
                (688, "e8:28:c1:f4:d6:88"),
                (1052, "94:04:9c:65:1d:8d"),
            ],
        )
        macs = self.eltex_ltp_8x.get_mac("10g-front3")
        self.assertEqual(
            macs,
            [],
        )

    def test_get_mac_pon_port_LTP_8X(self):
        # front-port {n}
        macs = self.eltex_ltp_8x.get_mac("pon-port 3")
        self.assertEqual(
            macs,
            [
                (1052, "44:8a:5b:70:a7:bf"),
                (688, "e8:28:c1:f4:d6:88"),
                (1052, "94:04:9c:65:1d:8d"),
            ],
        )
        macs = self.eltex_ltp_8x.get_mac("pon-port 8")
        self.assertEqual(
            macs,
            [],
        )

        # front {n}
        macs = self.eltex_ltp_8x.get_mac("pon 3")
        self.assertEqual(
            macs,
            [
                (1052, "44:8a:5b:70:a7:bf"),
                (688, "e8:28:c1:f4:d6:88"),
                (1052, "94:04:9c:65:1d:8d"),
            ],
        )
        macs = self.eltex_ltp_8x.get_mac("pon 8")
        self.assertEqual(
            macs,
            [],
        )

        # front{n}
        macs = self.eltex_ltp_8x.get_mac("pon0")
        self.assertEqual(
            macs,
            [
                (1052, "44:8a:5b:70:a7:bf"),
                (688, "e8:28:c1:f4:d6:88"),
                (1052, "94:04:9c:65:1d:8d"),
            ],
        )
        macs = self.eltex_ltp_8x.get_mac("pon8")
        self.assertEqual(
            macs,
            [],
        )
