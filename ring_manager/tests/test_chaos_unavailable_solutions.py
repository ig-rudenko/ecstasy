from devicemanager.device import DeviceManager
from .base import TestRingBase
from ..models import TransportRing
from ..ring_manager import TransportRingManager

TEST_DEVICES = [
    {
        "ip": "224.0.1.1",
        "name": "ring-dev11",
        "interfaces_vlans": [
            {
                "Interface": "GE0/1/3",
                "Status": "up",  # ================= TO DEV3 - UP
                "Description": "desc3_to_ring-dev13",
                "VLAN's": ["1-4", "30 to 32"],
            },
            {
                "Interface": "GE0/1/4",
                "Status": "up",  # ================== TO DEV2 - UP
                "Description": "desc4_to_ring-dev12",
                "VLAN's": ["1-4", "30 to 32"],
            },
        ],
    },
    {
        "ip": "224.0.1.2",
        "name": "ring-dev12",
        "interfaces": [
            {
                "Interface": "GE0/2/3",
                "Status": "up",  # ================== TO DEV1 - UP
                "Description": "desc3_to_ring-dev11",
            },
            {
                "Interface": "GE0/2/4",
                "Status": "up",  # ================== TO DEV3 - UP
                "Description": "desc4_to_ring-dev13",
            },
        ],
    },
    {
        "ip": "224.0.1.3",
        "name": "ring-dev13",
        "interfaces": [
            {
                "Interface": "GE0/3/3",
                "Status": "up",  # ================== TO DEV2 - UP
                "Description": "desc3_to_ring-dev12",
            },
            {
                "Interface": "GE0/3/4",
                "Status": "up",  # ================== TO DEV4 - UP
                "Description": "desc4_to_ring-dev14",
            },
        ],
    },
    {
        "ip": "224.0.1.4",
        "name": "ring-dev14",
        "interfaces": [
            {
                "Interface": "GE0/4/3",
                "Status": "up",  # ================ TO DEV3 - UP
                "Description": "desc3_to_ring-dev13",
            },
            {
                "Interface": "GE0/4/4",
                "Status": "up",  # ================ TO DEV5 - UP
                "Description": "desc4_to_ring-dev15",
            },
        ],
    },
    {
        "ip": "224.0.1.5",
        "name": "ring-dev15",
        "interfaces_vlans": [
            {
                "Interface": "GE0/5/3",
                "Status": "up",  # ================ TO DEV4 - UP
                "Description": "desc3_to_ring-dev14",
                "VLAN's": ["4", "30 to 32"],
            },
            {
                "Interface": "GE0/5/4",
                "Status": "up",  # ================ TO DEV1 - UP
                "Description": "desc4_to_ring-dev11",
                "VLAN's": ["4", "30 to 32"],
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
