from devicemanager.device import DeviceManager

from ..models import TransportRing
from ..ring_manager import TransportRingManager
from .base import TestRingBase

TEST_DEVICES = [
    {
        "ip": "224.0.1.1",
        "name": "ring-dev11",
        "interfaces_vlans": [
            {
                "name": "GE0/1/3",
                "status": "up",  # ================= TO DEV3 - UP
                "description": "desc3_to_ring-dev13",
                "vlans": ["1-4", "30 to 32"],
            },
            {
                "name": "GE0/1/4",
                "status": "up",  # ================== TO DEV2 - UP
                "description": "desc4_to_ring-dev12",
                "vlans": ["1-4", "30 to 32"],
            },
        ],
    },
    {
        "ip": "224.0.1.2",
        "name": "ring-dev12",
        "interfaces": [
            {
                "name": "GE0/2/3",
                "status": "up",  # ================== TO DEV1 - UP
                "description": "desc3_to_ring-dev11",
            },
            {
                "name": "GE0/2/4",
                "status": "up",  # ================== TO DEV3 - UP
                "description": "desc4_to_ring-dev13",
            },
        ],
    },
    {
        "ip": "224.0.1.3",
        "name": "ring-dev13",
        "interfaces": [
            {
                "name": "GE0/3/3",
                "status": "up",  # ================== TO DEV2 - UP
                "description": "desc3_to_ring-dev12",
            },
            {
                "name": "GE0/3/4",
                "status": "up",  # ================== TO DEV4 - UP
                "description": "desc4_to_ring-dev14",
            },
        ],
    },
    {
        "ip": "224.0.1.4",
        "name": "ring-dev14",
        "interfaces": [
            {
                "name": "GE0/4/3",
                "status": "up",  # ================ TO DEV3 - UP
                "description": "desc3_to_ring-dev13",
            },
            {
                "name": "GE0/4/4",
                "status": "up",  # ================ TO DEV5 - UP
                "description": "desc4_to_ring-dev15",
            },
        ],
    },
    {
        "ip": "224.0.1.5",
        "name": "ring-dev15",
        "interfaces_vlans": [
            {
                "name": "GE0/5/3",
                "status": "up",  # ================ TO DEV4 - UP
                "description": "desc3_to_ring-dev14",
                "vlans": ["4", "30 to 32"],
            },
            {
                "name": "GE0/5/4",
                "status": "up",  # ================ TO DEV1 - UP
                "description": "desc4_to_ring-dev11",
                "vlans": ["4", "30 to 32"],
            },
        ],
    },
]


class TestHeadDownSolutions(TestRingBase):
    TEST_DEVICES = TEST_DEVICES
    ring_name = "ring11"

    def test_head_down_solutions(self):
        class TestTransportRingManager(TransportRingManager):
            device_manager = DeviceManager

        r = TestTransportRingManager(ring=TransportRing.objects.get(name=self.ring_name))
        r.collect_all_interfaces()  # Собираем из истории
        r.find_link_between_devices()  # Соединяем

        r.ring_devs[0].ping = True  # dev1 `head`
        r.ring_devs[1].ping = False  # dev2
        r.ring_devs[2].ping = True  # dev3
        r.ring_devs[3].ping = False  # dev4
        r.ring_devs[4].ping = True  # dev5 `tail`

        solutions = r.create_solutions().solutions

        print(solutions)

        # Найдено 1 решение
        self.assertEqual(len(solutions), 1)

        # Решение
        self.assertDictEqual(
            solutions[0],
            {
                "error": {
                    "status": "uncertainty",
                    "message": "После цепочки недоступных появляется еще одно недоступное устройство, "
                    "видимо проблемы на сети",
                }
            },
        )
