from django.test import SimpleTestCase
from devicemanager.vendors.edge_core import EdgeCore


class EdgeCorePexpectFaker:
    """
    ## Это класс создает имитацию сессии pexpect для обработки команд EdgeCore.
    """

    def __init__(self):
        self.before = b""
        self.sent_commands = []
        self.expect_cmd = 0

    def send(self, command: str):
        return self.sendline(command.strip())

    def sendline(self, command):
        self.sent_commands.append(command)

        if command == "show interfaces status":
            self.before = b"""
Information of Eth 1/1
 Basic information:
  Port type: SFP
  Mac address: 70-72-CF-20-75-51
 Configuration:
  Name: Description1
  Port admin: Up
  Speed-duplex: Auto
  Capabilities: 1000full
  Broadcast storm: Enabled
  Broadcast storm limit: 500 packets/second
  Flow control: Disabled
  LACP: Disabled
  Port security: Disabled
  Max MAC count: 0
  Port security action: None
  Combo forced mode: None
 Current status:
  Link status: Up
  Port operation status: Up
  Operation speed-duplex: 1000full
  Flow control type: None

Information of Eth 1/2
 Basic information:
  Port type: SFP
  Mac address: 70-72-CF-20-75-52
 Configuration:
  Name: Description2
  Port admin: Up
  Speed-duplex: Auto
  Capabilities: 1000full
  Broadcast storm: Enabled
  Broadcast storm limit: 500 packets/second
  Flow control: Disabled
  LACP: Disabled
  Port security: Disabled
  Max MAC count: 0
  Port security action: None
  Combo forced mode: None
 Current status:
  Link status: Up
  Port operation status: Up
  Operation speed-duplex: 1000full
  Flow control type: None
            """

        elif command == "show running-config":
            self.before = b"""
!
no spanning-tree
!
spanning-tree MST-configuration
!
!
!
!
interface ethernet 1/1
 description Description11
 switchport allowed VLAN add 1 untagged
 switchport native VLAN 1
 switchport allowed VLAN add 3738 tagged
!
interface ethernet 1/2
 description Description22
 switchport allowed VLAN add 1 untagged
 switchport native VLAN 1
 switchport allowed VLAN add 818,1054 tagged
!
!
!
!
interface VLAN 1
!
!
i
            """

        elif command == "show mac-address-table interface Ethernet 1/1":
            self.before = b"""
Vty-0# show mac-address-table interface ethernet 1/3
 Interface MAC Address       VLAN Type
 --------- ----------------- ---- -----------------
  Eth 1/ 1 08-55-31-0A-99-4B    1 Learned
  Eth 1/ 3 08-55-31-0A-99-4B 3738 Learned
  Eth 1/12 B4-4C-3B-51-5C-2E 3738 Learned
  Eth 1/12 B4-4C-3B-51-5F-8F 3738 Learned
Vty-0#
            """

        elif command == "show interfaces status GigabitEthernet 0/1":
            self.before = b"""
 Basic information:
  Port type: SFP
  Mac address: 70-72-CF-20-75-51
  ...
  Max MAC count: 0
  Port security action: None
  Combo forced mode: None
 Current status:

            """
        elif command == "show interfaces status GigabitEthernet 0/2":
            self.before = b"""
 Basic information:
  Port type: SFP
  Mac address: 70-72-CF-20-75-51
  ...
  Max MAC count: 0
  Port security action: None
  Combo forced mode: SFP preferred auto
 Current status:
                   """
        elif command == "show interfaces status GigabitEthernet 0/3":
            self.before = b"""
 Basic information:
  Port type: 1000T
  Mac address: 70-72-CF-20-75-5C
  ...
  Max MAC count: 0
  Port security action: None
  Combo forced mode: None
 Current status:
                          """
        elif command == "show interfaces status GigabitEthernet 0/4":
            self.before = b"""
 Basic information:
  Port type: 1000T
  Mac address: 70-72-CF-20-75-5C
  ...
  Max MAC count: 0
  Port security action: None
  Combo forced mode: SFP preferred auto
 Current status:
                   """

    def expect(self, *args, **kwargs):
        return 0


class TestEdgeCoreInterfaces(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса EdgeCore.
        fake_session = EdgeCorePexpectFaker()
        # Создание объекта EdgeCore с fake_session, ip-адресом и авторизацией.
        cls.edge_core = EdgeCore(fake_session, "10.10.10.10", auth={})

    def test_get_interfaces(self):
        # Получение интерфейсов от объекта edge core.
        interfaces = self.edge_core.get_interfaces()
        self.assertEqual(
            interfaces,
            [
                ("Eth 1/1", "up", "Description1"),
                ("Eth 1/2", "up", "Description2"),
            ],
        )

    def test_get_vlans(self):
        # Получение интерфейсов и VLAN's от объекта edge_core.
        interfaces_vlans = self.edge_core.get_vlans()
        self.assertEqual(
            interfaces_vlans,
            [
                ("Eth 1/1", "up", "Description1", ["1", "3738"]),
                ("Eth 1/2", "up", "Description2", ["1", "1054", "818"]),
            ],
        )


class TestEdgeCoreMAC(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса EdgeCore.
        fake_session = EdgeCorePexpectFaker()
        # Создание объекта EdgeCore с fake_session, ip-адресом и авторизацией.
        cls.edge_core = EdgeCore(fake_session, "10.10.10.10", auth={})

    def test_get_mac(self):
        mac_result = self.edge_core.get_mac(port="eth 1/1")

        self.assertEqual(
            mac_result,
            [
                ("1", "08-55-31-0A-99-4B"),
                ("3738", "08-55-31-0A-99-4B"),
                ("3738", "B4-4C-3B-51-5C-2E"),
                ("3738", "B4-4C-3B-51-5F-8F"),
            ],
        )

    def test_get_mac_invalid_port(self):
        mac_result = self.edge_core.get_mac(port="re 1/1")

        self.assertEqual(
            mac_result,
            [],
        )


class TestEdgeCorePortControl(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса EdgeCore.
        cls.fake_session = EdgeCorePexpectFaker()
        # Создание объекта EdgeCore с fake_session, ip-адресом и авторизацией.
        cls.edge_core = EdgeCore(cls.fake_session, "10.10.10.10", auth={})

    def setUp(self) -> None:
        self.fake_session.sent_commands = []

    def test_reload_port(self):

        self.edge_core.reload_port("Gi 0/1")

        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "configure",
                "interface GigabitEthernet 0/1",
                "shutdown",
                "no shutdown",
                "end",
                "copy running-config startup-config",
                "\n",  # подтверждаем сохранение
            ],
        )

    def test_reload_invalid_port(self):

        self.edge_core.reload_port("Ri0/1")

        self.assertEqual(
            self.fake_session.sent_commands,
            [],
        )

    def test_set_port_up(self):

        self.edge_core.set_port("Gi 0/1", "up")

        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "configure",
                "interface GigabitEthernet 0/1",
                "no shutdown",
                "end",
                "copy running-config startup-config",
                "\n",  # подтверждаем сохранение
            ],
        )

    def test_set_port_down(self):

        self.edge_core.set_port("Gi 0/1", "down")

        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "configure",
                "interface GigabitEthernet 0/1",
                "shutdown",
                "end",
                "copy running-config startup-config",
                "\n",  # подтверждаем сохранение
            ],
        )

    def test_set_invalid_port_up(self):

        self.edge_core.set_port("Ri0/1", "up")

        self.assertEqual(
            self.fake_session.sent_commands,
            [],
        )

    def test_set_invalid_port_down(self):

        self.edge_core.set_port("i0/1", "down")

        self.assertEqual(
            self.fake_session.sent_commands,
            [],
        )


class TestEdgeCoreInfo(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса EdgeCore.
        cls.fake_session = EdgeCorePexpectFaker()
        # Создание объекта EdgeCore с fake_session, ip-адресом и авторизацией.
        cls.edge_core = EdgeCore(cls.fake_session, "10.10.10.10", auth={})

    def setUp(self) -> None:
        self.fake_session.sent_commands = []

    def test_get_port_info_cache(self):
        """
        Он проверяет функцию get_port_info_cache.
        """
        info1 = self.edge_core.get_port_info("Gi0/1")
        self.assertEqual(
            self.fake_session.sent_commands,
            ["show interfaces status GigabitEthernet 0/1"],
        )
        info2 = self.edge_core.get_port_info("Gi0/1")
        self.assertEqual(
            self.fake_session.sent_commands,
            ["show interfaces status GigabitEthernet 0/1"],
        )
        info3 = self.edge_core.get_port_info("Gi0/1")
        self.assertEqual(
            self.fake_session.sent_commands,
            ["show interfaces status GigabitEthernet 0/1"],
        )
        self.assertEqual(info1, info2)
        self.assertEqual(info2, info3)


class TestEdgeCorePortType(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса EdgeCore.
        cls.fake_session = EdgeCorePexpectFaker()
        # Создание объекта EdgeCore с fake_session, ip-адресом и авторизацией.
        cls.edge_core = EdgeCore(cls.fake_session, "10.10.10.10", auth={})

    def test_port_type_sfp(self):
        """
        Эта функция проверяет тип SFP-портов на коммутаторе.
        """
        port_type = self.edge_core.get_port_type("Gi0/1")
        self.assertEqual(port_type, "SFP")

        port_type = self.edge_core.get_port_type("Gi0/2")
        self.assertEqual(port_type, "COMBO-SFP")

    def test_port_type_copper(self):
        """
        Эта функция проверяет тип медных портов.
        """
        port_type = self.edge_core.get_port_type("Gi0/3")
        self.assertEqual(port_type, "COPPER")

        port_type = self.edge_core.get_port_type("Gi0/4")
        self.assertEqual(port_type, "COMBO-COPPER")


class TestEdgeCoreGetConfig(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса EdgeCore.
        cls.fake_session = EdgeCorePexpectFaker()
        # Создание объекта EdgeCore с fake_session, ip-адресом и авторизацией.
        cls.edge_core = EdgeCore(cls.fake_session, "10.10.10.10", auth={})

    def test_get_port_config(self):

        valid_port_config = (
            "interface ethernet 1/1\n"
            " description Description11\n"
            " switchport allowed VLAN add 1 untagged\n"
            " switchport native VLAN 1\n"
            " switchport allowed VLAN add 3738 tagged"
        )

        port_config = self.edge_core.get_port_config("Eth1/1")
        self.assertEqual(self.fake_session.sent_commands, ["show running-config"])

        self.assertEqual(port_config, valid_port_config)


class TestEdgeCorePortDescriptions(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        # Создание поддельного объекта сеанса, который будет использоваться для тестирования класса EdgeCore.
        cls.fake_session = EdgeCorePexpectFaker()
        # Создание объекта EdgeCore с fake_session, ip-адресом и авторизацией.
        cls.edge_core = EdgeCore(cls.fake_session, "10.10.10.10", auth={})

    def setUp(self) -> None:
        self.fake_session.sent_commands = []

    def test_clear_description(self):
        self.edge_core.set_description("Gi0/1", "")

        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "configure",
                "interface GigabitEthernet 0/1",
                "no description",
                "end",
                "copy running-config startup-config",
                "\n",  # подтверждаем сохранение
            ],
        )

    def test_set_description(self):
        self.edge_core.set_description("Gi0/1", "New [desc] \nновое описание")

        self.assertEqual(
            self.fake_session.sent_commands,
            [
                "configure",
                "interface GigabitEthernet 0/1",
                "description New_(desc)_novoe_opisanie",
                "end",
                "copy running-config startup-config",
                "\n",  # подтверждаем сохранение
            ],
        )
