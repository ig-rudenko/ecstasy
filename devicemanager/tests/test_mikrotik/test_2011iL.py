from django.test import SimpleTestCase

from devicemanager.vendors import MikroTik


class FakeMikrotik2011iLSession:
    def __init__(self):
        self.before = b""
        self.commands = []

    def sendline(self, command: str, *args, **kwargs):
        return self.send(command, *args, **kwargs)

    def send(self, command: str, *args, **kwargs):
        self.commands.append(command)

        if "system routerboard print" in command:
            self.before = b"""       routerboard: yes
             model: 2011iL
     serial-number: 607C0566A757
     firmware-type: ar9344
  factory-firmware: 3.24
  current-firmware: 3.24
  upgrade-firmware: 6.43.2"""

        elif "interface vlan print detail terse" in command:
            self.before = b""" 0 R name=VideoPZK mtu=1500 l2mtu=1594 mac-address=E4:8D:8C:7A:B5:70 arp=enabled arp-timeout=auto loop-protect=default loop-protect-status=off loop-protect-send-interval=5s loop-protect-disable-time=5m vlan-id=3738 interface=bridge1 use-service-tag=no
 1 R name=inet mtu=1500 l2mtu=1594 mac-address=E4:8D:8C:7A:B5:70 arp=enabled arp-timeout=auto loop-protect=default loop-protect-status=off loop-protect-send-interval=5s loop-protect-disable-time=5m vlan-id=1054 interface=bridge1 use-service-tag=no
 2 R name=mgmt mtu=1500 l2mtu=1594 mac-address=E4:8D:8C:7A:B5:70 arp=enabled arp-timeout=auto loop-protect=default loop-protect-status=off loop-protect-send-interval=5s loop-protect-disable-time=5m vlan-id=3989 interface=bridge1 use-service-tag=no
 3 R name=vlan818 mtu=1500 l2mtu=1594 mac-address=E4:8D:8C:7A:B5:70 arp=enabled arp-timeout=auto loop-protect=default loop-protect-status=off loop-protect-send-interval=5s loop-protect-disable-time=5m vlan-id=818 interface=bridge1 use-service-tag=no
 4 R comment=Miranda_Rakushka name=vlan1233 mtu=1500 l2mtu=1594 mac-address=E4:8D:8C:7A:B5:70 arp=enabled arp-timeout=auto loop-protect=default loop-protect-status=off loop-protect-send-interval=5s loop-protect-disable-time=5m vlan-id=1233 interface=bridge1 use-service-tag=no"""

        elif "interface bridge port print terse" in command:
            self.before = b""" 0     interface=inet bridge=BridgeInet priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
 1 XI   interface=mgmt bridge=BridgeMGMT priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
 2     interface=VideoPZK bridge=BridgeVideoPZK priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
 3     interface=ether6_to_CAM_PZK bridge=BridgeVideoPZK priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none hw=no auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
 4 I   interface=ether7 bridge=BridgeInet priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none hw=no auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
 5 I H interface=ether8_to_pzk5ghz bridge=bridge1 priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none hw=yes auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
 6 I H interface=ether9 bridge=bridge1 priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none hw=yes auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
 7 I H interface=ether10 bridge=bridge1 priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none hw=yes auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
 8 I   interface=*14 bridge=bridgeHotSpot priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
 9     interface=ether1 bridge=bridge1 priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none hw=yes auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
10     interface=ether3 bridge=bridge1 priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none hw=yes auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
11 I   interface=ether4 bridge=bridge1233 priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none hw=yes auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
12     interface=vlan1233 bridge=bridge1233 priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
13 I   interface=ether5 bridge=BridgeVideoPZK priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none hw=yes auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
14 I H interface=ether2 bridge=BridgeInet priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none hw=yes auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no"""

        elif "interface print without-paging terse" in command:
            self.before = b""" 0  RS comment=Uplink name=ether1 default-name=ether1 type=ether mtu=1500 actual-mtu=1500 l2mtu=1598 max-l2mtu=4074 mac-address=E4:8D:8C:7A:B5:70 last-link-up-time=dec/23/2023 04:22:31 link-downs=0
 1   S name=ether2 default-name=ether2 type=ether mtu=1500 actual-mtu=1500 l2mtu=1598 max-l2mtu=4074 mac-address=E4:8D:8C:7A:B5:71 link-downs=0
 2  RS comment=RB260_Rakushka name=ether3 default-name=ether3 type=ether mtu=1500 actual-mtu=1500 l2mtu=1598 max-l2mtu=4074 mac-address=E4:8D:8C:7A:B5:72 last-link-up-time=dec/23/2023 04:22:31 link-downs=0
 3  XS comment=L2VPN|Miranda| Arhipelag|1G| name=ether4 default-name=ether4 type=ether mtu=1500 actual-mtu=1500 l2mtu=1598 max-l2mtu=4074 mac-address=E4:8D:8C:7A:B5:73 link-downs=0
 4   S name=ether5 default-name=ether5 type=ether mtu=1500 actual-mtu=1500 l2mtu=1598 max-l2mtu=4074 mac-address=E4:8D:8C:7A:B5:74 link-downs=0
 5  RS comment=CAM_PZK name=ether6_to_CAM_PZK default-name=ether6 type=ether mtu=1500 actual-mtu=1500 l2mtu=1598 max-l2mtu=2028 mac-address=E4:8D:8C:7A:B5:75 last-link-down-time=dec/26/2023 13:37:32 last-link-up-time=dec/26/2023 13:43:05 link-downs=7
 6   S name=ether7 default-name=ether7 type=ether mtu=1500 actual-mtu=1500 l2mtu=1598 max-l2mtu=2028 mac-address=E4:8D:8C:7A:B5:76 link-downs=0
 7   S name=ether8_to_pzk5ghz default-name=ether8 type=ether mtu=1500 actual-mtu=1500 l2mtu=1598 max-l2mtu=2028 mac-address=E4:8D:8C:7A:B5:77 link-downs=0
 8  XS comment=SHater name=ether9 default-name=ether9 type=ether mtu=1500 actual-mtu=1500 l2mtu=1598 max-l2mtu=2028 mac-address=E4:8D:8C:7A:B5:78 link-downs=0
 9   S name=ether10 default-name=ether10 type=ether mtu=1500 actual-mtu=1500 l2mtu=1598 max-l2mtu=2028 mac-address=E4:8D:8C:7A:B5:79 link-downs=0
10  R  name=BridgeInet type=bridge mtu=auto actual-mtu=1500 l2mtu=1598 mac-address=6C:3B:6B:28:63:8E last-link-up-time=dec/23/2023 04:22:24 link-downs=0
11  R  name=BridgeMGMT type=bridge mtu=auto actual-mtu=1500 l2mtu=65535 mac-address=1A:B4:A0:E8:C7:78 last-link-up-time=dec/23/2023 04:22:24 link-downs=0
12  R  name=BridgeVideoPZK type=bridge mtu=auto actual-mtu=1500 l2mtu=1598 mac-address=E4:8D:8C:7A:B5:70 last-link-up-time=dec/23/2023 04:22:24 link-downs=0
13  RS name=VideoPZK type=vlan mtu=1500 actual-mtu=1500 l2mtu=1594 mac-address=E4:8D:8C:7A:B5:70 last-link-up-time=dec/23/2023 04:22:24 link-downs=0
14  R  name=bridge1 type=bridge mtu=auto actual-mtu=1500 l2mtu=1598 mac-address=E4:8D:8C:7A:B5:70 last-link-up-time=dec/23/2023 04:22:24 link-downs=0
15  R  comment=Miranda_Rakushka name=bridge1233 type=bridge mtu=auto actual-mtu=1500 l2mtu=1598 mac-address=E4:8D:8C:7A:B5:70 last-link-up-time=dec/23/2023 04:22:24 link-downs=0
16  X  name=bridgeHotSpot type=bridge mtu=auto mac-address=62:C3:74:1B:81:03 link-downs=0
17  R  name=bridgeLocal type=bridge mtu=auto actual-mtu=1500 l2mtu=65535 mac-address=8A:FE:DC:5E:1F:BE last-link-up-time=dec/23/2023 04:22:24 link-downs=0
18  RS name=inet type=vlan mtu=1500 actual-mtu=1500 l2mtu=1594 mac-address=E4:8D:8C:7A:B5:70 last-link-up-time=dec/23/2023 04:22:24 link-downs=0
19  R  name=mgmt type=vlan mtu=1500 actual-mtu=1500 l2mtu=1594 mac-address=E4:8D:8C:7A:B5:70 last-link-up-time=dec/23/2023 04:22:24 link-downs=0
20  R  name=vlan818 type=vlan mtu=1500 actual-mtu=1500 l2mtu=1594 mac-address=E4:8D:8C:7A:B5:70 last-link-up-time=dec/23/2023 04:22:24 link-downs=0
21  RS comment=Miranda_Rakushka name=vlan1233 type=vlan mtu=1500 actual-mtu=1500 l2mtu=1594 mac-address=E4:8D:8C:7A:B5:70 last-link-up-time=dec/23/2023 04:22:24 link-downs=0"""

        else:
            self.before = b""

    def expect(self, *args, **kwargs):
        return 0


class TestMikrotik2011iL(SimpleTestCase):
    def setUp(self):
        self.fake_session = FakeMikrotik2011iLSession()
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
        self.assertEqual(self.mikrotik.model, "2011iL")

    def test_vlans_and_bridges_parsing(self):
        self.assertDictEqual(
            self.mikrotik._vlans_interfaces,
            {"VideoPZK": "3738", "inet": "1054", "mgmt": "3989", "vlan818": "818"},
        )
        self.assertDictEqual(
            self.mikrotik._bridges,
            {
                "bridge1": {"vlans": ["3738", "1054", "3989", "818"]},
                "BridgeInet": {"vlans": ["1054"]},
                "BridgeMGMT": {"vlans": ["3989"]},
                "BridgeVideoPZK": {"vlans": ["3738"]},
            },
        )
        self.assertDictEqual(
            self.mikrotik._ether_interfaces,
            {
                "ether6_to_CAM_PZK": {"bridge": "BridgeVideoPZK"},
                "ether7": {"bridge": "BridgeInet"},
                "*14": {"bridge": "bridgeHotSpot"},
                "ether1": {"bridge": "bridge1"},
                "ether3": {"bridge": "bridge1"},
                "ether4": {"bridge": "bridge1233"},
                "vlan1233": {"bridge": "bridge1233"},
                "ether5": {"bridge": "BridgeVideoPZK"},
            },
        )

    def test_get_interfaces(self):
        self.assertListEqual(
            self.mikrotik.get_interfaces(),
            [
                ("ether1", "up", "Uplink"),
                ("ether2", "down", ""),
                ("ether3", "up", "RB260_Rakushka"),
                ("ether4", "admin down", "L2VPN|Miranda| Arhipelag|1G|"),
                ("ether5", "down", ""),
                ("ether6_to_CAM_PZK", "up", "CAM_PZK"),
                ("ether7", "down", ""),
                ("ether8_to_pzk5ghz", "down", ""),
                ("ether9", "admin down", "SHater"),
                ("ether10", "down", ""),
            ],
        )

    def test_get_vlans(self):
        self.assertListEqual(
            self.mikrotik.get_vlans(),
            [
                ("ether1", "up", "Uplink", ["3738", "1054", "3989", "818"]),
                ("ether2", "down", "", []),
                ("ether3", "up", "RB260_Rakushka", ["3738", "1054", "3989", "818"]),
                ("ether4", "admin down", "L2VPN|Miranda| Arhipelag|1G|", []),
                ("ether5", "down", "", ["3738"]),
                ("ether6_to_CAM_PZK", "up", "CAM_PZK", ["3738"]),
                ("ether7", "down", "", ["1054"]),
                ("ether8_to_pzk5ghz", "down", "", []),
                ("ether9", "admin down", "SHater", []),
                ("ether10", "down", "", []),
            ],
        )
