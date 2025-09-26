from devicemanager.device import DeviceManager

from ..models import TransportRing
from ..ring_manager import TransportRingManager
from .base import TestRingBase

TEST_DEVICES = [
    {
        "ip": "224.0.3.1",
        "name": "ring-dev31",
        "interfaces_vlans": [
            {
                "name": "GE0/1/3",
                "status": "up",  # ================= TO DEV3 - UP
                "description": "desc3_to_ring-dev33",
                "vlans": ["1-4", "30 to 32"],
            },
            {
                "name": "GE0/1/4",
                "status": "up",  # ================== TO DEV2 - UP
                "description": "desc4_to_ring-dev32",
                "vlans": ["1-4", "30 to 32"],
            },
        ],
    },
    {
        "ip": "224.0.3.2",
        "name": "ring-dev32",
        "interfaces": [
            {
                "name": "GE0/2/3",
                "status": "up",  # ================== TO DEV1 - UP
                "description": "desc3_to_ring-dev31",
            },
            {
                "name": "GE0/2/4",
                "status": "up",  # ================== TO DEV3 - UP
                "description": "desc4_to_ring-dev33",
            },
        ],
    },
    {
        "ip": "224.0.3.3",
        "name": "ring-dev33",
        "interfaces": [
            {
                "name": "GE0/3/3",
                "status": "up",  # ================== TO DEV2 - UP
                "description": "desc3_to_ring-dev32",
            },
            {
                "name": "GE0/3/4",
                "status": "up",  # ================== TO DEV4 - UP
                "description": "desc4_to_ring-dev34",
            },
        ],
    },
    {
        "ip": "224.0.3.4",
        "name": "ring-dev34",
        "interfaces_vlans": [
            {
                "name": "GE0/4/3",
                "status": "up",  # ================ TO DEV3 - UP
                "description": "desc3_to_ring-dev33",
                "vlans": ["4", "30 to 32"],
            },
            {
                "name": "GE0/4/4",
                "status": "up",  # ================ TO DEV1 - UP
                "description": "desc4_to_ring-dev31",
                "vlans": ["4", "30 to 32"],
            },
        ],
    },
]


class TestTransportRingManager(TransportRingManager):
    device_manager = DeviceManager


class TestHeadDownSolutions(TestRingBase):
    TEST_DEVICES = TEST_DEVICES
    ring_name = "ring31"

    def test_head_down_solutions(self):
        r = TestTransportRingManager(ring=TransportRing.objects.get(name=self.ring_name))
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
