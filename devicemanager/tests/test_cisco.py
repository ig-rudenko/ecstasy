import pathlib
import textfsm
from django.test import SimpleTestCase
from devicemanager.vendors.cisco import Cisco


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
        print(command)
        self.sent_commands.append(command)

        if command == "write":
            # Для случая 'OK'
            self.expect_cmd = 1

        if command == "show interfaces description":
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

        elif command == "show arp | include 0000.aaaa.0000":
            self.before = b"""
Internet  10.100.10.100             27   0000.aaaa.0000  ARPA   Vlan25
            """

        elif command == "show arp | include 10.100.10.100":
            self.before = b"""
Internet  10.100.10.100             27   0000.aaaa.0000  ARPA   Vlan25
            """

        elif "show interfaces GigabitEthernet " in command:
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

        elif "show running-config interface" in command and command.endswith("5"):
            self.before = b"""
Current configuration : 837 bytes
!
interface TenGigabitEthernet1/1
 switchport trunk allowed vlan 101,103-108
 switchport trunk allowed vlan add 213,214
 switchport trunk allowed vlan add 234-236
 switchport mode trunk
 load-interval 30
 shutdown
end
            """

        elif "show running-config interface" in command and command.endswith("9"):
            self.before = b"""
Current configuration : 837 bytes
!
interface TenGigabitEthernet1/1
 load-interval 30
 shutdown
end
            """

        elif "show running-config interface" in command:
            self.before = b"""
Current configuration : 837 bytes
!
interface FastEthernet0/2
 description L2VPN|1306|MirandaMedia|1M|YuBK_Genbank|17.03.2017|
 switchport access vlan 1230
 switchport mode access
 no cdp enable
end
            """

        elif command == "show version":
            self.before = b"""
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
        cisco = Cisco(session=CiscoPexpectFaker(), ip="10.10.10.10", auth={})

        self.assertEqual(cisco.mac, "F4:1F:C2:71:49:10")
        self.assertEqual(cisco.serialno, "FOC6734Z6AH")


class TestCiscoInterfaces(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TEMPLATE_DIR = pathlib.Path(__file__).parent.parent / "templates"
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса Cisco.
        fake_session = CiscoPexpectFaker()
        auth = {"privilege_mode_password": ""}
        # Создание объекта Cisco с fake_session, ip-адресом и авторизацией.
        cls.cisco = Cisco(fake_session, "10.10.10.10", auth=auth)

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
        # Получение интерфейсов от объекта dlink.
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
        # Получение интерфейсов и VLAN's от объекта cisco.
        interfaces_vlans = self.cisco.get_vlans()
        self.assertEqual(
            interfaces_vlans,
            [
                ("Te1/1", "admin down", "Desc1", ["1230"]),
                ("Te1/2", "admin down", "", ["1230"]),
                ("Te1/3", "up", "Desc3", ["1230"]),
                ("Te1/4", "up", "Desc4", ["1230"]),
                ("Te1/5", "admin down", "", ["101,103-108", "213,214", "234-236"]),
                ("Te1/6", "admin down", "Desc6", ["1230"]),
                ("Te1/7", "admin down", "", ["1230"]),
                ("Te1/8", "admin down", "", ["1230"]),
                ("Te1/9", "admin down", "", []),
                ("Te1/10", "admin down", "", ["1230"]),
                ("Te1/11", "admin down", "", ["1230"]),
                ("Te1/12", "up", "", ["1230"]),
                ("Te1/13", "admin down", "", ["1230"]),
                ("Te1/14", "admin down", "Desc14", ["1230"]),
                (
                    "Te1/15",
                    "up",
                    "Some description",
                    ["101,103-108", "213,214", "234-236"],
                ),
                ("Te1/16", "admin down", "", ["1230"]),
            ],
        )


class TestCiscoGetMACAddress(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса Cisco.
        fake_session = CiscoPexpectFaker()
        # Создание объекта Cisco с fake_session, ip-адресом и авторизацией.
        cls.cisco = Cisco(fake_session, "10.10.10.10", auth={})

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
        cls.cisco = Cisco(cls.fake_session, "10.10.10.10", auth={})

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
                "no shutdown",
                "end",
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
                "no shutdown",
                "end",
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
                "shutdown",
                "end",
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
        cls.cisco = Cisco(cls.fake_session, "10.10.10.10", auth={})

    def setUp(self) -> None:
        self.fake_session.sent_commands = []

    def test_get_port_info(self):
        self.cisco.get_port_info(port="Gi 0/1")

        self.assertEqual(
            self.fake_session.sent_commands,
            ["show interfaces GigabitEthernet 0/1"],
        )

    def test_invalid_get_port_info(self):
        status = self.cisco.get_port_info(port="Re 0/1")

        self.assertEqual(status, "Неверный порт")

        self.assertEqual(
            self.fake_session.sent_commands,
            [],
        )

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
            print(i)
            self.assertEqual(valid_result[i - 1], self.cisco.get_port_type(f"Gi0/{i}"))


class TestCiscoFindAddress(SimpleTestCase):
    # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса Cisco.
    fake_session = CiscoPexpectFaker()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создание объекта Cisco с fake_session, ip-адресом и авторизацией.
        cls.cisco = Cisco(cls.fake_session, "10.10.10.10", auth={})

    def test_search_mac_address(self):
        result = self.cisco.search_mac("0000aaaa0000")
        self.assertEqual(
            result,
            [["10.100.10.100", "0000.aaaa.0000", "25"]],
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
            [["10.100.10.100", "0000.aaaa.0000", "25"]],
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
        cls.cisco = Cisco(cls.fake_session, "10.10.10.10", auth={})

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
