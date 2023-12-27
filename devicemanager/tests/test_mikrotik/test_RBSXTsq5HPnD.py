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
        board-name: SXTsq 5
             model: RBSXTsq5HPnD
     serial-number: 831508FD9FDA
     firmware-type: ar9344L
  factory-firmware: 3.41
  current-firmware: 3.41
  upgrade-firmware: 7.6"""

        elif "interface vlan print detail terse" in command:
            self.before = b"""0 R name=vlan1054 mtu=1500 l2mtu=1594 mac-address=CC:2D:E0:22:A4:84 arp=enabled arp-timeout=auto loop-protect=default loop-protect-status=off loop-protect-send-interval=5s loop-protect-disable-time=5m vlan-id=1054 interface=bridge1 use-service-tag=no
1 R name=vlan3738 mtu=1500 l2mtu=1594 mac-address=CC:2D:E0:22:A4:84 arp=enabled arp-timeout=auto loop-protect=default loop-protect-status=off loop-protect-send-interval=5s loop-protect-disable-time=5m vlan-id=3738 interface=bridge1 use-service-tag=no"""

        elif "interface bridge port print terse" in command:
            self.before = b"""0 H interface=ether1 bridge=bridge1 priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none hw=yes auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
1   interface=wlan1 bridge=bridge1 priority=0x80 path-cost=10 internal-path-cost=10 edge=no point-to-point=no learn=auto horizon=none auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
2   interface=vlan3738 bridge=bridge3738 priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no"""

        elif "interface print without-paging terse" in command:
            self.before = b"""0 RS comment=SHR01 name=ether1 default-name=ether1 type=ether mtu=1500 actual-mtu=1500 l2mtu=1598 max-l2mtu=2028 mac-address=CC:2D:E0:22:A4:84 ifname=eth0 ifindex=12 id=2 last-link-up-time=jan/09/1971 06:56:20 link-downs=0
1 RS comment=UPLINK_To_RRL_Vodohran_Slave name=wlan1 default-name=wlan1 type=wlan mtu=1500 actual-mtu=1500 l2mtu=1600 max-l2mtu=2290 mac-address=CC:2D:E0:22:A4:85 ifname=ath0 ifindex=10 id=1 last-link-down-time=jan/19/1971 15:32:33 last-link-up-time=jan/19/1971 22:18:18 link-downs=8
2 R  name=bridge1 type=bridge mtu=auto actual-mtu=1500 l2mtu=1598 mac-address=CC:2D:E0:22:A4:84 ifname=br0 ifindex=6 id=3 last-link-up-time=jan/09/1971 06:56:14 link-downs=0
3 R  name=bridge3738 type=bridge mtu=auto actual-mtu=1500 l2mtu=65531 mac-address=CC:2D:E0:22:A4:84 ifname=br1 ifindex=7 id=6 last-link-up-time=jan/09/1971 06:56:14 link-downs=0
4 R  name=vlan1054 type=vlan mtu=1500 actual-mtu=1500 l2mtu=1594 mac-address=CC:2D:E0:22:A4:84 ifname=vlan5 ifindex=9 id=5 last-link-up-time=jan/09/1971 06:56:14 link-downs=0
5 RS name=vlan3738 type=vlan mtu=1500 actual-mtu=1500 l2mtu=1594 mac-address=CC:2D:E0:22:A4:84 ifname=vlan4 ifindex=8 id=4 last-link-up-time=jan/09/1971 06:56:14 link-downs=0"""

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
        self.assertEqual(self.mikrotik.model, "RBSXTsq5HPnD")

    def test_vlans_and_bridges_parsing(self):
        self.assertDictEqual(
            self.mikrotik._vlans_interfaces, {"vlan1054": "1054", "vlan3738": "3738"}
        )
        self.assertDictEqual(
            self.mikrotik._bridges,
            {"bridge1": {"vlans": ["1054", "3738"]}, "bridge3738": {"vlans": ["3738"]}},
        )
        self.assertDictEqual(
            self.mikrotik._ether_interfaces,
            {"ether1": {"bridge": "bridge1"}, "wlan1": {"bridge": "bridge1"}},
        )

    def test_get_interfaces(self):
        self.assertListEqual(
            self.mikrotik.get_interfaces(),
            [
                ("ether1", "up", "SHR01"),
                ("wlan1", "up", "UPLINK_To_RRL_Vodohran_Slave"),
            ],
        )

    def test_get_vlans(self):
        self.assertListEqual(
            self.mikrotik.get_vlans(),
            [
                ("ether1", "up", "SHR01", ["1054", "3738"]),
                ("wlan1", "up", "UPLINK_To_RRL_Vodohran_Slave", ["1054", "3738"]),
            ],
        )
