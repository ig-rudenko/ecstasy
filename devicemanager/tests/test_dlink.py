import pathlib
import textfsm
from django.test import SimpleTestCase
from devicemanager.vendors.dlink import Dlink, validate_port


class DLinkPexpectFaker:
    """
    ## Это класс создает имитацию сессии pexpect для обработки команд DLink.
    """

    def __init__(self):
        self.before = b""
        self.sent_commands = []

    def send(self, command: str):
        return self.sendline(command.strip())

    def sendline(self, command):
        self.sent_commands.append(command)
        if command == "show vlan":
            self.before = b"""
VID             : 1           VLAN Name       : default
VLAN Type       : Static      Advertisement   : Enabled
Member Ports    : 27
Static Ports    : 27
Current Tagged Ports   :
Current Untagged Ports : 27
Static Tagged Ports    :
Static Untagged Ports  : 27
Forbidden Ports        :

VID             : 701         VLAN Name       : 701
VLAN Type       : Static      Advertisement   : Disabled
Member Ports    : 25-26
Static Ports    : 25-26
Current Tagged Ports   : 25-26
Current Untagged Ports :
Static Tagged Ports    : 25-26
Static Untagged Ports  :
Forbidden Ports        :

VID             : 1051        VLAN Name       : 1051
VLAN Type       : Static      Advertisement   : Disabled
Member Ports    : 1-26
Static Ports    : 1-26
Current Tagged Ports   : 25-26
Current Untagged Ports : 1-24
Static Tagged Ports    : 25-26
Static Untagged Ports  : 1-24
Forbidden Ports        :

VID             : 3333        VLAN Name       : MGMT
VLAN Type       : Static      Advertisement   : Disabled
Member Ports    : 25-26
Static Ports    : 25-26
Current Tagged Ports   : 25-26
Current Untagged Ports :
Static Tagged Ports    : 25-26
Static Untagged Ports  :
Forbidden Ports        :
"""
        elif command == "show ports des":
            self.before = b"""
Command: show ports description 
 
 Port   State/          Settings             Connection           Address 
        MDI       Speed/Duplex/FlowCtrl  Speed/Duplex/FlowCtrl    Learning 
 -----  --------  ---------------------  ---------------------    -------- 
 1      Disabled  Auto/Disabled          LinkDown                 Enabled 
        Auto 
 Desc: 
 2      Disabled  Auto/Disabled          LinkDown                 Enabled 
        Auto 
 Desc: 
 3      Enabled   Auto/Disabled          100M/Full/None           Enabled 
        Auto 
 Desc: desc3 
 4      Enabled   Auto/Disabled          LinkDown                 Enabled 
        Auto 
 Desc: 
 5      Enabled   Auto/Disabled          100M/Full/None           Enabled 
        Auto 
 Desc: desc5 
 6      Disabled  Auto/Disabled          LinkDown                 Enabled 
        Auto 
 Desc: 
 7      Enabled   Auto/Disabled          LinkDown                 Enabled 
        Auto 
 Desc: desc7 
 8      Disabled  Auto/Disabled          LinkDown                 Enabled 
        Auto 
 Desc: desc8 
 9      Enabled   Auto/Disabled          100M/Full/None           Enabled 
        Auto 
 Desc: desc9 
 10     Enabled   Auto/Disabled          LinkDown                 Enabled 
        Auto 
 Desc: 
 11     Enabled   Auto/Disabled          LinkDown                 Enabled 
        Auto 
 Desc: 
 12     Disabled  Auto/Disabled          LinkDown                 Enabled 
        Auto 
 Desc: desc12 
 13     Enabled   Auto/Disabled          LinkDown                 Enabled 
        Auto 
 Desc: 
 14     Enabled   10M/Full/Disabled      LinkDown                 Enabled 
        Auto 
 Desc: 
 15     Disabled  Auto/Disabled          LinkDown                 Enabled 
        Auto 
 Desc: 
 16     Disabled  Auto/Disabled          LinkDown                 Enabled 
        Auto 
 Desc: 
 17     Disabled  Auto/Disabled          LinkDown                 Enabled 
        Auto 
 Desc: 
 18     Enabled   Auto/Disabled          LinkDown                 Enabled 
        Auto 
 Desc: 
 19     Enabled   Auto/Disabled          100M/Full/None           Enabled 
        Auto 
 Desc: VOIP 
 20     Enabled   Auto/Disabled          LinkDown                 Enabled 
        Auto 
 Desc: 
 21     Enabled   Auto/Disabled          LinkDown                 Enabled 
        Auto 
 Desc: 
 22     Enabled   Auto/Disabled          LinkDown                 Enabled 
        Auto 
 Desc: VOIP 
 23     Enabled   Auto/Disabled          100M/Full/None           Enabled 
        Auto 
 Desc: 
 24     Enabled   Auto/Disabled          LinkDown                 Enabled 
        Auto 
 Desc: VOIP 
 25(C)  Enabled   Auto/Disabled          LinkDown                 Enabled 
        Auto 
 Desc: 
 25(F)  Enabled   Auto/Disabled          100M/Full/None           Enabled 
 
 Desc: desc25F 
 26(C)  Enabled   Auto/Disabled          LinkDown                 Enabled 
        Auto 
 Desc: 
 26(F)  Enabled   Auto/Disabled          LinkDown                 Enabled 
 
 Desc: 
 27     Enabled   Auto/Disabled          1000M/Full/None          Enabled 
 
 Desc: uplink27 
 28     Enabled   Auto/Disabled          LinkDown                 Enabled 
 
 Desc: uplink28 
Notes:(F)indicates fiber medium and (C)indicates copper medium in a combo port. 
"""
        elif command == "show switch":
            self.before = b"""
Command: show switch

Device Type        : DES-1228/ME Metro Ethernet Switch
MAC Address        : B8-A3-86-C2-65-20
IP Address         : 127.20.69.128 (Manual)
VLAN Name          : MGMT
Subnet Mask        : 255.255.254.0
Default Gateway    : 127.20.69.254
Boot PROM Version  : Build 2.00.R001
Firmware Version   : Build 2.63.B001
Hardware Version   : B1
Serial Number      : PPCM4BB014291
System Name        : Device_name
System Location    :
System Uptime      : 31 days, 22 hours, 56 minutes, 21 seconds
System Contact     :
Spanning Tree      : Disabled
GVRP               : Disabled
IGMP Snooping      : Enabled
VLAN Trunk         : Disabled
802.1X             : Disabled
Telnet             : Enabled (TCP 23)
Web                : Disabled
RMON               : Disabled
SSH                : Disabled
SSL                : Disabled
CLI Paging         : Disabled
Syslog Global State: Enabled
Dual Image         : Supported
Password Encryption Status : Enabled
"""
        elif command == "show fdb port 1":
            self.before = b"""
Command: show fdb port 1

VID  VLAN Name                        MAC Address       Port Type
---- -------------------------------- ----------------- ---- ---------------
111  Name111                          F4-28-54-06-33-85  1   Dynamic
121  121                              F4-28-54-06-33-86  1   Dynamic
Total Entries  : 1
"""
        elif command == "show fdb port 10":
            self.before = b"""
VID  VLAN Name                        MAC Address       Port Type
---- -------------------------------- ----------------- ---- ---------------

Total Entries  : 0
            """
        elif "cable_diag ports" in command:
            self.before = self._virtual_cable_test(command)
        elif (
            "config ports 2 description" in command or "config ports 2 clear_description" in command
        ):
            self.before = b"Success"
        else:
            self.before = b""

        return len(command)

    def expect(self, *args, **kwargs):
        return 0

    def _virtual_cable_test(self, command: str):
        port = int(command.split()[-1])
        data = {
            1: b"""
 Port   Type      Link Status          Test Result          Cable Length (M)
 ----  -------  --------------  -------------------------  -----------------
  1     FE         Link Down     Pair1 Open      at 36  M          - 
                                 Pair2 Open      at 36  M
            """,
            2: b"""
 Port   Type      Link Status          Test Result          Cable Length (M)
 ----  -------  --------------  -------------------------  -----------------
  2      FE         Link Up       OK                                35 
            """,
            3: b"""
 Port   Type      Link Status          Test Result          Cable Length (M)
 ----  -------  --------------  -------------------------  -----------------
  3     FE         Link Down     No Cable                          - 
            """,
            4: b"""
 Port   Type      Link Status          Test Result          Cable Length (M)
 ----  -------  --------------  -------------------------  -----------------
  4     FE         Link Down     Pair1 Open      at 2   M          - 
                                 Pair2 Open      at 2   M
            """,
            5: b"""
 Port   Type       Link Status           Test Result         Cable Length (M)
------  -------  --------------  -------------------------  -----------------
  5      FE         Link Down    Pair 1 Short     at   1M          -
                                 Pair 2 OK        at   3M
            """,
            6: b"""
 Port   Type    Link Status            Test Result           Cable Length (M)
 ----  ------  -------------  -----------------------------  ----------------
  6     GE      Link Up        The PHY can't support Cable Diagnostic
            """,
            7: b"""
Port      Type      Link Status    Test Result                 Cable Length (M)
------  ----------  -------------  -------------------------  -----------------
7       100BASE-X   Link Up        Unknown                           - 
            """,
            8: b"""
Port      Type      Link Status    Test Result                 Cable Length (M)
------  ----------  -------------  -------------------------  -----------------
8       1000BASE-T  Link Up        Pair 1 Short     at   1M          -
                                   Pair 2 OK        at   3M
                                   Pair 3 OK        at   1M
                                   Pair 4 Short     at   1M
            """,
            9: b"",
        }
        return data[port]


class TestDLinkInit(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса DLink.
        fake_session = DLinkPexpectFaker()
        auth = {"privilege_mode_password": ""}
        # Создание объекта Dlink с fake_session, ip-адресом и авторизацией.
        cls.dlink = Dlink(fake_session, "10.10.10.10", auth=auth)

    def test_show_switch_command(self):
        """
        Command: show switch

        Device Type        : DES-1228/ME Metro Ethernet Switch
        MAC Address        : B8-A3-86-C2-65-20
        IP Address         : 127.20.69.128 (Manual)
        VLAN Name          : MGMT
        Subnet Mask        : 255.255.254.0
        Default Gateway    : 127.20.69.254
        Boot PROM Version  : Build 2.00.R001
        Firmware Version   : Build 2.63.B001
        Hardware Version   : B1
        Serial Number      : PPCM4BB014291
        System Name        : Device_name
        System Location    :
        System Uptime      : 31 days, 22 hours, 56 minutes, 21 seconds
        System Contact     :
        Spanning Tree      : Disabled
        GVRP               : Disabled
        IGMP Snooping      : Enabled
        VLAN Trunk         : Disabled
        802.1X             : Disabled
        Telnet             : Enabled (TCP 23)
        Web                : Disabled
        RMON               : Disabled
        SSH                : Disabled
        SSL                : Disabled
        CLI Paging         : Disabled
        Syslog Global State: Enabled
        Dual Image         : Supported
        Password Encryption Status : Enabled

        """

        self.assertEqual(self.dlink.mac, "B8-A3-86-C2-65-20")
        self.assertEqual(self.dlink.model, "DES-1228/ME")
        self.assertEqual(self.dlink.serialno, "PPCM4BB014291")


class TestDLinkInterfaceParser(SimpleTestCase):
    """
    ## Тестируем регулярки для поиска интерфейсов и вланов,
    а также методы get_interfaces(), get_vlans()
    """

    @classmethod
    def setUpClass(cls):
        cls.TEMPLATE_DIR = pathlib.Path(__file__).parent.parent / "templates"
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса DLink.
        fake_session = DLinkPexpectFaker()
        auth = {"privilege_mode_password": ""}
        # Создание объекта Dlink с fake_session, ip-адресом и авторизацией.
        cls.dlink = Dlink(fake_session, "10.10.10.10", auth=auth)

    def test_interfaces_regexp(self):
        """
        ## Тестируем регулярное выражение для выходных данных команды «show ports description»
        """

        interfaces_output = """Command: show ports description 
 Port   State/          Settings             Connection           Address 
        MDI       Speed/Duplex/FlowCtrl  Speed/Duplex/FlowCtrl    Learning 
 -----  --------  ---------------------  ---------------------    --------
 1      Enabled   Auto/Disabled          LinkDown                 Enabled 
        Auto            
 Desc: Description1     
 2      Enabled   Auto/Disabled          LinkDown                 Enabled 
        Auto            
 Desc:                                                                   
 28(C)  Disabled  Auto/Disabled          LinkDown                 Enabled 
        Auto            
 Desc:          
 28(F)  Enabled   Auto/Disabled          1000M/Full/None          Enabled 
                        
 Desc: Description_for_28F          
Notes:(F)indicates fiber medium and (C)indicates copper medium in a combo port.
        """

        with open(self.TEMPLATE_DIR / "interfaces" / "d-link.template") as template_file:
            int_des_ = textfsm.TextFSM(template_file)
        result = int_des_.ParseText(interfaces_output)

        self.assertEqual(
            result,
            [
                ["1", "Enabled", "LinkDown", "Description1"],
                ["2", "Enabled", "LinkDown", ""],
                ["28(C)", "Disabled", "LinkDown", ""],
                ["28(F)", "Enabled", "1000M/Full/None", "Description_for_28F"],
            ],
        )

    def test_vlans_regexp(self):
        """
        ## Тестируем регулярное выражение для выходных данных команды «show vlan»
        """

        vlan_output = """
VID             : 1           VLAN Name       : default
VLAN Type       : Static      Advertisement   : Enabled
Member Ports    : 27
Static Ports    : 27
Current Tagged Ports   :
Current Untagged Ports : 27
Static Tagged Ports    :
Static Untagged Ports  : 27
Forbidden Ports        :

VID             : 701         VLAN Name       : 701
VLAN Type       : Static      Advertisement   : Disabled
Member Ports    : 25-26
Static Ports    : 25-26
Current Tagged Ports   : 25-26
Current Untagged Ports :
Static Tagged Ports    : 25-26
Static Untagged Ports  :
Forbidden Ports        :

VID             : 1051        VLAN Name       : 1051
VLAN Type       : Static      Advertisement   : Disabled
Member Ports    : 1-26
Static Ports    : 1-26
Current Tagged Ports   : 25-26
Current Untagged Ports : 1-24
Static Tagged Ports    : 25-26
Static Untagged Ports  : 1-24
Forbidden Ports        :

VID             : 3333        VLAN Name       : MGMT
VLAN Type       : Static      Advertisement   : Disabled
Member Ports    : 25-26
Static Ports    : 25-26
Current Tagged Ports   : 25-26
Current Untagged Ports :
Static Tagged Ports    : 25-26
Static Untagged Ports  :
Forbidden Ports        :
"""
        with open(self.TEMPLATE_DIR / "vlans_templates" / "d-link.template") as template_file:
            int_des_ = textfsm.TextFSM(template_file)
        result = int_des_.ParseText(vlan_output)

        self.assertEqual(
            result,
            [
                ["1", "default", "27"],
                ["701", "701", "25-26"],
                ["1051", "1051", "1-26"],
                ["3333", "MGMT", "25-26"],
            ],
        )

    def test_get_interfaces(self):
        """
        ## Через поддельный объект сеанса будем тестировать метод ```get_interfaces()```.

            Port   State/          Settings             Connection           Address
                   MDI       Speed/Duplex/FlowCtrl  Speed/Duplex/FlowCtrl    Learning
            -----  --------  ---------------------  ---------------------    --------
            1      Disabled  Auto/Disabled          LinkDown                 Enabled
                   Auto
            Desc:
            2      Disabled  Auto/Disabled          LinkDown                 Enabled
                   Auto
            Desc:
            ...
        """

        # Получение интерфейсов от объекта dlink.
        interfaces = self.dlink.get_interfaces()

        self.assertEqual(
            interfaces,
            [
                ("1", "admin down", ""),
                ("2", "admin down", ""),
                ("3", "100M/Full/None", "desc3"),
                ("4", "down", ""),
                ("5", "100M/Full/None", "desc5"),
                ("6", "admin down", ""),
                ("7", "down", "desc7"),
                ("8", "admin down", "desc8"),
                ("9", "100M/Full/None", "desc9"),
                ("10", "down", ""),
                ("11", "down", ""),
                ("12", "admin down", "desc12"),
                ("13", "down", ""),
                ("14", "down", ""),
                ("15", "admin down", ""),
                ("16", "admin down", ""),
                ("17", "admin down", ""),
                ("18", "down", ""),
                ("19", "100M/Full/None", "VOIP"),
                ("20", "down", ""),
                ("21", "down", ""),
                ("22", "down", "VOIP"),
                ("23", "100M/Full/None", ""),
                ("24", "down", "VOIP"),
                ("25(C)", "down", ""),
                ("25(F)", "100M/Full/None", "desc25F"),
                ("26(C)", "down", ""),
                ("26(F)", "down", ""),
                ("27", "1000M/Full/None", "uplink27"),
                ("28", "down", "uplink28"),
            ],
        )

    def test_get_vlans(self):
        """
        ## Через поддельный объект сеанса будем тестировать метод ```get_vlans()```.
        """

        # Получение вланов с коммутатора dlink.
        interfaces_vlans = self.dlink.get_vlans()

        self.assertEqual(
            interfaces_vlans,
            [
                ("1", "admin down", "", ["1051"]),
                ("2", "admin down", "", ["1051"]),
                ("3", "100M/Full/None", "desc3", ["1051"]),
                ("4", "down", "", ["1051"]),
                ("5", "100M/Full/None", "desc5", ["1051"]),
                ("6", "admin down", "", ["1051"]),
                ("7", "down", "desc7", ["1051"]),
                ("8", "admin down", "desc8", ["1051"]),
                ("9", "100M/Full/None", "desc9", ["1051"]),
                ("10", "down", "", ["1051"]),
                ("11", "down", "", ["1051"]),
                ("12", "admin down", "desc12", ["1051"]),
                ("13", "down", "", ["1051"]),
                ("14", "down", "", ["1051"]),
                ("15", "admin down", "", ["1051"]),
                ("16", "admin down", "", ["1051"]),
                ("17", "admin down", "", ["1051"]),
                ("18", "down", "", ["1051"]),
                ("19", "100M/Full/None", "VOIP", ["1051"]),
                ("20", "down", "", ["1051"]),
                ("21", "down", "", ["1051"]),
                ("22", "down", "VOIP", ["1051"]),
                ("23", "100M/Full/None", "", ["1051"]),
                ("24", "down", "VOIP", ["1051"]),
                ("25(C)", "down", "", ["701", "1051", "3333"]),
                ("25(F)", "100M/Full/None", "desc25F", ["701", "1051", "3333"]),
                ("26(C)", "down", "", ["701", "1051", "3333"]),
                ("26(F)", "down", "", ["701", "1051", "3333"]),
                ("27", "1000M/Full/None", "uplink27", ["1"]),
                ("28", "down", "uplink28", []),
            ],
        )


class TestDLinkMAC(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса DLink.
        fake_session = DLinkPexpectFaker()
        auth = {"privilege_mode_password": ""}
        # Создание объекта Dlink с fake_session, ip-адресом и авторизацией.
        cls.dlink = Dlink(fake_session, "10.10.10.10", auth=auth)

    def test_get_mac(self):
        """
        ## Через поддельный объект сеанса будем тестировать метод ```get_mac()```.

            Command: show fdb port 1

            VID  VLAN Name                        MAC Address       Port Type
            ---- -------------------------------- ----------------- ---- ---------------
            111  Name111                          F4-28-54-06-33-85  1   Dynamic
            121  121                              F4-28-54-06-33-86  1   Dynamic
            Total Entries  : 1

        """
        mac_result = self.dlink.get_mac("1")

        self.assertEqual(
            mac_result,
            [
                (111, "F4-28-54-06-33-85"),
                (121, "F4-28-54-06-33-86"),
            ],
        )

    def test_get_mac_empty(self):
        """
        ## Через поддельный объект сеанса будем тестировать метод ```get_mac()```.

            Command: show fdb port 1

            VID  VLAN Name                        MAC Address       Port Type
            ---- -------------------------------- ----------------- ---- ---------------
            Total Entries  : 0

        """
        mac_result = self.dlink.get_mac("10")
        self.assertEqual(mac_result, [])


class TestDLinkPortStateControl(SimpleTestCase):
    def setUp(self) -> None:
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса DLink.
        self.fake_session = DLinkPexpectFaker()
        auth = {"privilege_mode_password": ""}
        # Создание объекта Dlink с fake_session, ip-адресом и авторизацией.
        self.dlink = Dlink(self.fake_session, "10.10.10.10", auth=auth)
        self.fake_session.sent_commands = []

    def test_port_reload_commands(self):
        self.dlink.reload_port("26(F)", save_config=False)
        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "config ports 26 medium_type fiber state disable",
                "config ports 26 medium_type fiber state enable",
            ],
        )
        self.fake_session.sent_commands = []

        self.dlink.reload_port("26(F)", save_config=True)
        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "config ports 26 medium_type fiber state disable",
                "config ports 26 medium_type fiber state enable",
                "save",
            ],
        )
        self.fake_session.sent_commands = []

        self.dlink.reload_port("24")
        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "config ports 24 state disable",
                "config ports 24 medium_type fiber state disable",
                "config ports 24 state enable",
                "config ports 24 medium_type fiber state enable",
                "save",
            ],
        )
        self.fake_session.sent_commands = []

        self.dlink.reload_port("23")
        self.assertEqual(
            self.fake_session.sent_commands,
            ["config ports 23 state disable", "config ports 23 state enable", "save"],
        )
        self.fake_session.sent_commands = []

    def test_port_set_up_down_commands(self):
        # переводит оптический порт 26 в состояние up и НЕ сохраняет конфигурацию.
        self.dlink.set_port(port="26(F)", status="up", save_config=False)
        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "config ports 26 medium_type fiber state enable",
            ],
        )
        self.fake_session.sent_commands = []

        # переводит оптический порт 26 в состояние down и сохраняет конфигурацию.
        self.dlink.set_port(port="26(F)", status="down", save_config=True)
        self.assertEqual(
            self.fake_session.sent_commands,
            ["config ports 26 medium_type fiber state disable", "save"],
        )
        self.fake_session.sent_commands = []

        # переводит порт 23 в состояние up и сохраняет конфигурацию.
        self.dlink.set_port(port="24", status="up", save_config=True)
        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "config ports 24 state enable",
                "config ports 24 medium_type fiber state enable",
                "save",
            ],
        )
        self.fake_session.sent_commands = []

        # переводит порт 23 в состояние down и сохраняет конфигурацию.
        self.dlink.set_port(port="23", status="down", save_config=True)
        self.assertEqual(
            self.fake_session.sent_commands,
            ["config ports 23 state disable", "save"],
        )
        self.fake_session.sent_commands = []

    def test_invalid_port(self):
        res = self.dlink.set_port(port="3C", status="down")
        self.assertEqual(res, "Неверный порт")
        self.assertEqual(
            self.fake_session.sent_commands,
            [],
        )

        res = self.dlink.reload_port(port="3C")
        self.assertEqual(res, "Неверный порт")
        self.assertEqual(
            self.fake_session.sent_commands,
            [],
        )


class TestDLinkCableDiag(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса DLink.
        fake_session = DLinkPexpectFaker()
        auth = {"privilege_mode_password": ""}
        # Создание объекта Dlink с fake_session, ip-адресом и авторизацией.
        cls.dlink = Dlink(fake_session, "10.10.10.10", auth=auth)

    def test_virtual_cable_test(self):
        valid_results = [
            # 1
            {
                "len": "-",
                "status": "Down",
                "pair1": {"status": "open", "len": "36"},
                "pair2": {"status": "open", "len": "36"},
            },
            # 2
            {"len": "35", "status": "Up"},
            # 3
            {"len": "-", "status": "Empty"},
            # 4
            {
                "len": "-",
                "status": "Down",
                "pair1": {"status": "open", "len": "2"},
                "pair2": {"status": "open", "len": "2"},
            },
            # 5
            {
                "len": "-",
                "status": "Down",
                "pair1": {"status": "short", "len": "1"},
                "pair2": {"status": "ok", "len": "3"},
            },
            # 6
            {"len": "-", "status": "Don't support Cable Diagnostic"},
            # 7
            {"len": "-", "status": "Don't support Cable Diagnostic"},
            # 8
            {
                "len": "-",
                "status": "Up",
                "pair1": {"status": "short", "len": "1"},
                "pair2": {"status": "ok", "len": "3"},
                "pair3": {"status": "ok", "len": "1"},
                "pair4": {"status": "short", "len": "1"},
            },
            # 9
            {"len": "-", "status": "None"},
        ]
        for port_num in range(1, 10):
            res = self.dlink.virtual_cable_test(str(port_num))
            self.assertEqual(valid_results[port_num - 1], res)


class TestDLinkPortValid(SimpleTestCase):
    """
    Проверяем порт на валидность
    """

    def test_port(self):
        self.assertEqual(validate_port("1/2"), "2")
        self.assertEqual(validate_port("23"), "23")
        self.assertEqual(validate_port("26(C)"), "26")
        self.assertEqual(validate_port("1c"), None)


class TestCiscoPortDescription(SimpleTestCase):
    # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса Dlink.
    fake_session = DLinkPexpectFaker()

    @classmethod
    def setUpClass(cls):
        auth = {"privilege_mode_password": ""}
        # Создание объекта Dlink с fake_session, ip-адресом и авторизацией.
        cls.dlink = Dlink(cls.fake_session, "10.10.10.10", auth=auth)

    def setUp(self) -> None:
        self.fake_session.sent_commands = []

    def test_change_description(self):
        self.dlink.set_description("2", "New [desc] \n")
        self.assertEqual(
            self.fake_session.sent_commands,
            ["config ports 2 description New_(desc)_", "save"],
        )

    def test_clear_description(self):
        self.dlink.set_description("2", "")
        self.assertEqual(
            self.fake_session.sent_commands,
            ["config ports 2 clear_description", "save"],
        )

    def test_description_invalid_port(self):
        self.dlink.set_description("req", "")
        self.assertEqual(
            self.fake_session.sent_commands,
            [],
        )
        self.dlink.set_description("req", "desc")
        self.assertEqual(
            self.fake_session.sent_commands,
            [],
        )

    def test_error_description_result(self):
        # Для состояния, когда после изменения описания оборудование не отправляет Success
        self.dlink.set_description("3", "новое описание")
        self.assertEqual(
            self.fake_session.sent_commands,
            ["config ports 3 description novoe_opisanie"],
        )
