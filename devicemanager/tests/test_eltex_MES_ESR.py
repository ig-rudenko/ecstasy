from unittest.mock import patch, Mock

from django.test import SimpleTestCase

from devicemanager.vendors.eltex import EltexMES, EltexESR
from .base_factory_test import AbstractTestFactory


class TestEltexMESFactory(AbstractTestFactory):
    def setUp(self) -> None:
        super().setUp()
        self.show_system_output = """
System Description:                       MES3324F 28-port 1G/10G Managed Switch
System Up Time (days,hour:min:sec):       431,14:32:21
System Contact:
System Name:                              DeviceName
System Location:                          DeviceLocation
System MAC Address:                       e8:28:c1:11:22:33
System Object ID:                         1.3.6.1.4.1.35265.1.81
Reset-Button:                             enable"""

    @staticmethod
    def get_device_class():
        return EltexMES

    @staticmethod
    def get_output_from_show_version_command() -> str:
        return """
Active-image: flash://system/images/mes3300-4016-5R1.ros
  Version: 4.0.16.5
  Commit: 4213e309
  Build: 1 (master)
  MD5 Digest: 272412312325ee77350902e4f0371b8a
  Date: 12-Oct-2021
  Time: 14:03:17
Inactive-image: flash://system/images/mes3300-4014-R5.ros
  Version: 4.0.14
  Commit: ae3f55b3
  Build: 5 (master)
  MD5 Digest: 712c912374012374129f81212528a51908
  Date: 08-Jul-2020
  Time: 15:20:28"""

    @patch("devicemanager.vendors.eltex.base.EltexBase.send_command")
    def test_factory_return_class(self, show_system_command: Mock):
        # Eltex Factory определяет тип Eltex по выводу команды `show system`
        show_system_command.return_value = self.show_system_output
        super().test_factory_return_class()

    @patch("devicemanager.vendors.eltex.base.EltexBase.send_command")
    def test_factory_device_attributes(self, show_system_command: Mock):
        # Eltex Factory определяет тип Eltex по выводу команды `show system`
        show_system_command.return_value = self.show_system_output
        super().test_factory_device_attributes()


class TestEltexESRFactory(TestEltexMESFactory):
    def setUp(self) -> None:
        super().setUp()
        self.show_system_output = """
System type:           Eltex ESR-12VF Service Router
System name:           DeviceName
Software version:      1.13.0 build 41[a6eb430ee2] (date 02/06/2021 time 13:25:01)
Hardware version:      3v2
System uptime:         346 days, 9 hours, 32 minutes and 45 seconds
System MAC address:    A8:F9:4B:11:22:33
System serial number:  NP0A341239"""

    @staticmethod
    def get_device_class():
        return EltexESR

    @staticmethod
    def get_output_from_show_version_command() -> str:
        return """
Boot version:
  1.8.1.4 (date 11/09/2019 time 09:39:34)
SW version:
  1.13.0 build 41[a6eb430ee2] (date 02/06/2021 time 13:25:01)
HW version:
  3v2
VoIP version:
  1.8.0.1"""


class EltexMESPexpectFaker:
    """
    ## Это класс создает имитацию сессии pexpect для обработки команд Eltex MES.
    """

    def __init__(self):
        self.before = b""
        self.sent_commands = []
        self.expect_cmd = 0

    def send(self, command: str):
        return self.sendline(command.strip())

    def sendline(self, command: str):
        """
        ## Обрабатывает команду

        :param command: Команда для отправки в оболочку
        :type command: str
        """
        self.sent_commands.append(command)

        if command == "show interfaces description":
            self.before = b"""
                                  Admin Link
Port     Port Mode (VLAN)         State State       Description
-------- ------------------------ ----- ----------- -----------
gi1/0/1  Trunk                    Up    Up          Description1
gi1/0/2  Trunk                    Up    Up          Description2
gi1/0/3  General                  Up    Up          Description3
gi1/0/4  General                  Up    Up          Description4
gi1/0/5  Trunk                    Up    Up          Description5
gi1/0/6  Access (1944)            Up    Up          Description6
gi1/0/7  Trunk                    Up    Up          Description7
gi1/0/8  Access (711)             Up    Up          Description8
gi1/0/9  Trunk                    Down  Down        Description9
gi1/0/10 Trunk                    Down  Down
gi1/0/11 Trunk                    Up    Up          Description11
gi1/0/12 General                  Up    Up          Description12 
gi1/0/13 General                  Up    Up          Description13 
gi1/0/14 Trunk                    Up    Up          Description14 
gi1/0/15 Trunk                    Up    Up          Description15 
gi1/0/16 General                  Down  Down        Description16 
gi1/0/17 General                  Up    Up          Description17
gi1/0/18 Trunk                    Up    Up          Description18
gi1/0/19 General                  Up    Up          
gi1/0/20 Trunk                    Up    Up          
gi1/0/21 Trunk                    Up    Up          
gi1/0/22 Trunk                    Up    Up          
gi1/0/23 Trunk                    Up    Up          
gi1/0/24 Trunk                    Up    Up          
te1/0/1  Trunk                    Up    Up          
te1/0/2  Trunk                    Up    Up          
te1/0/3  Trunk                    Up    Down        
te1/0/4  Trunk                    Up    Down        

            """

        elif "show running-config interface" in command:
            self.before = b"""
interface gigabitethernet1/0/3
 loopback-detection enable
 description Description3
 mtu 9000
 storm-control broadcast kbps 1024 trap
 storm-control unicast kbps 1024 trap
 storm-control multicast level 10 trap
 spanning-tree disable
 spanning-tree guard root
 switchport general ingress-filtering disable
 switchport mode general
 switchport general allowed vlan add 700,711,800-802,811 tagged
 switchport general allowed vlan add 4021 untagged
 switchport forbidden default-vlan
 selective-qinq list ingress permit ingress_vlan 700,711,800-801,811
 selective-qinq list ingress add_vlan 4021
!
            """

        elif command == "show mac address-table interface GigabitEthernet 0/1":
            self.before = b"""
    Vlan          Mac Address         Port       Type
------------ --------------------- ---------- ----------
    711        1c:af:f7:41:bd:3f    gi1/0/1    dynamic
    711        4c:5e:0c:d5:da:c8    gi1/0/1    dynamic
    711        70:62:b8:72:62:ee    gi1/0/1    dynamic

            """

        elif command == "Y":
            self.before = b"succeed"

        else:
            self.before = b""

        return len(command)

    def expect(self, *args, **kwargs):
        if self.expect_cmd != 0:
            # Если указан другой случай ожидания, то выдаем его и снова ставим по умолчанию `0`
            v = self.expect_cmd
            self.expect_cmd = 0
            return v

        return 0


class EltexESRPexpectFaker:
    """
    ## Это класс создает имитацию сессии pexpect для обработки команд Eltex ESR.
    """

    def __init__(self):
        self.before = b""
        self.sent_commands = []
        self.expect_cmd = 0

    def send(self, command: str):
        return self.sendline(command.strip())

    def sendline(self, command: str):
        """
        ## Обрабатывает команду

        :param command: Команда для отправки в оболочку
        :type command: str
        """
        self.sent_commands.append(command)

        if command == "show interfaces description":
            self.before = b"""
Interface            Admin   Link    Description
                     State   State
------------------   -----   -----   ----------------------------------------------------
gi1/0/1              Up      Up      --
gi1/0/2              Up      Down    --
gi1/0/3              Up      Down    --
gi1/0/4              Up      Down    --
gi1/0/5              Down    Down    --
gi1/0/6              Down    Down    --
gi1/0/7              Up      Down    --
gi1/0/8              Up      Down    --
gi1/0/9              Up      Up      Descr
bridge 1             Up      Up      MGMT
bridge 2             Up      Up      INET_DHCP
            """

        elif command == "show running-config interface GigabitEthernet 1/0/9":
            self.before = b"""
interface gigabitethernet 1/0/9
  description "Description"
  mode switchport
  security-zone trusted
  switchport forbidden default-vlan
  switchport mode trunk
  switchport trunk allowed vlan auto-all
exit
            """

        elif "show running-config interface" in command:
            self.before = b"""
interface gigabitethernet 1/0/1
  mode switchport
  security-zone untrusted
  switchport forbidden default-vlan
  switchport access vlan 604
exit
            """

        elif command == "show mac address-table interface GigabitEthernet 1/0/1":
            self.before = b"""
VID     MAC Address          Interface                        Type
-----   ------------------   ------------------------------   -------
1959    bc:16:65:4f:a3:a2    gigabitethernet 1/0/1            Dynamic
1959    00:0f:e2:b6:eb:78    gigabitethernet 1/0/1            Dynamic
1959    00:0f:e2:07:f2:e0    gigabitethernet 1/0/1            Dynamic
            """

        elif command == "show interfaces status GigabitEthernet 1/0/1":
            self.before = b"""
Interface 'gi1/0/9' status information:
 Description:          Descr
 Operational state:    Up
 Administrative state: Up
 Supports broadcast:   Yes
 Supports multicast:   Yes
 MTU:                  1500
 MAC address:          a8:f9:4b:ad:12:8d
 Last change:          22 days, 20 hours, 49 minutes and 49 seconds
 Mode:                 switchport
            """

        else:
            self.before = b""

        return len(command)

    def expect(self, *args, **kwargs):
        if self.expect_cmd != 0:
            # Если указан другой случай ожидания, то выдаем его и снова ставим по умолчанию `0`
            v = self.expect_cmd
            self.expect_cmd = 0
            return v

        return 0


class TestEltexMESInterfaces(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        """
        ## Функция `setUpClass` вызывается один раз перед всеми тестами в классе

        :param cls: Настраиваемый объект класса
        """
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса eltex_mes.
        fake_session = EltexMESPexpectFaker()
        auth = {"privilege_mode_password": ""}
        # Создание объекта eltex_mes с fake_session, ip-адресом и авторизацией.
        cls.eltex_mes = EltexMES(fake_session, "10.10.10.10", auth=auth)

    def test_interfaces(self):
        """
        Он проверяет, что
        интерфейсы класса правильные
        """
        interfaces = self.eltex_mes.get_interfaces()

        self.assertEqual(
            interfaces,
            [
                ("gi1/0/1", "up", "Description1"),
                ("gi1/0/2", "up", "Description2"),
                ("gi1/0/3", "up", "Description3"),
                ("gi1/0/4", "up", "Description4"),
                ("gi1/0/5", "up", "Description5"),
                ("gi1/0/6", "up", "Description6"),
                ("gi1/0/7", "up", "Description7"),
                ("gi1/0/8", "up", "Description8"),
                ("gi1/0/9", "admin down", "Description9"),
                ("gi1/0/10", "admin down", ""),
                ("gi1/0/11", "up", "Description11"),
                ("gi1/0/12", "up", "Description12"),
                ("gi1/0/13", "up", "Description13"),
                ("gi1/0/14", "up", "Description14"),
                ("gi1/0/15", "up", "Description15"),
                ("gi1/0/16", "admin down", "Description16"),
                ("gi1/0/17", "up", "Description17"),
                ("gi1/0/18", "up", "Description18"),
                ("gi1/0/19", "up", ""),
                ("gi1/0/20", "up", ""),
                ("gi1/0/21", "up", ""),
                ("gi1/0/22", "up", ""),
                ("gi1/0/23", "up", ""),
                ("gi1/0/24", "up", ""),
                ("te1/0/1", "up", ""),
                ("te1/0/2", "up", ""),
                ("te1/0/3", "down", ""),
                ("te1/0/4", "down", ""),
            ],
        )

    def test_interfaces_vlans(self):
        valid_interfaces_vlans = [
            ("gi1/0/1", "up", "Description1", ["700,711,800-802,811", "4021"]),
            ("gi1/0/2", "up", "Description2", ["700,711,800-802,811", "4021"]),
            ("gi1/0/3", "up", "Description3", ["700,711,800-802,811", "4021"]),
            ("gi1/0/4", "up", "Description4", ["700,711,800-802,811", "4021"]),
            ("gi1/0/5", "up", "Description5", ["700,711,800-802,811", "4021"]),
            ("gi1/0/6", "up", "Description6", ["700,711,800-802,811", "4021"]),
            ("gi1/0/7", "up", "Description7", ["700,711,800-802,811", "4021"]),
            ("gi1/0/8", "up", "Description8", ["700,711,800-802,811", "4021"]),
            (
                "gi1/0/9",
                "admin down",
                "Description9",
                ["700,711,800-802,811", "4021"],
            ),
            ("gi1/0/10", "admin down", "", ["700,711,800-802,811", "4021"]),
            ("gi1/0/11", "up", "Description11", ["700,711,800-802,811", "4021"]),
            ("gi1/0/12", "up", "Description12", ["700,711,800-802,811", "4021"]),
            ("gi1/0/13", "up", "Description13", ["700,711,800-802,811", "4021"]),
            ("gi1/0/14", "up", "Description14", ["700,711,800-802,811", "4021"]),
            ("gi1/0/15", "up", "Description15", ["700,711,800-802,811", "4021"]),
            (
                "gi1/0/16",
                "admin down",
                "Description16",
                ["700,711,800-802,811", "4021"],
            ),
            ("gi1/0/17", "up", "Description17", ["700,711,800-802,811", "4021"]),
            ("gi1/0/18", "up", "Description18", ["700,711,800-802,811", "4021"]),
            ("gi1/0/19", "up", "", ["700,711,800-802,811", "4021"]),
            ("gi1/0/20", "up", "", ["700,711,800-802,811", "4021"]),
            ("gi1/0/21", "up", "", ["700,711,800-802,811", "4021"]),
            ("gi1/0/22", "up", "", ["700,711,800-802,811", "4021"]),
            ("gi1/0/23", "up", "", ["700,711,800-802,811", "4021"]),
            ("gi1/0/24", "up", "", ["700,711,800-802,811", "4021"]),
            ("te1/0/1", "up", "", ["700,711,800-802,811", "4021"]),
            ("te1/0/2", "up", "", ["700,711,800-802,811", "4021"]),
            ("te1/0/3", "down", "", ["700,711,800-802,811", "4021"]),
            ("te1/0/4", "down", "", ["700,711,800-802,811", "4021"]),
        ]

        interfaces_vlans = self.eltex_mes.get_vlans()

        self.assertEqual(
            interfaces_vlans,
            valid_interfaces_vlans,
        )


class TestEltexMESMacAddress(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        """
        ## Функция `setUpClass` вызывается один раз перед всеми тестами в классе

        :param cls: Настраиваемый объект класса
        """
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса eltex_mes.
        fake_session = EltexMESPexpectFaker()
        auth = {"privilege_mode_password": ""}
        # Создание объекта eltex_mes с fake_session, ip-адресом и авторизацией.
        cls.eltex_mes = EltexMES(fake_session, "10.10.10.10", auth=auth)

    def test_get_mac(self):
        """
        ## Проверяет функцию get_mac, чтобы убедиться, что она возвращает правильный ответ
        """
        macs = self.eltex_mes.get_mac("Gi0/1")
        self.assertEqual(
            macs,
            [
                (711, "1c:af:f7:41:bd:3f"),
                (711, "4c:5e:0c:d5:da:c8"),
                (711, "70:62:b8:72:62:ee"),
            ],
        )

    def test_get_mac_invalid_port(self):
        """
        ## Проверяет функцию get_mac, чтобы убедиться, что она возвращает правильный ответ
        """
        macs = self.eltex_mes.get_mac("Ri0 /1")
        self.assertEqual(
            macs,
            [],
        )


class TestEltexMESPortControl(SimpleTestCase):
    # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса eltex_mes.
    fake_session = EltexMESPexpectFaker()

    @classmethod
    def setUpClass(cls):
        """
        ## Функция `setUpClass` вызывается один раз перед всеми тестами в классе

        :param cls: Настраиваемый объект класса
        """
        auth = {"privilege_mode_password": ""}
        # Создание объекта eltex_mes с fake_session, ip-адресом и авторизацией.
        cls.eltex_mes = EltexMES(cls.fake_session, "10.10.10.10", auth=auth)

    def setUp(self) -> None:
        self.fake_session.sent_commands = []

    def test_reload_port(self):
        self.eltex_mes.reload_port("Gi0/1")

        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "configure terminal",
                "interface GigabitEthernet 0/1",
                "shutdown",
                "no shutdown",
                "end",
                "write",
                "Y",
            ],
        )

    def test_reload_port_no_save(self):
        self.eltex_mes.reload_port("Gi0/1", save_config=False)

        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "configure terminal",
                "interface GigabitEthernet 0/1",
                "shutdown",
                "no shutdown",
                "end",
            ],
        )

    def test_reload_invalid_port(self):
        status = self.eltex_mes.reload_port("Re0/1")

        self.assertEqual(status, "Неверный порт")

        self.assertEqual(
            self.fake_session.sent_commands,
            [],
        )

    def test_set_up_port(self):
        # Установка порта Te 0/1/2 на up.
        self.eltex_mes.set_port("Te 0/1/2", "up")

        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "configure terminal",
                "interface TenGigabitEthernet 0/1/2",
                "no shutdown",
                "end",
                "write",
                "Y",
            ],
        )

    def test_set_up_port_no_save(self):
        # Установка порта Te 0/1/2 на up.
        self.eltex_mes.set_port("Te 0/1/2", "up", save_config=False)

        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "configure terminal",
                "interface TenGigabitEthernet 0/1/2",
                "no shutdown",
                "end",
            ],
        )

    def test_set_up_invalid_port(self):
        status = self.eltex_mes.set_port("Re 0/1/2", "up")

        self.assertEqual(status, "Неверный порт")

        self.assertEqual(
            self.fake_session.sent_commands,
            [],
        )

    def test_set_down_port(self):
        self.eltex_mes.set_port("Fa 0/2", "down")

        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "configure terminal",
                "interface FastEthernet 0/2",
                "shutdown",
                "end",
                "write",
                "Y",
            ],
        )

    def test_set_down_invalid_port(self):
        status = self.eltex_mes.set_port("Ra 0/2", "down")

        self.assertEqual(status, "Неверный порт")

        self.assertEqual(
            self.fake_session.sent_commands,
            [],
        )


class TestEltexMESPortInfo(SimpleTestCase):
    # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса eltex_mes.
    fake_session = EltexMESPexpectFaker()

    @classmethod
    def setUpClass(cls):
        """
        ## Функция `setUpClass` вызывается один раз перед всеми тестами в классе

        :param cls: Настраиваемый объект класса
        """
        auth = {"privilege_mode_password": ""}
        # Создание объекта eltex_mes с fake_session, ip-адресом и авторизацией.
        cls.eltex_mes = EltexMES(cls.fake_session, "10.10.10.10", auth=auth)

    def setUp(self) -> None:
        self.fake_session.sent_commands = []

    def test_port_config(self):
        self.eltex_mes.get_port_config("Gi 0/1")
        self.assertEqual(
            self.fake_session.sent_commands,
            ["show running-config interface GigabitEthernet 0/1"],
        )


class TestEltexMESPortDescription(SimpleTestCase):
    # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса eltex_mes.
    fake_session = EltexMESPexpectFaker()

    @classmethod
    def setUpClass(cls):
        # Создание объекта eltex_mes с fake_session, ip-адресом и авторизацией.
        cls.eltex_mes = EltexMES(cls.fake_session, "10.10.10.10", auth={})

    def setUp(self) -> None:
        self.fake_session.sent_commands = []

    def test_change_description(self):
        self.eltex_mes.set_description("Gi0/1", "New [desc] \nновое описание")
        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "configure terminal",
                "interface GigabitEthernet 0/1",
                "description New_(desc)_novoe_opisanie",
                "end",
                "write",
                "Y",
            ],
        )

    def test_clear_description(self):
        self.eltex_mes.set_description("Gi0/1", "")
        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "configure terminal",
                "interface GigabitEthernet 0/1",
                "no description",
                "end",
                "write",
                "Y",
            ],
        )


class TestEltexESRInterfaces(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        """
        ## Функция `setUpClass` вызывается один раз перед всеми тестами в классе

        :param cls: Настраиваемый объект класса
        """
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса eltex_esr.
        fake_session = EltexESRPexpectFaker()
        auth = {"privilege_mode_password": ""}
        # Создание объекта eltex_mes с fake_session, ip-адресом и авторизацией.
        cls.eltex_esr = EltexESR(fake_session, "10.10.10.10", auth=auth)

    def test_interfaces(self):
        """
        Он проверяет, что
        интерфейсы класса правильные
        """
        interfaces = self.eltex_esr.get_interfaces()
        self.assertEqual(
            interfaces,
            [
                ("gi1/0/1", "up", "--"),
                ("gi1/0/2", "down", "--"),
                ("gi1/0/3", "down", "--"),
                ("gi1/0/4", "down", "--"),
                ("gi1/0/5", "admin down", "--"),
                ("gi1/0/6", "admin down", "--"),
                ("gi1/0/7", "down", "--"),
                ("gi1/0/8", "down", "--"),
                ("gi1/0/9", "up", "Descr"),
            ],
        )

    def test_interfaces_vlans(self):
        valid_interfaces_vlans = [
            ("gi1/0/1", "up", "--", ["604"]),
            ("gi1/0/2", "down", "--", ["604"]),
            ("gi1/0/3", "down", "--", ["604"]),
            ("gi1/0/4", "down", "--", ["604"]),
            ("gi1/0/5", "admin down", "--", ["604"]),
            ("gi1/0/6", "admin down", "--", ["604"]),
            ("gi1/0/7", "down", "--", ["604"]),
            ("gi1/0/8", "down", "--", ["604"]),
            ("gi1/0/9", "up", "Descr", ["1 to 4096"]),
        ]

        interfaces_vlans = self.eltex_esr.get_vlans()

        self.assertEqual(
            interfaces_vlans,
            valid_interfaces_vlans,
        )


class TestEltexESRMacAddress(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        """
        ## Функция `setUpClass` вызывается один раз перед всеми тестами в классе

        :param cls: Настраиваемый объект класса
        """
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса eltex_esr.
        fake_session = EltexESRPexpectFaker()
        # Создание объекта eltex_mes с fake_session, ip-адресом и авторизацией.
        cls.eltex_esr = EltexESR(fake_session, "10.10.10.10", auth={})

    def test_get_mac(self):
        """
        ## Проверяет функцию get_mac, чтобы убедиться, что она возвращает правильный ответ
        """
        macs = self.eltex_esr.get_mac("Gi1/0/1")
        self.assertEqual(
            macs,
            [
                (1959, "bc:16:65:4f:a3:a2"),
                (1959, "00:0f:e2:b6:eb:78"),
                (1959, "00:0f:e2:07:f2:e0"),
            ],
        )

    def test_get_mac_invalid_port(self):
        """
        ## Проверяет функцию get_mac, чтобы убедиться, что она возвращает правильный ответ
        """
        macs = self.eltex_esr.get_mac("Ri0 /1")
        self.assertEqual(
            macs,
            [],
        )
