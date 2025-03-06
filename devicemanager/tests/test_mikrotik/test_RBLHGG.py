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
        board-name: LHG 60G
             model: RBLHGG-60ad
          revision: r2
     serial-number: CF340D742322
     firmware-type: ipq4000L
  factory-firmware: 6.45.9
  current-firmware: 6.45.9
  upgrade-firmware: 6.45.9"""

        elif "interface vlan print detail terse" in command:
            self.before = b""" 0 R name=vlan1944 mtu=1500 l2mtu=1594 mac-address=08:55:31:85:7D:30 arp=enabled arp-timeout=auto loop-protect=default loop-protect-status=off loop-protect-send-interval=5s loop-protect-disable-time=5m vlan-id=1944 interface=T_bridge use-service-tag=no
 1 R name=vlan3738 mtu=1500 l2mtu=1594 mac-address=08:55:31:85:7D:30 arp=enabled arp-timeout=auto loop-protect=default loop-protect-status=off loop-protect-send-interval=5s loop-protect-disable-time=5m vlan-id=3738 interface=T_bridge use-service-tag=no"""

        elif "interface bridge port print terse" in command:
            self.before = b""" 0   H interface=ether1 bridge=T_bridge priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none hw=yes auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
 1     interface=vlan3738 bridge=bridge3738 priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=none auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no
 2  D  comment=wlan60-1 interface=wlan60-station-1 bridge=T_bridge priority=0x80 path-cost=10 internal-path-cost=10 edge=auto point-to-point=auto learn=auto horizon=1 auto-isolate=no restricted-role=no restricted-tcn=no pvid=1 frame-types=admit-all ingress-filtering=no unknown-unicast-flood=yes unknown-multicast-flood=yes broadcast-flood=yes tag-stacking=no bpdu-guard=no trusted=no multicast-router=temporary-query fast-leave=no"""

        elif "interface print without-paging terse" in command:
            self.before = b""" 0  RS name=ether1 default-name=ether1 type=ether mtu=1500 actual-mtu=1500 l2mtu=1598 max-l2mtu=9214 mac-address=08:55:31:85:7D:30 last-link-up-time=dec/19/2023 12:58:56 link-downs=0
 1     name=wlan60-1 type=wlan60- mtu=1500 actual-mtu=1500 l2mtu=1600 max-l2mtu=7882 mac-address=08:55:31:85:7D:31 link-downs=0
 2  R  name=T_bridge type=bridge mtu=auto actual-mtu=1500 l2mtu=1598 mac-address=08:55:31:85:7D:30 last-link-up-time=dec/19/2023 12:56:29 link-downs=0
 3  R  name=bridge3738 type=bridge mtu=auto actual-mtu=1500 l2mtu=65531 mac-address=08:55:31:85:7D:30 last-link-up-time=dec/19/2023 12:56:29 link-downs=0
 4  R  name=vlan1944 type=vlan mtu=1500 actual-mtu=1500 l2mtu=1594 mac-address=08:55:31:85:7D:30 last-link-up-time=dec/19/2023 12:56:29 link-downs=0
 5  RS name=vlan3738 type=vlan mtu=1500 actual-mtu=1500 l2mtu=1594 mac-address=08:55:31:85:7D:30 last-link-up-time=dec/19/2023 12:56:29 link-downs=0
 6  RS name=wlan60-station-1 type=wlan60-station- mtu=1500 actual-mtu=1500 l2mtu=1600 mac-address=08:55:31:85:7D:31 last-link-down-time=dec/21/2023 08:11:10 last-link-up-time=dec/21/2023 21:57:31 link-downs=2"""

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
        self.assertEqual(self.mikrotik.model, "RBLHGG-60ad")

    def test_vlans_and_bridges_parsing(self):
        self.assertDictEqual(self.mikrotik._vlans_interfaces, {"vlan1944": "1944", "vlan3738": "3738"})
        self.assertDictEqual(
            self.mikrotik._bridges,
            {
                "T_bridge": {"vlans": ["1944", "3738"]},
                "bridge3738": {"vlans": ["3738"]},
            },
        )
        self.assertDictEqual(
            self.mikrotik._ether_interfaces,
            {
                "ether1": {"bridge": "T_bridge"},
                "wlan60-station-1": {"bridge": "T_bridge"},
            },
        )

    def test_get_interfaces(self):
        # print(f"{self.mikrotik.get_interfaces()=}")
        # print(f"{self.mikrotik._vlans_interfaces=}")
        # print(f"{self.mikrotik._bridges=}")
        # print(f"{self.mikrotik._ether_interfaces=}")
        # print(f"{self.mikrotik.get_vlans()=}")
        self.assertListEqual(
            self.mikrotik.get_interfaces(),
            [
                ("ether1", "up", ""),
                ("wlan60-1", "down", ""),
                ("wlan60-station-1", "up", ""),
            ],
        )

    def test_get_vlans(self):
        self.assertListEqual(
            self.mikrotik.get_vlans(),
            [
                ("ether1", "up", "", ["1944", "3738"]),
                ("wlan60-1", "down", "", []),
                ("wlan60-station-1", "up", "", ["1944", "3738"]),
            ],
        )
