from django import test

from devicemanager.vendors.base.helpers import parse_by_template


class TestCE6865Template(test.TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.dis_int_desc_output = """
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
100GE1/0/1                    up      up       Desc1
100GE1/0/2                    up      up       Desc2
100GE1/0/3                    up      up       Desc3-long-long-long-long
100GE1/0/4                    *down   down
100GE1/0/5                    ^down   ^down
100GE1/0/6                    ^down   down
100GE1/0/7                    down    down
100GE1/0/8                    down    down
25GE1/0/1                     up(s)   up       Device2:Gi2/0/9
25GE1/0/1.105                 up      up
25GE1/0/1.106                 up(dl)  up
25GE1/0/2                     up      up       This:25GE1/0/3
25GE1/0/3                     up      down     This:25GE1/0/2
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
        cls.dis_cur_inter_output = """
        #
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
 port default vlan 7
#
interface 100GE1/0/7
 port default vlan 8
 device transceiver 100GBASE-FIBER
#"""

    def test_interfaces_find_template(self):
        parse_data = parse_by_template(
            "interfaces/huawei-ce6865.template", self.dis_int_desc_output
        )
        self.assertListEqual(
            [
                ["100GE1/0/1", "up", "up", "Desc1"],
                ["100GE1/0/2", "up", "up", "Desc2"],
                ["100GE1/0/3", "up", "up", "Desc3-long-long-long-long"],
                ["100GE1/0/4", "*down", "down", ""],
                ["100GE1/0/5", "^down", "^down", ""],
                ["100GE1/0/6", "^down", "down", ""],
                ["100GE1/0/7", "down", "down", ""],
                ["100GE1/0/8", "down", "down", ""],
                ["25GE1/0/1", "up(s)", "up", "Device2:Gi2/0/9"],
                ["25GE1/0/1.105", "up", "up", ""],
                ["25GE1/0/1.106", "up(dl)", "up", ""],
                ["25GE1/0/2", "up", "up", "This:25GE1/0/3"],
                ["25GE1/0/3", "up", "down", "This:25GE1/0/2"],
            ],
            parse_data,
        )

    def test_vlans_find_template(self):
        parse_data = parse_by_template(
            f"vlans_templates/huawei-ce6865.template", self.dis_cur_inter_output
        )

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
                ["100GE1/0/6", "7"],
                ["100GE1/0/7", "8"],
            ],
            parse_data,
        )
