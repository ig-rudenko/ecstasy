from datetime import datetime

from devicemanager import DeviceManager
from ring_manager.models import TransportRing
from ring_manager.ring_manager import TransportRingManager
from ring_manager.solutions import SolutionsPerformer
from ring_manager.tests.base import TestRingBase

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


class TestSolutionsPerformer(TestRingBase):
    TEST_DEVICES = TEST_DEVICES

    def test_down_solutions(self):
        class TestTransportRingManager(TransportRingManager):
            device_manager = DeviceManager

        ring = TransportRing.objects.get(name="ring1")

        r = TestTransportRingManager(ring=ring)
        r.collect_all_interfaces()  # Собираем из истории
        r.find_link_between_devices()  # Соединяем

        # dev1 (head), dev4 (tail) доступно
        r.ring_devs[0].ping = True
        r.ring_devs[3].ping = True

        # Кроме dev2, dev3
        r.ring_devs[1].ping = False
        r.ring_devs[2].ping = False

        solutions = r.create_solutions().solutions

        ring.solutions = solutions
        ring.solution_time = datetime.now()
        ring.save(update_fields=["solutions", "solution_time"])

        performer = SolutionsPerformer(ring=ring)
        performer.perform_all()

        # Найдено 2 решения
        self.assertEqual(len(solutions), 2)

        # 1 решение - закрыть порт на dev1 (head) в сторону dev2
        self.assertDictEqual(
            solutions[0],
            {
                "set_port_status": {
                    "status": "down",
                    "device": {
                        "name": r.ring_devs[0].device.name,
                        "ip": r.ring_devs[0].device.ip,
                    },
                    "port": r.ring_devs[0].port_to_next_dev.name,
                    "message": "Закрываем порт в сторону tail, готовимся разворачивать кольцо",
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
