from django.test import SimpleTestCase

from devicemanager.vendors.zte import ZTE
from .base_factory_test import AbstractTestFactory


class TestZTEFactory(AbstractTestFactory):
    @staticmethod
    def get_device_class():
        return ZTE

    @staticmethod
    def get_output_from_show_version_command() -> str:
        return """
    ZXR10 Router Operating System Software, ZTE Corporation:
    ZXR10 2928E Version Number    : 2900E Series V2.05.10B25
    Copyright (c) 2001-2013 By ZTE Corporation
    Compiled: 11:44:45 Jul  2 2013
    System uptime is  0 years 93 days 13 hours 19 minutes 58 seconds

    Main processor       : arm926ejs
    Bootrom Version      : v1.28       Creation Date : Jun 24 2013
    System Memory        : 128 M bytes System Flash  : 256 M bytes
    EPLD Version (Dno.)  : V1.3
    PCB  Version (Dno.)  : V1.0
    Product Version(Dno.): V1.0
    Startup From         : /img/zImage
    Switch's Mac Address : 00.22.93.11.22.33
    Module 0:      ZXR10 2928E; fasteth: 24; gbit:  4;"""


class FakeZTE2936FISession:
    def __init__(self):
        self._output = b""

    @staticmethod
    def expect(*args, **kwargs):
        return 0

    @property
    def before(self) -> bytes:
        return self._output

    def send(self, *args, **kwargs):
        return self.sendline(*args, **kwargs)

    def sendline(self, command, *args, **kwargs):
        if command == "show port\n":
            self._output = b"""
  PortId     : 1
  Description: Desc1
  PortParams :
    PortEnable     : enabled       MediaType      : 100BaseT
    Duplex         : auto          Speed          : 10Mbps
    DefaultVlanId  : 702           FlowControl    : disabled
    Multicastfilter: default       Security       : disabled
    SpeedAdvertise : maxSpeed      Mdix           : auto
    AcceptFrame    : all           Jumbo          : disabled
    MTU            : 1522B         ProtocolVlan   : disabled
    EgressTPID     : 0x8100        PortVlanJump   : disabled
  PortStatus :
    PortClass      : 802.3         Link           : up
    Duplex         : half          Speed          : 10Mbps
    DownTime       : 0 years   0 days  3 hours 18 minutes 21 seconds
    RecentUpTime   : 0 years   0 days  0 hours  6 minutes  6 seconds

  PortId     : 2
  PortParams :
    PortEnable     : disable       MediaType      : 100BaseT
    Duplex         : auto          Speed          : auto
    DefaultVlanId  : 702           FlowControl    : disabled
    Multicastfilter: default       Security       : disabled
    SpeedAdvertise : maxSpeed      Mdix           : auto
    AcceptFrame    : all           Jumbo          : disabled
    MTU            : 1522B         ProtocolVlan   : disabled
    EgressTPID     : 0x8100        PortVlanJump   : disabled
  PortStatus :
    PortClass      : 802.3         Link           : down
    Duplex         : half          Speed          : 10Mbps
    DownTime       : 0 years  93 days 13 hours 21 minutes 23 seconds
    RecentUpTime   : 0 years   0 days  0 hours  0 minutes  0 seconds

  PortId     : 3
  PortParams : Desc3
    PortEnable     : enabled       MediaType      : 100BaseT
    Duplex         : auto          Speed          : auto
    DefaultVlanId  : 702           FlowControl    : disabled
    Multicastfilter: default       Security       : disabled
    SpeedAdvertise : maxSpeed      Mdix           : auto
    AcceptFrame    : all           Jumbo          : disabled
    MTU            : 1522B         ProtocolVlan   : disabled
    EgressTPID     : 0x8100        PortVlanJump   : disabled
  PortStatus :
    PortClass      : 802.3         Link           : down
    Duplex         : half          Speed          : 10Mbps
    DownTime       : 0 years  93 days 13 hours 21 minutes 23 seconds
    RecentUpTime   : 0 years   0 days  0 hours  0 minutes  0 seconds

  PortId     : 4
  PortParams :
    PortEnable     : enabled       MediaType      : 100BaseT
    Duplex         : auto          Speed          : auto
    DefaultVlanId  : 702           FlowControl    : disabled
    Multicastfilter: default       Security       : disabled
    SpeedAdvertise : maxSpeed      Mdix           : auto
    AcceptFrame    : all           Jumbo          : disabled
    MTU            : 1522B         ProtocolVlan   : disabled
    EgressTPID     : 0x8100        PortVlanJump   : disabled
  PortStatus :
    PortClass      : 802.3         Link           : down
    Duplex         : half          Speed          : 10Mbps
    DownTime       : 0 years  93 days 13 hours 21 minutes 23 seconds
    RecentUpTime   : 0 years   0 days  0 hours  0 minutes  0 seconds"""
        elif command == "show vlan\n":
            self._output = b"""
  VlanType: 802.1q vlan

  VlanId  : 1     VlanStatus: enabled
  VlanName:
  VlanMode: Static
  Tagged ports    :
  Untagged ports  :
  Forbidden ports :

  VlanId  : 782   VlanStatus: enabled
  VlanName: Clients
  VlanMode: Static
  Tagged ports    : 28
  Untagged ports  : 1-2
  Forbidden ports :

  VlanId  : 1442  VlanStatus: enabled
  VlanName: DHCP
  VlanMode: Static
  Tagged ports    : 2,4
  Untagged ports  :
  Forbidden ports :

  VlanId  : 3232  VlanStatus: enabled
  VlanName: Manage
  VlanMode: Static
  Tagged ports    : 3
  Untagged ports  :
  Forbidden ports :

  Total Vlans: 4
"""
        elif command == "show fdb detail\n":
            self._output = self._show_fdb_detail_output()
        elif "show fdb port" in command:
            self._output = self._show_fdb_port()
        elif command == "show vct port 1\n":
            self._output = b"""
  Cable Test Result for Port 1
  RX PAIR :
    Cable Test Passed. Cable is open.
    Approximately 71 meters from the tested port.
  TX PAIR :
    Cable Test Passed. Cable is open.
    Approximately 71 meters from the tested port."""
        elif command == "show vct port 2\n":
            self._output = b"""
  Cable Test Result for Port 2
  RX PAIR :
    Cable Test Passed. No problem found.
    Cable Length is unknown.
  TX PAIR :
    Cable Test Passed. No problem found.
    Cable Length is unknown."""
        elif command == "show vct port 9\n":
            self._output = b"""  %  Port 9 doesn't support VCT!"""

    @staticmethod
    def _show_fdb_detail_output() -> bytes:
        return b"""
  1c.69.7a.11.22.85 1052  28       dynamic
  d4.5d.64.11.22.91 3764  36       dynamic
  c4.2f.90.11.22.c9 2850  36       dynamic
  8c.1a.bf.11.22.e0 3764  36       security
  00.22.93.11.22.dc 3991  CPU      static
  Total: 529
"""

    @staticmethod
    def _show_fdb_port(port: str = "1"):
        return b"""
              MacAddress        Vlan  PortId   Type
  ----------------- ----- -------- --------
  00.00.01.11.22.45 888   2        dynamic
  00.e0.b3.11.22.aa 888   2        dynamic
  Total: 2       Dynamic: 2     Static: 0     Fixed: 0
"""


class TestZTE2936FI(SimpleTestCase):
    def setUp(self) -> None:
        self.device = ZTE(
            session=FakeZTE2936FISession(),
            ip="10.10.10.10",
            snmp_community="",
            auth={
                "login": "user",
                "password": "passwd",
                "privilege_mode_password": "secret",
            },
        )

    def test_get_interfaces(self):
        res = self.device.get_interfaces()
        self.assertEqual(
            res,
            [
                ("1", "up", "Desc1"),
                ("2", "admin down", ""),
                ("3", "down", ""),
                ("4", "down", ""),
            ],
        )

    def test_get_vlans(self):
        res = self.device.get_vlans()
        self.assertEqual(
            res,
            [
                ("1", "up", "Desc1", [782]),
                ("2", "admin down", "", [782, 1442]),
                ("3", "down", "", [3232]),
                ("4", "down", "", [1442]),
            ],
        )

    def test_get_mac_table(self):
        res = self.device.get_mac_table()
        self.assertListEqual(
            res,
            [
                (1052, "1c.69.7a.11.22.85", "dynamic", "28"),
                (3764, "d4.5d.64.11.22.91", "dynamic", "36"),
                (2850, "c4.2f.90.11.22.c9", "dynamic", "36"),
                (3764, "8c.1a.bf.11.22.e0", "security", "36"),
            ],
        )

    def test_get_mac(self):
        res = self.device.get_mac("2")
        self.assertListEqual(res, [(888, "00.00.01.11.22.45"), (888, "00.e0.b3.11.22.aa")])

    def test_cable_diag(self):
        res = self.device.virtual_cable_test("1")
        self.assertDictEqual(
            res,
            {
                "len": "-",
                "status": "Open",
                "pair1": {"status": "open", "len": "71"},
                "pair2": {"status": "open", "len": "71"},
            },
        )

        res = self.device.virtual_cable_test("2")
        self.assertDictEqual(
            res,
            {"len": "-", "status": "Up"},
        )

        res = self.device.virtual_cable_test("9")
        self.assertDictEqual(
            res,
            {"len": "-", "status": "Doesn't support VCT"},
        )


class FakeZTE2928ESession(FakeZTE2936FISession):
    @staticmethod
    def _show_fdb_detail_output() -> bytes:
        return b"  %  Command not found (0x40000034)"

    @staticmethod
    def _show_fdb_port(port: str = "1"):
        return b"  %  Command not found (0x40000034)"

    def sendline(self, command, *args, **kwargs):
        super().sendline(command, *args, **kwargs)

        if command == "show mac\n":
            self._output = b""" Total MAC Address : 138

 Flags: Per - permanent, Stc - static, ToP - to_permanent, ToS - to_static,
        Sav - auto saved mac address, SrF - source filter,
        DsF - destination filter, Time - day:hour:min:sec,
        Frm - mac from where:0,LEARN; 1,CONFIG; 2,DUPLICATE; 3,VPN; 4,802.1X;
                             5,LAYER-3; 6,DHCP

  MAC-Address  Vlan-Id   Port    Per Stc ToP ToS Sav SrF DsF Frm      Time
-------------------------------------------------------------------------------
8416.1122.bcff   702   port-1     0   0   0   0  -    0   0   0    00:16:39:28
dc2c.1122.f457  1052   port-28    0   0   0   0  -    0   0   0    00:00:10:25
0021.1122.386c   702   port-28    0   0   0   0  -    0   0   0    00:00:00:08
dc02.1122.f9ca   702   port-28    0   0   0   0  -    0   0   0    00:00:00:08
e01c.1122.ecc3   702   port-28    0   0   0   0  -    0   0   0    00:11:24:00"""
        elif "show mac dynamic port" in command:
            self._output = b""" Total MAC Address : 1

 Flags: Per - permanent, Stc - static, ToP - to_permanent, ToS - to_static,
        Sav - auto saved mac address, SrF - source filter,
        DsF - destination filter, Time - day:hour:min:sec,
        Frm - mac from where:0,LEARN; 1,CONFIG; 2,DUPLICATE; 3,VPN; 4,802.1X;
                             5,LAYER-3; 6,DHCP

  MAC-Address  Vlan-Id   Port    Per Stc ToP ToS Sav SrF DsF Frm      Time
-------------------------------------------------------------------------------
c46e.1122.1b21   702   port-1     0   0   0   0  -    0   0   0    01:00:26:57
"""
        elif "show vct port 1" in command:
            self._output = b"""
Cable Test Result for Port 1
RX PAIR :
  Cable Test Passed. No problem found.
  Cable Length is 0(unknown).
TX PAIR :
  Cable Test Passed. No problem found.
  Cable Length is 0(unknown)."""
        elif "show vct port 2" in command:
            self._output = b"""
Cable Test Result for Port 4
RX PAIR :
  Cable Test Passed. Cable is open.
  Approximately 43 meters from the tested port.
TX PAIR :
  Cable Test Passed. Cable is open.
  Approximately 42 meters from the tested port."""


class TestZTE2928E(SimpleTestCase):
    def setUp(self) -> None:
        self.device = ZTE(
            session=FakeZTE2928ESession(),
            ip="10.10.10.10",
            snmp_community="",
            auth={
                "login": "user",
                "password": "passwd",
                "privilege_mode_password": "secret",
            },
        )

    def test_get_mac_table(self):
        res = self.device.get_mac_table()
        self.assertListEqual(
            res,
            [
                (702, "8416.1122.bcff", "dynamic", "1"),
                (1052, "dc2c.1122.f457", "dynamic", "28"),
                (702, "0021.1122.386c", "dynamic", "28"),
                (702, "dc02.1122.f9ca", "dynamic", "28"),
                (702, "e01c.1122.ecc3", "dynamic", "28"),
            ],
        )

    def test_get_mac(self):
        res = self.device.get_mac("1")
        self.assertListEqual(res, [(702, "c46e.1122.1b21")])

    def test_cable_diag(self):
        res = self.device.virtual_cable_test("1")
        self.assertDictEqual(
            res,
            {"len": "-", "status": "Up"},
        )

        res = self.device.virtual_cable_test("2")
        self.assertDictEqual(
            res,
            {
                "len": "-",
                "status": "Open",
                "pair1": {"status": "open", "len": "43"},
                "pair2": {"status": "open", "len": "42"},
            },
        )
