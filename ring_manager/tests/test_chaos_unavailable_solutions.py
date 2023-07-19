from devicemanager.device import DeviceManager
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
        "interfaces": [
            {
                "Interface": "GE0/4/3",
                "Status": "up",  # ================ TO DEV3 - UP
                "Description": "desc3_to_dev3",
            },
            {
                "Interface": "GE0/4/4",
                "Status": "up",  # ================ TO DEV5 - UP
                "Description": "desc4_to_dev5",
            },
        ],
    },
    {
        "ip": "224.0.0.5",
        "name": "dev5",
        "interfaces_vlans": [
            {
                "Interface": "GE0/5/3",
                "Status": "up",  # ================ TO DEV4 - UP
                "Description": "desc3_to_dev4",
                "VLAN's": ["4", "30 to 32"],
            },
            {
                "Interface": "GE0/5/4",
                "Status": "up",  # ================ TO DEV1 - UP
                "Description": "desc4_to_dev1",
                "VLAN's": ["4", "30 to 32"],
            },
        ],
    },
]


class TestHeadDownSolutions(TestRingBase):
    TEST_DEVICES = TEST_DEVICES

    def test_head_down_solutions(self):
        class TestTransportRingManager(TransportRingManager):
            device_manager = DeviceManager

        r = TestTransportRingManager(ring=TransportRing.objects.get(name="ring1"))
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
