import pathlib

import textfsm
from django.test import SimpleTestCase

from devicemanager.vendors.cisco import Cisco

from ..multifactory import DeviceMultiFactory
from ..vendors.base.types import ArpInfoResult
from .base_factory_test import AbstractTestFactory

fake_auth = {"login": "test", "password": "password", "privilege_mode_password": ""}


class TestCiscoFactory(AbstractTestFactory):
    @staticmethod
    def get_device_class():
        return Cisco

    @staticmethod
    def get_output_from_show_version_command() -> str:
        return """
Cisco IOS Software, C3560 Software (C3560-IPBASE-M), Version 12.2(25)SEB2, RELEASE SOFTWARE (fc1)
Copyright (c) 1986-2005 by Cisco Systems, Inc.
        """


class CiscoPexpectFaker:
    """
    ## Это класс создает имитацию сессии pexpect для обработки команд Cisco.
    """

    def __init__(self):
        self.before = b""
        self.sent_commands = []
        self.expect_cmd = 0

    def send(self, command: str):
        return self.sendline(command.strip())

    def sendline(self, command: str):
        self.sent_commands.append(command)

        if command == "write":
            # Для случая 'OK'
            self.expect_cmd = 1

        if command == "show interface description":
            self.before = b"""
Interface                      Status         Protocol Description
Fa1                            down           down
Te1/1                          admin down     down     Desc1
Te1/2                          admin down     down
Te1/3                          up             up       Desc3
Te1/4                          up             up       Desc4
Te1/5                          admin down     down
Te1/6                          admin down     down     Desc6
Te1/7                          admin down     down
Te1/8                          admin down     down
Te1/9                          admin down     down
Te1/10                         admin down     down
Te1/11                         admin down     down
Te1/12                         up             up       
Te1/13                         admin down     down
Te1/14                         admin down     down     Desc14
Te1/15                         up             up       Some description
Te1/16                         admin down     down
Vl1                            admin down     down
Vl101                          up             up
Vl106                          up             up
"""
        elif command == "show vlan brief":
            self.before = b"""VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Gi1/0/1,   Gi1/0/4  Gi1/0/8
                                                Gi1/0/9
                                                Gi1/0/10
                                                Gi1/0/25
                                                Gi1/0/26
3    Proxy_kspi                       active    
4    VLAN0004                         active    
5    VLAN0005                         active    
6    VLAN0006                         active    Gi1/0/13
7    VLAN0007                         active    
8    VLAN0008                         active    
9    VLAN0009                         active    
"""

        elif command == "show arp | include 0000.aaaa.0000" or command == "show arp | include 10.100.10.100":
            self.before = b"""
Internet  10.100.10.100             27   0000.aaaa.0000  ARPA   Vlan25
            """

        elif "show interface GigabitEthernet " in command:
            if command.endswith("/1"):
                self.before = b"""
  Keepalive set (10 sec)
  Full-duplex, 1000Mb/s, media type is 10/100/1000BaseTX
  input flow-control is off, output flow-control is unsupported
                """
            elif command.endswith("/2"):
                self.before = b"""
  Keepalive not set
  Full-duplex, 1000Mb/s, link type is auto, media type is 1000BaseLX SFP
  input flow-control is off, output flow-control is unsupported
                """
            elif command.endswith("/3"):
                self.before = b"""
  Keepalive not set
  Full-duplex, 1000Mb/s, link type is auto, media type is 1000BaseBX10-U SFP
  input flow-control is off, output flow-control is unsupported
                """
            elif command.endswith("/4"):
                self.before = b"""
  Keepalive not set
  Full-duplex, 1000Mb/s, link type is auto, media type is No XCVR
  input flow-control is off, output flow-control is unsupported
                """
            elif command.endswith("/5"):
                self.before = b"""
  Transport mode LAN (10GBASE-R, 10.3125Gb/s), media type is SFP-LR
  input flow-control is off, output flow-control is unsupported
  ARP type: ARPA, ARP Timeout 04:00:00
                """
            elif command.endswith("/6"):
                self.before = b"""
  Transport mode LAN (10GBASE-R, 10.3125Gb/s), media type is unknown media type
  input flow-control is off, output flow-control is unsupported
  ARP type: ARPA, ARP Timeout 04:00:00
                """
            elif command.endswith("/7"):
                self.before = b"""
  Full-duplex, Auto-speed, link type is auto, media type is No Gbic
  input flow-control is off, output flow-control is off
  ARP type: ARPA, ARP Timeout 04:00:00
                """
            elif command.endswith("/8"):
                self.before = b"""
  Full-duplex, Auto-speed, link type is auto, media type is 1000BaseLH
  input flow-control is off, output flow-control is off
  ARP type: ARPA, ARP Timeout 04:00:00
                """
            elif command.endswith("/9"):
                self.before = b"""
  Full-duplex, 1000Mb/s, link type is auto, media type is unsupported
  input flow-control is off, output flow-control is unsupported
  ARP type: ARPA, ARP Timeout 04:00:00
                """
            elif command.endswith("/10"):
                self.before = b"""
  Auto-duplex, Auto-speed, link type is auto, media type is Not Present
  input flow-control is off, output flow-control is unsupported
  ARP type: ARPA, ARP Timeout 04:00:00
                """
            elif command.endswith("/11"):
                self.before = b"""
  Full-duplex, 100Mb/s, media type is RJ45
  input flow-control is off, output flow-control is off
  ARP type: ARPA, ARP Timeout 04:00:00
                """
            elif command.endswith("/12"):
                self.before = b"""
  Keepalive set (10 sec)
  Auto-duplex, Auto-speed, media type is LX
  input flow-control is off, output flow-control is off
                """

        elif "show running-config" in command:
            self.before = b"""
Current configuration : 837 bytes
!
interface TenGigabitEthernet1/1
 switchport trunk allowed vlan 101,103-105
 switchport mode trunk
 load-interval 30
 shutdown
!
interface TenGigabitEthernet1/2
 switchport trunk allowed vlan 101,103-105
 switchport trunk allowed vlan add 213,214
 switchport mode trunk
 load-interval 30
!
interface TenGigabitEthernet1/3
 switchport trunk allowed vlan 101,103-105
 switchport trunk allowed vlan add 213,214
 switchport mode trunk
 load-interval 30
!
interface TenGigabitEthernet1/4
 switchport trunk allowed vlan 101,103-105
 switchport trunk allowed vlan add 213,214
 switchport mode trunk
 load-interval 30
!
interface TenGigabitEthernet1/5
 switchport trunk allowed vlan 101,103-105
 switchport trunk allowed vlan add 213,214
 switchport mode trunk
 load-interval 30
!
interface TenGigabitEthernet1/6
 switchport trunk allowed vlan 101,103-105
 switchport trunk allowed vlan add 213,214
 switchport mode trunk
 load-interval 30
!
interface TenGigabitEthernet1/7
 switchport trunk allowed vlan 101,103-105
 switchport trunk allowed vlan add 213,214
 switchport mode trunk
 load-interval 30
!
interface TenGigabitEthernet1/8
 switchport trunk allowed vlan 101,103-105
 switchport trunk allowed vlan add 213,214
 switchport mode trunk
 load-interval 30
!
interface TenGigabitEthernet1/9
 switchport trunk allowed vlan 101,103-105
 switchport trunk allowed vlan add 213,214
 switchport mode trunk
 load-interval 30
!
interface TenGigabitEthernet1/10
 switchport trunk allowed vlan 101,103-105
 switchport trunk allowed vlan add 213,214
 switchport mode trunk
 load-interval 30
!
interface TenGigabitEthernet1/11
 switchport trunk allowed vlan 101,103-105
 switchport trunk allowed vlan add 213,214
 switchport mode trunk
 load-interval 30
!
interface TenGigabitEthernet1/12
 switchport trunk allowed vlan 101,103-105
 switchport trunk allowed vlan add 213,214
 switchport mode trunk
 load-interval 30
!
interface TenGigabitEthernet1/13
 switchport trunk allowed vlan 101,103-105
 switchport trunk allowed vlan add 213,214
 switchport mode trunk
 load-interval 30
!
interface TenGigabitEthernet1/14
 switchport trunk allowed vlan 101,103-105
 switchport trunk allowed vlan add 213,214
 switchport mode trunk
 load-interval 30
!
interface TenGigabitEthernet1/15
 switchport trunk allowed vlan 101,103-105
 switchport trunk allowed vlan add 213,214
 switchport mode trunk
 load-interval 30
!
interface TenGigabitEthernet1/16
 switchport trunk allowed vlan 101,103-105
 switchport trunk allowed vlan add 213,214
 switchport mode trunk
 load-interval 30
!
            """

        elif command == "show version":
            self.before = b"""
Cisco IOS Software, C3560 Software (C3560-ADVIPSERVICESK9-M), Version 12.2(46)SE, RELEASE SOFTWARE (fc2)
Copyright (c) 1986-2008 by Cisco Systems, Inc.
Compiled Thu 21-Aug-08 15:26 by nachen
Image text-base: 0x00003000, data-base: 0x01A00000

1536K bytes of flash-simulated non-volatile configuration memory.
Base ethernet MAC Address       : F4:1F:C2:71:49:10
Motherboard assembly number     : 21-15693-07
Motherboard serial number       : FOC26367HL7
Model revision number           : B0
Motherboard revision number     : B0
Model number                    : ME-3600X-24FS-M
System serial number            : FOC6734Z6AH
Top Assembly Part Number        : 800-38657-01
Top Assembly Revision Number    : C0
Version ID                      : V01
CLEI Code Number                : IPML500KRA
            """

        elif "show mac address-table interface GigabitEthernet 0/1" in command:
            self.before = b"""
          Mac Address Table
-------------------------------------------

Vlan    Mac Address       Type        Ports
----    -----------       --------    -----
 716    2887.baf2.0f9a    DYNAMIC     Gi0/1
 716    50ff.2028.f55b    DYNAMIC     Gi0/1
 716    b0a7.b9c4.aa41    DYNAMIC     Gi0/1
 800    80fb.06cb.ee68    DYNAMIC     Gi0/1
Total Mac Addresses for this criterion: 4
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


class TestCiscoInit(SimpleTestCase):
    def test_initial_data(self):
        cisco = DeviceMultiFactory.get_device(
            session=CiscoPexpectFaker(),
            ip="10.10.10.10",
            auth=fake_auth,
            version_output="",
            snmp_community="public",
        )

        self.assertEqual(cisco.mac, "F4:1F:C2:71:49:10")
        self.assertEqual(cisco.serialno, "FOC6734Z6AH")


class TestCiscoVlanTable(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса Cisco.
        fake_session = CiscoPexpectFaker()
        # Создание объекта Cisco с fake_session, ip-адресом и авторизацией.
        cls.cisco = Cisco(fake_session, "10.10.10.10", auth=fake_auth)

    def test_get_vlan_table(self):
        vlan_table = self.cisco.get_vlan_table()
        self.assertListEqual(
            vlan_table,
            [
                (
                    1,
                    [
                        "GigabitEthernet 1/0/1",
                        "GigabitEthernet 1/0/4",
                        "GigabitEthernet 1/0/8",
                        "GigabitEthernet 1/0/9",
                        "GigabitEthernet 1/0/10",
                        "GigabitEthernet 1/0/25",
                        "GigabitEthernet 1/0/26",
                    ],
                    "default",
                ),
                (3, [], "Proxy_kspi"),
                (4, [], "VLAN0004"),
                (5, [], "VLAN0005"),
                (6, ["GigabitEthernet 1/0/13"], "VLAN0006"),
                (7, [], "VLAN0007"),
                (8, [], "VLAN0008"),
                (9, [], "VLAN0009"),
            ],
        )


class TestCiscoInterfaces(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TEMPLATE_DIR = pathlib.Path(__file__).parent.parent / "templates"
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса Cisco.
        fake_session = CiscoPexpectFaker()
        # Создание объекта Cisco с fake_session, ip-адресом и авторизацией.
        cls.cisco = Cisco(fake_session, "10.10.10.10", auth=fake_auth)

    def test_interfaces_regexp(self):
        """
        ## Тестируем регулярное выражение для выходных данных команды «show ports description»
        """

        interfaces_output = """
Interface                      Status         Protocol Description
Fa1                            down           down
Te1/1                          admin down     down     Desc1
Te1/2                          admin down     down
Te1/3                          up             up       Desc3
Te1/4                          up             up       Desc4
Te1/5                          admin down     down
Te1/6                          admin down     down     Desc6
Te1/7                          admin down     down
Te1/8                          admin down     down
Te1/9                          admin down     down
Te1/10                         admin down     down
Te1/11                         admin down     down
Te1/12                         up             up       
Te1/13                         admin down     down
Te1/14                         admin down     down     Desc14
Te1/15                         up             up       Some description
Te1/16                         admin down     down
Vl1                            admin down     down
Vl101                          up             up
Vl106                          up             up
        """

        with open(self.TEMPLATE_DIR / "interfaces" / "cisco.template") as template_file:
            int_des_ = textfsm.TextFSM(template_file)
        result = int_des_.ParseText(interfaces_output)

        self.assertEqual(
            result,
            [
                ["Te1/1", "admin down", "down", "Desc1"],
                ["Te1/2", "admin down", "down", ""],
                ["Te1/3", "up", "up", "Desc3"],
                ["Te1/4", "up", "up", "Desc4"],
                ["Te1/5", "admin down", "down", ""],
                ["Te1/6", "admin down", "down", "Desc6"],
                ["Te1/7", "admin down", "down", ""],
                ["Te1/8", "admin down", "down", ""],
                ["Te1/9", "admin down", "down", ""],
                ["Te1/10", "admin down", "down", ""],
                ["Te1/11", "admin down", "down", ""],
                ["Te1/12", "up", "up", ""],
                ["Te1/13", "admin down", "down", ""],
                ["Te1/14", "admin down", "down", "Desc14"],
                ["Te1/15", "up", "up", "Some description"],
                ["Te1/16", "admin down", "down", ""],
            ],
        )

    def test_get_interfaces(self):
        # Получение интерфейсов от объекта cisco.
        interfaces = self.cisco.get_interfaces()
        self.assertEqual(
            interfaces,
            [
                ("Te1/1", "admin down", "Desc1"),
                ("Te1/2", "admin down", ""),
                ("Te1/3", "up", "Desc3"),
                ("Te1/4", "up", "Desc4"),
                ("Te1/5", "admin down", ""),
                ("Te1/6", "admin down", "Desc6"),
                ("Te1/7", "admin down", ""),
                ("Te1/8", "admin down", ""),
                ("Te1/9", "admin down", ""),
                ("Te1/10", "admin down", ""),
                ("Te1/11", "admin down", ""),
                ("Te1/12", "up", ""),
                ("Te1/13", "admin down", ""),
                ("Te1/14", "admin down", "Desc14"),
                ("Te1/15", "up", "Some description"),
                ("Te1/16", "admin down", ""),
            ],
        )

    def test_get_vlans(self):
        # Получение интерфейсов и VLAN от объекта cisco.
        interfaces_vlans = self.cisco.get_vlans()
        self.assertEqual(
            interfaces_vlans,
            [
                ("Te1/1", "admin down", "Desc1", ["101,103-105"]),
                ("Te1/2", "admin down", "", ["101,103-105", "213,214"]),
                ("Te1/3", "up", "Desc3", ["101,103-105", "213,214"]),
                ("Te1/4", "up", "Desc4", ["101,103-105", "213,214"]),
                ("Te1/5", "admin down", "", ["101,103-105", "213,214"]),
                ("Te1/6", "admin down", "Desc6", ["101,103-105", "213,214"]),
                ("Te1/7", "admin down", "", ["101,103-105", "213,214"]),
                ("Te1/8", "admin down", "", ["101,103-105", "213,214"]),
                ("Te1/9", "admin down", "", ["101,103-105", "213,214"]),
                ("Te1/10", "admin down", "", ["101,103-105", "213,214"]),
                ("Te1/11", "admin down", "", ["101,103-105", "213,214"]),
                ("Te1/12", "up", "", ["101,103-105", "213,214"]),
                ("Te1/13", "admin down", "", ["101,103-105", "213,214"]),
                ("Te1/14", "admin down", "Desc14", ["101,103-105", "213,214"]),
                (
                    "Te1/15",
                    "up",
                    "Some description",
                    ["101,103-105", "213,214"],
                ),
                ("Te1/16", "admin down", "", ["101,103-105", "213,214"]),
            ],
        )


class TestCiscoGetMACAddress(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса Cisco.
        fake_session = CiscoPexpectFaker()
        # Создание объекта Cisco с fake_session, ip-адресом и авторизацией.
        cls.cisco = Cisco(fake_session, "10.10.10.10", auth=fake_auth)

    def test_get_mac(self):
        mac_list = self.cisco.get_mac("Gi0/1")

        self.assertEqual(
            mac_list,
            [
                (716, "2887.baf2.0f9a"),
                (716, "50ff.2028.f55b"),
                (716, "b0a7.b9c4.aa41"),
                (800, "80fb.06cb.ee68"),
            ],
        )

        mac_list_2 = self.cisco.get_mac("rea0/1")
        self.assertEqual(mac_list_2, [])


class TestCiscoPortControl(SimpleTestCase):
    # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса Cisco.
    fake_session = CiscoPexpectFaker()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создание объекта Cisco с fake_session, ip-адресом и авторизацией.
        cls.cisco = Cisco(cls.fake_session, "10.10.10.10", auth=fake_auth)

    def setUp(self) -> None:
        self.fake_session.sent_commands = []

    def test_reload_port(self):
        self.cisco.reload_port("Gi0/1")

        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "configure terminal",
                "interface GigabitEthernet 0/1",
                "shutdown",
                "no shutdown",
                "end",
                "write",
            ],
        )

    def test_reload_port_no_save(self):
        self.cisco.reload_port("Gi0/1", save_config=False)

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
        status = self.cisco.reload_port("Re0/1")

        self.assertEqual(status, "Неверный порт")

        self.assertEqual(
            self.fake_session.sent_commands,
            [],
        )

    def test_set_up_port(self):
        # Установка порта Te 0/1/2 на up.
        self.cisco.set_port("Te 0/1/2", "up")

        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "configure terminal",
                "interface TenGigabitEthernet 0/1/2",
                "no shutdown\n",
                "end\n",
                "write",
            ],
        )

    def test_set_up_port_no_save(self):
        # Установка порта Te 0/1/2 на up.
        self.cisco.set_port("Te 0/1/2", "up", save_config=False)

        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "configure terminal",
                "interface TenGigabitEthernet 0/1/2",
                "no shutdown\n",
                "end\n",
            ],
        )

    def test_set_up_invalid_port(self):
        status = self.cisco.set_port("Re 0/1/2", "up")

        self.assertEqual(status, "Неверный порт")

        self.assertEqual(
            self.fake_session.sent_commands,
            [],
        )

    def test_set_down_port(self):
        self.cisco.set_port("Fa 0/2", "down")

        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "configure terminal",
                "interface FastEthernet 0/2",
                "shutdown\n",
                "end\n",
                "write",
            ],
        )

    def test_set_down_invalid_port(self):
        status = self.cisco.set_port("Ra 0/2", "down")

        self.assertEqual(status, "Неверный порт")

        self.assertEqual(
            self.fake_session.sent_commands,
            [],
        )


class TestCiscoInfo(SimpleTestCase):
    # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса Cisco.
    fake_session = CiscoPexpectFaker()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создание объекта Cisco с fake_session, ip-адресом и авторизацией.
        cls.cisco = Cisco(cls.fake_session, "10.10.10.10", auth=fake_auth)

    def setUp(self) -> None:
        self.fake_session.sent_commands = []

    def test_get_port_info(self):
        self.cisco.get_port_info(port="Gi 0/1")

        self.assertEqual(
            self.fake_session.sent_commands,
            ["show interface GigabitEthernet 0/1"],
        )

    def test_invalid_get_port_info(self):
        status = self.cisco.get_port_info(port="Re 0/1")

        self.assertEqual({"type": "error", "data": "Неверный порт"}, status)

        self.assertEqual(self.fake_session.sent_commands, [])

    def test_port_type(self):
        valid_result = [
            "COPPER",  # 1
            "SFP",  # 2
            "SFP",  # 3
            "SFP",  # 4
            "SFP",  # 5
            "?",  # 6
            "?",  # 7
            "SFP",  # 8
            "?",  # 9
            "?",  # 10
            "COPPER",  # 11
            "SFP",  # 12
        ]
        for i in range(1, len(valid_result) + 1):
            self.assertEqual(valid_result[i - 1], self.cisco.get_port_type(f"Gi0/{i}"), f"Gi0/{i}")


class TestCiscoFindAddress(SimpleTestCase):
    # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса Cisco.
    fake_session = CiscoPexpectFaker()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создание объекта Cisco с fake_session, ip-адресом и авторизацией.
        cls.cisco = Cisco(cls.fake_session, "10.10.10.10", auth=fake_auth)

    def test_search_mac_address(self):
        result = self.cisco.search_mac("0000aaaa0000")
        self.assertEqual(
            result,
            [ArpInfoResult("10.100.10.100", "0000.aaaa.0000", "25")],
        )

        result = self.cisco.search_mac("0000ffff0000")
        self.assertEqual(
            result,
            [],
        )

    def test_search_mac_address_invalid_format(self):
        result = self.cisco.search_mac("0000.aaaa.0000")
        self.assertEqual(
            result,
            [],
        )
        result = self.cisco.search_mac("aaaa.0000")
        self.assertEqual(
            result,
            [],
        )

    def test_search_ip_address(self):
        result = self.cisco.search_ip("10.100.10.100")
        self.assertEqual(
            result,
            [ArpInfoResult("10.100.10.100", "0000.aaaa.0000", "25")],
        )

        result = self.cisco.search_ip("127.0.0.1")
        self.assertEqual(
            result,
            [],
        )


class TestCiscoPortDescription(SimpleTestCase):
    # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса Cisco.
    fake_session = CiscoPexpectFaker()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создание объекта Cisco с fake_session, ip-адресом и авторизацией.
        cls.cisco = Cisco(cls.fake_session, "10.10.10.10", auth=fake_auth)

    def setUp(self) -> None:
        self.fake_session.sent_commands = []

    def test_change_description(self):
        self.cisco.set_description("Gi0/1", "New [desc] \nновое описание")
        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "configure terminal",
                "interface GigabitEthernet 0/1",
                "description New_(desc)_novoe_opisanie",
                "end",
                "write",
            ],
        )

    def test_clear_description(self):
        self.cisco.set_description("Gi0/1", "")
        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "configure terminal",
                "interface GigabitEthernet 0/1",
                "no description",
                "end",
                "write",
            ],
        )
