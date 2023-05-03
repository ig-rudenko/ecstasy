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
                "Status": "admin down",  # ================== TO DEV4 - ADMIN DOWN
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
                "Status": "down",  # ================ TO DEV3 - UP
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
                "VLAN's": ["1-4", "30 to 32"],  # ============ HAS VLANS
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


class TestRotateToNormalSolutions(TestRingBase):
    TEST_DEVICES = TEST_DEVICES

    def test_rotate_to_normal_solutions(self):
        """
        Кольцо уже было развернуто, на оборудовании dev3 порт выключен в сторону dev4.
        На dev5 (tail) необходимые VLAN's добавлены.
        Необходимо проверить создание решений, для разворота в штатное состояние
        :return:
        """

        class TestTransportRingManager(TransportRingManager):
            device_manager = DeviceManager

        r = TestTransportRingManager(ring=TransportRing.objects.get(name="ring1"))
        r.collect_all_interfaces()  # Собираем из истории
        r.find_link_between_devices()  # Соединяем

        # Все оборудование доступно
        for dev in r.ring_devs:
            dev.ping = True

        solutions = r.create_solutions().solutions

        print(solutions)

        # Найдено 3 решение
        self.assertEqual(len(solutions), 3)

        # Решение 1
        self.assertDictEqual(
            solutions[0],
            {
                "info": {
                    "message": "Транспортное кольцо в данный момент развернуто, со стороны dev5 "
                    "Убедитесь, что линия исправна, ведь дальнейшие действия развернут кольцо в штатное состояние"
                }
            },
        )

        # Решение 2
        self.assertDictEqual(
            solutions[1],
            {
                "set_port_vlans": {
                    "status": "delete",
                    "vlans": (1, 2, 3),
                    "device": r.ring_devs[-1].device,  # `tail`
                    "port": "GE0/5/3",
                    "message": "Сначала будут удалены VLAN'ы {1, 2, 3} "
                    "на оборудовании dev5 (224.0.0.5) на порту GE0/5/3",
                }
            },
        )

        # Решение 3
        self.assertDictEqual(
            solutions[2],
            {
                "set_port_status": {
                    "status": "up",
                    "device": r.ring_devs[2].device,  # dev3
                    "port": "GE0/3/4",
                    "message": "Переводим кольцо в штатное состояние",
                }
            },
        )
