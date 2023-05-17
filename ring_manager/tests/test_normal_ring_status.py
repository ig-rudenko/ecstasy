from devicemanager import DeviceManager
from .base import TestRingBase
from ..models import TransportRing
from ..ring_manager import TransportRingManager


TEST_DEVICES = [
    {
        "ip": "224.0.0.1",
        "name": "dev1",
        "interfaces_vlans": [
            {
                "Interface": "GE0/1/3",
                "Status": "up",  # ================= TO DEV3 - UP
                "Description": "desc3_to_dev3",
                "VLAN's": ["1-4", "30 to 32"],
            },
            {
                "Interface": "GE0/1/4",
                "Status": "up",  # ================== TO DEV2 - UP
                "Description": "desc4_to_dev2",
                "VLAN's": ["1-4", "30 to 32"],
            },
        ],
    },
    {
        "ip": "224.0.0.2",
        "name": "dev2",
        "interfaces": [
            {
                "Interface": "GE0/2/3",
                "Status": "up",  # ================== TO DEV1 - UP
                "Description": "desc3_to_dev1",
            },
            {
                "Interface": "GE0/2/4",
                "Status": "up",  # ================== TO DEV3 - UP
                "Description": "desc4_to_dev3",
            },
        ],
    },
    {
        "ip": "224.0.0.3",
        "name": "dev3",
        "interfaces": [
            {
                "Interface": "GE0/3/3",
                "Status": "up",  # ================== TO DEV2 - UP
                "Description": "desc3_to_dev2",
            },
            {
                "Interface": "GE0/3/4",
                "Status": "up",  # ================== TO DEV4 - UP
                "Description": "desc4_to_dev4",
            },
        ],
    },
    {
        "ip": "224.0.0.4",
        "name": "dev4",
        "interfaces_vlans": [
            {
                "Interface": "GE0/4/3",
                "Status": "up",  # ================ TO DEV3 - UP
                "Description": "desc3_to_dev3",
                "VLAN's": ["4", "30 to 32"],
            },
            {
                "Interface": "GE0/4/4",
                "Status": "up",  # ================ TO DEV1 - UP
                "Description": "desc4_to_dev1",
                "VLAN's": ["4", "30 to 32"],
            },
        ],
    },
]


class TestTransportRingManager(TransportRingManager):
    device_manager = DeviceManager


class TestHeadDownSolutions(TestRingBase):
    TEST_DEVICES = TEST_DEVICES

    def test_head_down_solutions(self):
        r = TestTransportRingManager(ring=TransportRing.objects.get(name="ring1"))
        r.collect_all_interfaces()
        r.find_link_between_devices()

        # Все оборудование доступно
        for d in r.ring_devs:
            d.ping = True

        solutions = r.create_solutions().solutions

        self.assertTrue(len(solutions), 1)

        self.assertTrue(
            solutions[0],
            {"info": {"message": "Кольцо находится в исправном состоянии"}},
        )
