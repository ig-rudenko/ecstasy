from django.test import SimpleTestCase

from devicemanager.vendors.extreme import Extreme

from .base_factory_test import AbstractTestFactory


class TestExtremeFactory(AbstractTestFactory):
    @staticmethod
    def get_device_class():
        return Extreme

    @staticmethod
    def get_output_from_show_version_command() -> str:
        return """Switch      : 800325-00-03 1047G-01689 Rev 3.0 BootROM: 2.0.1.0    IMG: 15.3.1.4
XGM3SB-4sf-B-1: 800443-00-03 1334G-00032 Rev 3.0
PSU-1       : EDPS-300AB A-S6 800386-00-03 1047E-41689
PSU-2       : PSSW301201A -02 800519-00-05 1342A-41955

Image   : ExtremeXOS version 15.3.1.4 v1531b4-patch1-40 by release-manager
          on Wed Jun 25 23:57:28 EDT 2014
BootROM : 2.0.1.0
Diagnostics : 5.10"""


class FakeExtremeSession:
    def __init__(self):
        self._output = b""

    @staticmethod
    def expect(*args, **kwargs):
        return 0

    @property
    def before(self):
        return self._output

    def send(self, command, *args, **kwargs):
        return self.sendline(command, *args, **kwargs)

    def sendline(self, command, *args, **kwargs):
        if command == "show ports information\n":
            self._output = b"""
Port      Flags               Link      ELSM Link Num Num  Num   Jumbo QOS     Load
                              State     /OAM UPS  STP VLAN Proto Size  profile Master
=====================================================================================
1         Emj--------fMB---x- active    - / -  0    0   15   0   9216  none
2         Emj--------fMB---x- active    - / -  0    0   10   0   9216  none
3         Emj--------fMB---x- ready     - / - 14    0   11   0   9216  none
4         Dmj--------fMB---x- ready     - / -  0    0   11   0   9216  none
5         Emj--------fMB---x- active    - / -  0    0   13   0   9216  none
=====================================================================================
> indicates Port Display Name truncated past 8 characters
Flags : a - Load Sharing Algorithm address-based, D - Port Disabled,
        e - Extreme Discovery Protocol Enabled, E - Port Enabled,
        g - Egress TOS Enabled, i - Isolation, j - Jumbo Frame Enabled,
        l - Load Sharing Enabled, m - MACLearning Enabled,
        n - Ingress TOS Enabled, o - Dot1p Replacement Enabled,
        P - Software redundant port(Primary),
        R - Software redundant port(Redundant),
        q - Background QOS Monitoring Enabled,
        s - diffserv Replacement Enabled,
        v - Vman Enabled, f - Unicast Flooding Enabled,
        M - Multicast Flooding Enabled, B - Broadcast Flooding Enabled
        L - Extreme Link Status Monitoring Enabled
        O - Ethernet OAM Enabled
        w - MACLearning Disabled with Forwarding
        b - Rx and Tx Flow Control Enabled, x - Rx Flow Control Enabled
        p - Priority Flow Control Enabled"""

        elif command == "show ports description\n":
            self._output = b"""
Port   Display String        Description String
=====  ====================  ==================================================
1                            description1
2                            description2
3                            description3
4
5                            description5
=====  ====================  =================================================="""


class TestExtreme(SimpleTestCase):
    def setUp(self) -> None:
        self.device = Extreme(
            session=FakeExtremeSession(),
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
        self.assertListEqual(
            res,
            [
                ("1", "up", "description1"),
                ("2", "up", "description2"),
                ("3", "down", "description3"),
                ("4", "admin down", ""),
                ("5", "up", "description5"),
            ],
        )
