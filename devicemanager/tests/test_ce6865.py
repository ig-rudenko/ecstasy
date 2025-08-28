from typing import ClassVar  # noqa: F401
from unittest.mock import Mock, patch

from django.test import TestCase

from devicemanager.vendors.base.helpers import parse_by_template
from devicemanager.vendors.huawei.ce6865 import HuaweiCE6865
from .test_huawei import TestHuaweiS2326TPFactory

dis_int_desc_output = """
PHY: Physical
*down: administratively down
^down: standby
(l): loopback
(s): spoofing
(b): BFD down
(e): ETHOAM down
(d): Dampening Suppressed
(p): port alarm down
(dl): DLDP down
(c): CFM down
(ed): error down
Interface                     PHY     Protocol Description
25GE1/0/1                     up      up       Desc1
25GE1/0/1.105                 up      up       Desc2
25GE1/0/1.106                 up      up       Desc3-long-long-long-long
25GE1/0/2                     *down   down
25GE1/0/3.101                 ^down   ^down
25GE1/0/3.102                 ^down   down
25GE1/0/3.103                 down    down
25GE1/0/3.104                 down    down
25GE1/0/3.200                 up(s)   up       Device2:Gi2/0/9
25GE1/0/4                     up(dl)  up
25GE1/0/5                     up      up
25GE1/0/6                     up      up
25GE1/0/7                     up      up
25GE1/0/8                     up      up
100GE1/0/6                    up      up       This:25GE1/0/3
100GE1/0/7                    up      down     This:25GE1/0/2
Loop0                         up      up(s)
MEth0/0/0                     up      up
NULL0                         up      up(s)
Nve1                          up      up
Vbdif1004                     up      up
Vbdif1005                     up      up
Vbdif14010                    up      up
Vlanif300                     up      up
Vlanif301                     down    down
Vlanif3995                    up      up
"""
dis_cur_inter_output = """#
interface 25GE1/0/1
 port link-type hybrid
 port hybrid pvid vlan 200
 port hybrid tagged vlan 101 to 104 300
 port hybrid untagged vlan 200
 port vlan-stacking vlan 100 stack-vlan 200
 jumboframe enable 9210
 device transceiver 10GBASE-COPPER
 port mode 10G
#
interface 25GE1/0/1.105 mode l2
 encapsulation dot1q vid 105
 bridge-domain 1005
#
interface 25GE1/0/1.106 mode l2
 encapsulation qinq vid 106 ce-vid 500
 bridge-domain 1006
#
interface 25GE1/0/2
 port link-type trunk
 undo port trunk allow-pass vlan 1
 port trunk allow-pass vlan 1 to 4 8 101 to 104 200
 jumboframe enable 9210
 device transceiver 10GBASE-COPPER
 port mode 10G
#
interface 25GE1/0/3
 undo portswitch
 mtu 9600
 jumboframe enable 9210
 device transceiver 10GBASE-COPPER
 port mode 10G
#
interface 25GE1/0/3.101 mode l2
 encapsulation dot1q vid 101
 bridge-domain 1002
#
interface 25GE1/0/3.102 mode l2
 encapsulation dot1q vid 102
 bridge-domain 1001
#
interface 25GE1/0/3.103 mode l2
 encapsulation qinq vid 103 ce-vid 801
 bridge-domain 1003
#
interface 25GE1/0/3.104 mode l2
 encapsulation dot1q vid 104
 bridge-domain 1004
#
interface 25GE1/0/3.200 mode l2
 encapsulation dot1q vid 200
 bridge-domain 1000
#
interface 25GE1/0/4
 undo portswitch
 device transceiver 10GBASE-FIBER
 port mode 10G
#
interface 25GE1/0/5
 port link-type trunk
 undo port trunk allow-pass vlan 1
 port trunk allow-pass vlan 3995
 device transceiver 10GBASE-FIBER
 port mode 10G
#
interface 25GE1/0/6
 description AGG2:Port26
 port link-type trunk
 undo port trunk allow-pass vlan 1
 port trunk allow-pass vlan 3995
 device transceiver 10GBASE-FIBER
 port mode 10G
#
interface 25GE1/0/7
 port mode 10G
#
interface 25GE1/0/8
 port mode 10G
#
interface 100GE1/0/6
 port default vlan 6
#
interface 100GE1/0/7
 port default vlan 7
 device transceiver 100GBASE-FIBER
#"""


class TestCE6865HuaweiFactory(TestHuaweiS2326TPFactory):
    @staticmethod
    def get_device_class():
        return HuaweiCE6865

    @staticmethod
    def get_output_from_display_version_command():
        """
        HuaweiFactory вызывает еще одну команду `display version`, перехватываем её и возвращаем
        данную строку для `CE6865`
        """
        return """
Huawei Versatile Routing Platform Software
VRP (R) software, Version 8.220 (CE6865EI V200R022C00SPC500)
Copyright (C) 2012-2022 Huawei Technologies Co., Ltd.
HUAWEI CE6865-48S8CQ-EI uptime is 70 days, 0 hour, 3 minutes"""


class TestCE6865Template(TestCase):
    def test_interfaces_find_template(self):
        parse_data = parse_by_template("interfaces/huawei-ce6865.template", dis_int_desc_output)
        self.assertListEqual(
            [
                ["25GE1/0/1", "up", "up", "Desc1"],
                ["25GE1/0/1.105", "up", "up", "Desc2"],
                ["25GE1/0/1.106", "up", "up", "Desc3-long-long-long-long"],
                ["25GE1/0/2", "*down", "down", ""],
                ["25GE1/0/3.101", "^down", "^down", ""],
                ["25GE1/0/3.102", "^down", "down", ""],
                ["25GE1/0/3.103", "down", "down", ""],
                ["25GE1/0/3.104", "down", "down", ""],
                ["25GE1/0/3.200", "up(s)", "up", "Device2:Gi2/0/9"],
                ["25GE1/0/4", "up(dl)", "up", ""],
                ["25GE1/0/5", "up", "up", ""],
                ["25GE1/0/6", "up", "up", ""],
                ["25GE1/0/7", "up", "up", ""],
                ["25GE1/0/8", "up", "up", ""],
                ["100GE1/0/6", "up", "up", "This:25GE1/0/3"],
                ["100GE1/0/7", "up", "down", "This:25GE1/0/2"],
            ],
            parse_data,
        )

    def test_vlans_find_template(self):
        parse_data = parse_by_template("vlans_templates/huawei-ce6865.template", dis_cur_inter_output)

        self.assertListEqual(
            [
                ["25GE1/0/1", "200"],
                ["25GE1/0/1.105", "105"],
                ["25GE1/0/1.106", "500"],
                ["25GE1/0/2", "1 to 4 8 101 to 104 200"],
                ["25GE1/0/3", ""],
                ["25GE1/0/3.101", "101"],
                ["25GE1/0/3.102", "102"],
                ["25GE1/0/3.103", "801"],
                ["25GE1/0/3.104", "104"],
                ["25GE1/0/3.200", "200"],
                ["25GE1/0/4", ""],
                ["25GE1/0/5", "3995"],
                ["25GE1/0/6", "3995"],
                ["25GE1/0/7", ""],
                ["25GE1/0/8", ""],
                ["100GE1/0/6", "6"],
                ["100GE1/0/7", "7"],
            ],
            parse_data,
        )


class HuaweiCE6865PexpectFaker:
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

        if "display device elabel" in command:
            self.before = b"""
BarCode=000000000000
BarCode=oud129388939
BarCode=kojaisoid9h9
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


class TestCE6865Methods(TestCase):
    device = None  # type: ClassVar[HuaweiCE6865]
    display_mac_address_output = None  # type: ClassVar[str]
    display_mac_address_port_output = None  # type: ClassVar[str]
    display_interface_errors_output = None  # type: ClassVar[str]
    display_interface_output = None  # type: ClassVar[str]
    valid_interfaces_list = None  # type: ClassVar[list]
    valid_vlans_list = None  # type: ClassVar[list]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.device = HuaweiCE6865(
            session=HuaweiCE6865PexpectFaker(),
            ip="",
            auth={
                "login": "login",
                "password": "password",
                "privilege_mode_password": "privilege_mode_password",
            },
        )
        cls.display_mac_address_output = """
# display mac-address
Flags: * - Backup
       # - forwarding logical interface, operations cannot be performed based
           on the interface.
BD   : bridge-domain   Age : dynamic MAC learned time in seconds
-------------------------------------------------------------------------------
MAC Address    VLAN/VSI/BD   Learned-From        Type                Age
-------------------------------------------------------------------------------
3aad-b223-d191 104/-/-       25GE1/0/2           dynamic                247
5aa0-b220-729f 104/-/-       25GE1/0/2           dynamic                 51
8aad-b22b-b194 104/-/-       25GE1/0/1           dynamic                144
8aad-b22b-b194 300/-/-       25GE1/0/1           dynamic                363
0aab-b226-0791 3995/-/-      25GE1/0/6           dynamic            1821961
0aa3-b22b-5f91 3995/-/-      25GE1/0/5           dynamic            1561821
0aab-b226-0791 -/bbn3991/13991 25GE1/0/6.3991      dynamic            2733593"""
        cls.display_mac_address_port_output = """
# display mac-address
Flags: * - Backup
       # - forwarding logical interface, operations cannot be performed based
           on the interface.
BD   : bridge-domain   Age : dynamic MAC learned time in seconds
-------------------------------------------------------------------------------
MAC Address    VLAN/VSI/BD   Learned-From        Type                Age
-------------------------------------------------------------------------------
3aad-b223-d191 104/-/-       25GE1/0/1           dynamic                247
5aa0-b220-729f 104/-/-       25GE1/0/1           dynamic                 51
8aad-b22b-b194 104/-/-       25GE1/0/1           dynamic                144
8aad-b22b-b194 300/-/-       25GE1/0/1           dynamic                363"""
        cls.display_interface_errors_output = "CRC: 123\nErrors: 0"
        cls.display_interface_output = f"some data\n{cls.display_interface_errors_output}\nnext data"
        cls.valid_interfaces_list = [
            ("25GE1/0/1", "up", "Desc1"),
            ("25GE1/0/1.105", "up", "Desc2"),
            ("25GE1/0/1.106", "up", "Desc3-long-long-long-long"),
            ("25GE1/0/2", "admin down", ""),
            ("25GE1/0/3.101", "down", ""),
            ("25GE1/0/3.102", "down", ""),
            ("25GE1/0/3.103", "down", ""),
            ("25GE1/0/3.104", "down", ""),
            ("25GE1/0/3.200", "up", "Device2:Gi2/0/9"),
            ("25GE1/0/4", "up", ""),
            ("25GE1/0/5", "up", ""),
            ("25GE1/0/6", "up", ""),
            ("25GE1/0/7", "up", ""),
            ("25GE1/0/8", "up", ""),
            ("100GE1/0/6", "up", "This:25GE1/0/3"),
            ("100GE1/0/7", "down", "This:25GE1/0/2"),
        ]
        cls.valid_vlans_list = [
            ("25GE1/0/1", "up", "Desc1", [200]),
            ("25GE1/0/1.105", "up", "Desc2", [105]),
            ("25GE1/0/1.106", "up", "Desc3-long-long-long-long", [500]),
            ("25GE1/0/2", "admin down", "", [1, 2, 3, 4, 8, 101, 102, 103, 104, 200]),
            ("25GE1/0/3.101", "down", "", [101]),
            ("25GE1/0/3.102", "down", "", [102]),
            ("25GE1/0/3.103", "down", "", [801]),
            ("25GE1/0/3.104", "down", "", [104]),
            ("25GE1/0/3.200", "up", "Device2:Gi2/0/9", [200]),
            ("25GE1/0/4", "up", "", []),
            ("25GE1/0/5", "up", "", [3995]),
            ("25GE1/0/6", "up", "", [3995]),
            ("25GE1/0/7", "up", "", []),
            ("25GE1/0/8", "up", "", []),
            ("100GE1/0/6", "up", "This:25GE1/0/3", [6]),
            ("100GE1/0/7", "down", "This:25GE1/0/2", [7]),
        ]

    @patch("devicemanager.vendors.huawei.ce6865.HuaweiCE6865.send_command")
    def test_get_interfaces_method(self, send_command: Mock):
        send_command.return_value = dis_int_desc_output

        result = self.device.get_interfaces()
        self.assertListEqual(result, self.valid_interfaces_list)

    @patch("devicemanager.vendors.huawei.ce6865.HuaweiCE6865.send_command")
    @patch("devicemanager.vendors.huawei.ce6865.HuaweiCE6865.get_interfaces")
    def test_get_vlans_method(self, get_interfaces: Mock, send_command: Mock):
        get_interfaces.return_value = self.valid_interfaces_list
        send_command.return_value = dis_cur_inter_output

        result = self.device.get_vlans()
        print(result)
        self.assertListEqual(result, self.valid_vlans_list)

    @patch("devicemanager.vendors.huawei.ce6865.HuaweiCE6865.send_command")
    def test_get_mac_table_method(self, send_command: Mock):
        send_command.return_value = self.display_mac_address_output

        result = self.device.get_mac_table()

        self.assertListEqual(
            result,
            [
                (104, "3aad-b223-d191", "dynamic", "25GE1/0/2"),
                (104, "5aa0-b220-729f", "dynamic", "25GE1/0/2"),
                (104, "8aad-b22b-b194", "dynamic", "25GE1/0/1"),
                (300, "8aad-b22b-b194", "dynamic", "25GE1/0/1"),
                (3995, "0aab-b226-0791", "dynamic", "25GE1/0/6"),
                (3995, "0aa3-b22b-5f91", "dynamic", "25GE1/0/5"),
            ],
        )

    @patch("devicemanager.vendors.huawei.ce6865.HuaweiCE6865.send_command")
    def test_get_mac_method(self, send_command: Mock):
        send_command.return_value = self.display_mac_address_port_output

        result = self.device.get_mac(port="25GE1/0/1")

        self.assertListEqual(
            result,
            [
                (104, "3aad-b223-d191"),
                (104, "5aa0-b220-729f"),
                (104, "8aad-b22b-b194"),
                (300, "8aad-b22b-b194"),
            ],
        )

    def test_get_port_type_method(self):
        self.assertEqual(self.device.get_port_type(port="25GE1/0/1"), "SFP")

    @patch("devicemanager.vendors.huawei.ce6865.HuaweiCE6865.send_command")
    def test_get_port_info_method_valid_port(self, send_command: Mock):
        send_command.return_value = self.display_interface_output

        self.assertEqual(
            self.device.get_port_info(port="25GE1/0/1"),
            {
                "type": "text",
                "data": self.display_interface_output,
            },
        )

    @patch("devicemanager.vendors.huawei.ce6865.HuaweiCE6865.send_command")
    def test_get_port_info_method_invalid_port(self, send_command: Mock):
        send_command.return_value = self.display_interface_output

        self.assertEqual(
            self.device.get_port_info(port="dsfas"),
            {
                "type": "error",
                "data": "Неверный порт",
            },
        )

    @patch("devicemanager.vendors.huawei.ce6865.HuaweiCE6865.send_command")
    def test_get_port_errors_method_valid_port(self, send_command: Mock):
        send_command.return_value = self.display_interface_output

        self.assertEqual(
            self.device.get_port_errors(port="25GE1/0/1"),
            self.display_interface_errors_output,
        )

    @patch("devicemanager.vendors.huawei.ce6865.HuaweiCE6865.send_command")
    def test_get_port_errors_method_invalid_port(self, send_command: Mock):
        send_command.return_value = self.display_interface_output

        self.assertEqual(self.device.get_port_errors(port="dsfas"), "Неверный порт")
