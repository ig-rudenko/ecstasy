from devicemanager.device import DeviceManager
from .base import TestRingBase
from ..models import TransportRing
from ..ring_manager import TransportRingManager, RingStatusError


TEST_DEVICES = [
    {
        "ip": "224.0.2.1",
        "name": "ring-dev41",
        "interfaces_vlans": [
            {
                "Interface": "GE0/1/3",
                "Status": "up",  # ================= TO DEV3 - UP
                "Description": "desc3_to_ring-dev43",
                "VLAN's": ["1-4", "30 to 32"],
            },
            {
                "Interface": "GE0/1/4",
                "Status": "up",  # ================== TO DEV2 - UP
                "Description": "desc4_to_ring-dev42",
                "VLAN's": ["1-4", "30 to 32"],
            },
        ],
    },
    {
        "ip": "224.0.2.2",
        "name": "ring-dev42",
        "interfaces": [
            {
                "Interface": "GE0/2/3",
                "Status": "up",  # ================== TO DEV1 - UP
                "Description": "desc3_to_ring-dev41",
            },
            {
                "Interface": "GE0/2/4",
                "Status": "up",  # ================== TO DEV3 - UP
                "Description": "desc4_to_ring-dev43",
            },
        ],
    },
    {
        "ip": "224.0.2.3",
        "name": "ring-dev43",
        "interfaces": [
            {
                "Interface": "GE0/3/3",
                "Status": "up",  # ================== TO DEV2 - UP
                "Description": "desc3_to_ring-dev42",
            },
            {
                "Interface": "GE0/3/4",
                "Status": "up",  # ================== TO DEV4 - UP
                "Description": "desc4_to_ring-dev44",
            },
        ],
    },
    {
        "ip": "224.0.2.4",
        "name": "ring-dev44",
        "interfaces_vlans": [
            {
                "Interface": "GE0/4/3",
                "Status": "up",  # ================ TO DEV3 - UP
                "Description": "desc3_to_ring-dev43",
                "VLAN's": ["4", "30 to 32"],
            },
            {
                "Interface": "GE0/4/4",
                "Status": "up",  # ================ TO DEV1 - UP
                "Description": "desc4_to_ring-dev41",
                "VLAN's": ["4", "30 to 32"],
            },
        ],
    },
]


class TestHeadDownSolutions(TestRingBase):
    TEST_DEVICES = TEST_DEVICES
    ring_name = "ring21"

    def test_head_down_solutions(self):
        class TestTransportRingManager(TransportRingManager):
            device_manager = DeviceManager

        r = TestTransportRingManager(ring=TransportRing.objects.get(name=self.ring_name))
        r.collect_all_interfaces()
        r.find_link_between_devices()

        # Все оборудование доступно
        for d in r.ring_devs:
            d.ping = True

        # Кроме `head`
        r.ring_devs[0].ping = False

        with self.assertRaises(RingStatusError):
            r.create_solutions()

    def test_tail_down_solutions(self):
        class TestTransportRingManager(TransportRingManager):
            device_manager = DeviceManager

        r = TestTransportRingManager(ring=TransportRing.objects.get(name=self.ring_name))
        r.collect_all_interfaces()
        r.find_link_between_devices()

        # Все оборудование доступно
        for d in r.ring_devs:
            d.ping = True

        # Кроме `tail`
        r.ring_devs[-1].ping = False

        with self.assertRaises(RingStatusError):
            r.create_solutions()

    def test_all_down_solutions(self):
        class TestTransportRingManager(TransportRingManager):
            device_manager = DeviceManager

        r = TestTransportRingManager(ring=TransportRing.objects.get(name=self.ring_name))
        r.collect_all_interfaces()
        r.find_link_between_devices()

        # Все оборудование НЕ доступно
        for d in r.ring_devs:
            d.ping = False

        with self.assertRaises(RingStatusError):
            r.create_solutions()

    def test_invalid_vlans_solutions(self):
        class TestTransportRingManager(TransportRingManager):
            device_manager = DeviceManager

        r = TestTransportRingManager(ring=TransportRing.objects.get(name=self.ring_name))
        r.collect_all_interfaces()
        r.find_link_between_devices()

        # Все оборудование доступно
        for d in r.ring_devs:
            d.ping = True

        # VLAN, которые требуются для разворота отсутствуют на `head`
        r.ring_devs[0].port_to_next_dev.vlan = [1000, 1001]

        with self.assertRaises(RingStatusError):
            r.create_solutions()
