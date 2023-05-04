from devicemanager import Device as DeviceManager
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
                "Status": "down",  # ================== TO DEV3 - DOWN
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
                "Status": "down",  # ================== TO DEV2 - DOWN
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


class TestHeadDownSolutions(TestRingBase):
    TEST_DEVICES = TEST_DEVICES

    def test_head_down_solutions(self):
        class TestTransportRingManager(TransportRingManager):
            device_manager = DeviceManager

        r = TestTransportRingManager(ring=TransportRing.objects.get(name="ring1"))
        r.collect_all_interfaces()  # Собираем из истории
        r.find_link_between_devices()  # Соединяем

        r.ring_devs[0].ping = True
        r.ring_devs[1].ping = True
        r.ring_devs[3].ping = True

        # Обрыв до dev3
        r.ring_devs[2].ping = True

        solutions = r.create_solutions().solutions

        print(solutions)

        # Найдено 2 решения
        self.assertEqual(len(solutions), 2)

        # 1 решение - закрыть порт на dev1 (head) в сторону dev2
        self.assertDictEqual(
            solutions[0],
            {
                "set_port_status": {
                    "status": "down",
                    "device": {
                        "name": r.ring_devs[1].device.name,
                        "ip": r.ring_devs[1].device.ip,
                    },
                    "port": r.ring_devs[1].port_to_next_dev.name,
                    "message": "Нашли обрыв между: "
                    "dev2 (224.0.0.2) - порт (GE0/2/4) и dev3 (224.0.0.3) - порт (GE0/3/3)",
                }
            },
        )

        # 2 решение - прописать VLANS на dev4 (tail) в сторону dev3
        self.assertDictEqual(
            solutions[1],
            {
                "set_port_vlans": {
                    "status": "add",
                    "vlans": (1, 2, 3),
                    "device": {
                        "name": r.ring_devs[-1].device.name,
                        "ip": r.ring_devs[-1].device.ip,
                    },
                    "port": r.ring_devs[-1].port_to_prev_dev.name,
                    "message": "Прописываем VLANS (1, 2, 3) на dev4 (224.0.0.4) на порту GE0/4/3",
                }
            },
        )
