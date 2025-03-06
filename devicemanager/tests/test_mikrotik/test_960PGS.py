from django.test import SimpleTestCase

from devicemanager.vendors import MikroTik


class FakeMikrotikRBLHGGSession:
    def __init__(self):
        self.before = b""
        self.commands = []

    def sendline(self, command: str, *args, **kwargs):
        return self.send(command, *args, **kwargs)

    def send(self, command: str, *args, **kwargs):
        self.commands.append(command)

        if "system routerboard print" in command:
            self.before = b"""       routerboard: yes
        board-name: PowerBox Pro
             model: 960PGS
     serial-number: 8A3108D4CAE0
     firmware-type: qca9550L
  factory-firmware: 3.41
  current-firmware: 6.47.8
  upgrade-firmware: 6.47.8"""

        elif "interface vlan print detail terse" in command:
            self.before = b""" 0 R name=vlan1051 mtu=1500 l2mtu=1596 mac-address=CC:2D:E0:48:97:B8 arp=enabled arp-timeout=auto loop-protect=default loop-protect-status=off loop-protect-send-interval=5s loop-protect-disable-time=5m vlan-id=1051 interface=T_bridge use-service-tag=no
 1 R name=vlan3738 mtu=1500 l2mtu=1596 mac-address=CC:2D:E0:48:97:B8 arp=enabled arp-timeout=auto loop-protect=default loop-protect-status=off loop-protect-send-interval=5s loop-protect-disable-time=5m vlan-id=3738 interface=T_bridge use-service-tag=no"""

        elif "interface bridge port print terse" in command:
            self.before = b""" 0     interface=sfp1 bridge=T_bridge priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none hw=no auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
 1     interface=ether1 bridge=bridge3738 priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none hw=no auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
 2     interface=ether2 bridge=bridge3738 priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none hw=no auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=yes multicast-router=temporary-query fast-leave=no
 3     interface=ether3 bridge=bridge3738 priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none hw=no auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
 4     interface=ether4 bridge=bridge3738 priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none hw=no auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
 5     interface=ether5 bridge=bridge3738 priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none hw=no auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
 6     interface=vlan3738 bridge=bridge3738 priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
 7     interface=vlan1051 bridge=bridge1051 priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no"""

        elif "interface print without-paging terse" in command:
            self.before = b""" 0  RS comment=Camera_4 name=ether1 default-name=ether1 type=ether mtu=1500 actual-mtu=1500 l2mtu=1598 max-l2mtu=4074 mac-address=CC:2D:E0:48:97:B3 last-link-down-time=oct/26/2023 09:33:01 last-link-up-time=oct/26/2023 09:33:11 link-downs=2
 1  RS comment=Camera_1 name=ether2 default-name=ether2 type=ether mtu=1500 actual-mtu=1500 l2mtu=1598 max-l2mtu=4074 mac-address=CC:2D:E0:48:97:B4 last-link-down-time=oct/26/2023 08:49:49 last-link-up-time=oct/26/2023 08:49:58 link-downs=1
 2  RS comment=Camera_3 name=ether3 default-name=ether3 type=ether mtu=1500 actual-mtu=1500 l2mtu=1598 max-l2mtu=4074 mac-address=CC:2D:E0:48:97:B5 last-link-down-time=oct/26/2023 09:17:21 last-link-up-time=oct/26/2023 09:17:31 link-downs=1
 3  RS comment=Camera_2 name=ether4 default-name=ether4 type=ether mtu=1500 actual-mtu=1500 l2mtu=1598 max-l2mtu=4074 mac-address=CC:2D:E0:48:97:B6 last-link-down-time=oct/27/2023 13:06:52 last-link-up-time=oct/27/2023 13:06:54 link-downs=12
 4  RS comment=Camera_5 name=ether5 default-name=ether5 type=ether mtu=1500 actual-mtu=1500 l2mtu=1598 max-l2mtu=4074 mac-address=CC:2D:E0:48:97:B7 last-link-down-time=oct/26/2023 09:19:54 last-link-up-time=oct/26/2023 09:20:03 link-downs=2
 5  RS comment=SFP_Uplink name=sfp1 default-name=sfp1 type=ether mtu=1500 actual-mtu=1500 l2mtu=1600 max-l2mtu=4076 mac-address=CC:2D:E0:48:97:B8 last-link-up-time=oct/21/2023 09:23:20 link-downs=0
 6  R  name=T_bridge type=bridge mtu=auto actual-mtu=1500 l2mtu=1600 mac-address=CC:2D:E0:48:97:B8 last-link-up-time=oct/21/2023 09:23:12 link-downs=0
 7  R  name=bridge type=bridge mtu=auto actual-mtu=1500 l2mtu=65535 mac-address=EE:8A:43:7F:EB:2A last-link-up-time=oct/21/2023 09:23:12 link-downs=0
 8  R  name=bridge1051 type=bridge mtu=auto actual-mtu=1500 l2mtu=65531 mac-address=CC:2D:E0:48:97:B8 last-link-up-time=oct/21/2023 09:23:12 link-downs=0
 9  R  name=bridge3738 type=bridge mtu=auto actual-mtu=1500 l2mtu=1598 mac-address=CC:2D:E0:48:97:B8 last-link-up-time=oct/21/2023 09:23:12 link-downs=0
10  RS name=vlan1051 type=vlan mtu=1500 actual-mtu=1500 l2mtu=1596 mac-address=CC:2D:E0:48:97:B8 last-link-up-time=oct/21/2023 09:23:12 link-downs=0
11  RS name=vlan3738 type=vlan mtu=1500 actual-mtu=1500 l2mtu=1596 mac-address=CC:2D:E0:48:97:B8 last-link-up-time=oct/21/2023 09:23:12 link-downs=0"""

        else:
            self.before = b""

    def expect(self, *args, **kwargs):
        return 0


class TestMikrotikRBLHGG(SimpleTestCase):
    def setUp(self):
        self.fake_session = FakeMikrotikRBLHGGSession()
        self.mikrotik = MikroTik(
            self.fake_session,
            "10.10.10.10",
            {
                "login": "admin",
                "password": "<PASSWORD>",
                "privilege_mode_password": "secret",
            },
        )

    def test_model_parsing(self):
        self.assertEqual(self.mikrotik.model, "960PGS")

    def test_vlans_and_bridges_parsing(self):
        self.assertDictEqual(self.mikrotik._vlans_interfaces, {"vlan1051": "1051", "vlan3738": "3738"})
        self.assertDictEqual(
            self.mikrotik._bridges,
            {
                "T_bridge": {"vlans": ["1051", "3738"]},
                "bridge3738": {"vlans": ["3738"]},
                "bridge1051": {"vlans": ["1051"]},
            },
        )
        self.assertDictEqual(
            self.mikrotik._ether_interfaces,
            {
                "sfp1": {"bridge": "T_bridge"},
                "ether1": {"bridge": "bridge3738"},
                "ether2": {"bridge": "bridge3738"},
                "ether3": {"bridge": "bridge3738"},
                "ether4": {"bridge": "bridge3738"},
                "ether5": {"bridge": "bridge3738"},
            },
        )

    def test_get_interfaces(self):
        self.assertListEqual(
            self.mikrotik.get_interfaces(),
            [
                ("ether1", "up", "Camera_4"),
                ("ether2", "up", "Camera_1"),
                ("ether3", "up", "Camera_3"),
                ("ether4", "up", "Camera_2"),
                ("ether5", "up", "Camera_5"),
                ("sfp1", "up", "SFP_Uplink"),
            ],
        )

    def test_get_vlans(self):
        self.assertListEqual(
            self.mikrotik.get_vlans(),
            [
                ("ether1", "up", "Camera_4", ["3738"]),
                ("ether2", "up", "Camera_1", ["3738"]),
                ("ether3", "up", "Camera_3", ["3738"]),
                ("ether4", "up", "Camera_2", ["3738"]),
                ("ether5", "up", "Camera_5", ["3738"]),
                ("sfp1", "up", "SFP_Uplink", ["1051", "3738"]),
            ],
        )
