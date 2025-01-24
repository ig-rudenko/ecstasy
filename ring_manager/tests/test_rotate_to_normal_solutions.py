import pprint
from unittest.mock import patch

from django.utils import timezone

from check.models import Devices, AuthGroup
from devicemanager.device import DeviceManager
from devicemanager.remote import remote_connector
from devicemanager.remote.connector import RemoteDevice
from .base import TestRingBase
from ..models import TransportRing
from ..ring_manager import TransportRingManager
from ..solutions import SolutionsPerformer

TEST_DEVICES = [
    {
        "ip": "224.0.5.1",
        "name": "ring-dev51",
        "interfaces_vlans": [
            {
                "Interface": "GE0/1/3",
                "Status": "up",  # ================= TO DEV3 - UP
                "Description": "desc3_to_ring-dev53",
                "VLAN's": ["1-4", "30 to 32"],
            },
            {
                "Interface": "GE0/1/4",
                "Status": "up",  # ================== TO DEV2 - UP
                "Description": "desc4_to_ring-dev52",
                "VLAN's": ["1-4", "30 to 32"],
            },
        ],
    },
    {
        "ip": "224.0.5.2",
        "name": "ring-dev52",
        "interfaces": [
            {
                "Interface": "GE0/2/3",
                "Status": "up",  # ================== TO DEV1 - UP
                "Description": "desc3_to_ring-dev51",
            },
            {
                "Interface": "GE0/2/4",
                "Status": "up",  # ================== TO DEV3 - UP
                "Description": "desc4_to_ring-dev53",
            },
        ],
    },
    {
        "ip": "224.0.5.3",
        "name": "ring-dev53",
        "interfaces": [
            {
                "Interface": "GE0/3/3",
                "Status": "up",  # ================== TO DEV2 - UP
                "Description": "desc3_to_ring-dev52",
            },
            {
                "Interface": "GE0/3/4",
                "Status": "admin down",  # ================== TO DEV4 - ADMIN DOWN
                "Description": "desc4_to_ring-dev54",
            },
        ],
    },
    {
        "ip": "224.0.5.4",
        "name": "ring-dev54",
        "interfaces": [
            {
                "Interface": "GE0/4/3",
                "Status": "down",  # ================ TO DEV3 - UP
                "Description": "desc3_to_ring-dev53",
            },
            {
                "Interface": "GE0/4/4",
                "Status": "up",  # ================ TO DEV5 - UP
                "Description": "desc4_to_ring-dev55",
            },
        ],
    },
    {
        "ip": "224.0.5.5",
        "name": "ring-dev55",
        "interfaces_vlans": [
            {
                "Interface": "GE0/5/3",
                "Status": "up",  # ================ TO DEV4 - UP
                "Description": "desc3_to_ring-dev54",
                "VLAN's": ["1-4", "30 to 32"],  # ============ HAS VLANS
            },
            {
                "Interface": "GE0/5/4",
                "Status": "up",  # ================ TO DEV1 - UP
                "Description": "desc4_to_ring-dev51",
                "VLAN's": ["4", "30 to 32"],
            },
        ],
    },
]


class TestTransportRingManager(TransportRingManager):
    device_manager = DeviceManager


class FakeTailSession(RemoteDevice):
    vlans_on_port_args: list[list] = []
    port_vlans = ["4"]

    @classmethod
    def reset_class_data(cls):
        cls.vlans_on_port_args = []
        cls.port_vlans = ["4"]

    @classmethod
    def vlans_on_port(
        cls,
        port: str,
        operation,
        vlans,
        tagged: bool = True,
    ):
        """Будет смотреть сколько раз вызывался данный метод и какие параметры были переданы"""
        cls.vlans_on_port_args.append([port, operation, vlans])
        if operation == "add":
            cls.port_vlans += vlans
        else:
            cls.port_vlans = ["4"]

    @classmethod
    def get_vlans(cls):
        """
        Необходимо вернуть порт GE0/5/3 без VLAN {1, 2, 3}
        :return:
        """
        return [
            {
                "Interface": "GE0/5/3",
                "Status": "up",  # ================ TO DEV4 - UP
                "Description": "desc3_to_ring-dev54",
                "VLAN's": cls.port_vlans,  # ============ NO VLANS
            },
            {
                "Interface": "GE0/5/4",
                "Status": "up",  # ================ TO DEV1 - UP
                "Description": "desc4_to_ring-dev51",
                "VLAN's": ["4", "30 to 32"],
            },
        ]


class FakeTailAndDev3Session(FakeTailSession):
    set_port_args: list[list] = []
    port_status = "admin down"

    @classmethod
    def reset_class_data(cls):
        cls.set_port_args = []
        cls.port_status = "admin down"

    @classmethod
    def set_port(cls, port, status, save_config=True):
        """Будет смотреть сколько раз вызывался данный метод и какие параметры были переданы"""
        cls.set_port_args.append([port, status, save_config])
        if status == "up":
            cls.port_status = "up"
        else:
            cls.port_status = "admin down"

    @classmethod
    def get_interfaces(cls):
        return (
            [
                {
                    "Interface": "GE0/3/3",
                    "Status": "up",  # ================== TO DEV2 - UP
                    "Description": "desc3_to_ring-dev52",
                },
                {
                    "Interface": "GE0/3/4",
                    "Status": cls.port_status,  # ==================
                    "Description": "desc4_to_ring-dev54",
                },
            ],
        )


class TestRotateToNormalSolutions(TestRingBase):
    TEST_DEVICES = TEST_DEVICES
    ring_name = "ring51"

    def setUp(self):
        super(TestRotateToNormalSolutions, self).setUp()
        FakeTailSession.reset_class_data()

    def test_rotate_to_normal_solutions(self):
        """
        Кольцо уже было развернуто, на оборудовании ring-dev53 порт выключен в сторону ring-dev54.
        На ring-dev55 (tail) необходимые VLAN's добавлены.
        Необходимо проверить создание решений, для разворота в штатное состояние
        :return:
        """

        r = TestTransportRingManager(ring=TransportRing.objects.get(name=self.ring_name))
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
                    "message": "Транспортное кольцо в данный момент развернуто, со стороны ring-dev55 "
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
                    "device": {  # `tail`
                        "name": r.ring_devs[-1].device.name,
                        "ip": r.ring_devs[-1].device.ip,
                    },
                    "port": "GE0/5/3",
                    "message": "Сначала будут удалены VLAN'ы {1, 2, 3} "
                    "на оборудовании ring-dev55 (224.0.5.5) на порту GE0/5/3",
                }
            },
        )

        # Решение 3
        self.assertDictEqual(
            solutions[2],
            {
                "set_port_status": {
                    "status": "up",
                    "device": {  # dev3
                        "name": r.ring_devs[2].device.name,
                        "ip": r.ring_devs[2].device.ip,
                    },
                    "port": "GE0/3/4",
                    "message": "Переводим кольцо в штатное состояние",
                }
            },
        )

    @patch("check.models.Devices.available", return_value=False)
    def test_perform_solutions_fail_first(self, *args):
        ring = TransportRing.objects.get(name=self.ring_name)

        r = TestTransportRingManager(ring=ring)
        r.collect_all_interfaces()  # Собираем из истории
        r.find_link_between_devices()  # Соединяем

        # Все оборудование доступно
        for dev in r.ring_devs:
            dev.ping = True

        solutions = r.create_solutions().solutions

        print(solutions)

        # Найдено 3 решения
        self.assertEqual(len(solutions), 3)

        # Решение 1 - NO STATUS
        self.assertDictEqual(
            solutions[0],
            {
                "info": {
                    "message": "Транспортное кольцо в данный момент развернуто, со стороны ring-dev55 "
                    "Убедитесь, что линия исправна, ведь дальнейшие действия развернут кольцо в штатное состояние"
                }
            },
        )

        # Решение 2 - STATUS FAIL
        self.assertDictEqual(
            solutions[1],
            {
                "set_port_vlans": {
                    "status": "delete",
                    "vlans": (1, 2, 3),
                    "device": {  # `tail`
                        "name": r.ring_devs[-1].device.name,
                        "ip": r.ring_devs[-1].device.ip,
                    },
                    "port": "GE0/5/3",
                    "message": "Сначала будут удалены VLAN'ы {1, 2, 3} "
                    "на оборудовании ring-dev55 (224.0.5.5) на порту GE0/5/3",
                }
            },
        )

        # Решение 3 - NO STATUS
        self.assertDictEqual(
            solutions[2],
            {
                "set_port_status": {
                    "status": "up",
                    "device": {  # dev3
                        "name": r.ring_devs[2].device.name,
                        "ip": r.ring_devs[2].device.ip,
                    },
                    "port": "GE0/3/4",
                    "message": "Переводим кольцо в штатное состояние",
                }
            },
        )

    @patch("check.models.Devices.available", return_value=False)
    def test_perform_solutions_fail_last(self, *args):
        # Меняем IP TAIL чтобы он был доступен
        Devices.objects.filter(ip="224.0.5.5").update(
            ip="127.0.0.1",
            auth_group=AuthGroup.objects.create(login="admin", password="admin", name="test"),
        )
        # Также создаем группу авторизации для данного оборудования

        ring = TransportRing.objects.get(name=self.ring_name)

        r = TestTransportRingManager(ring=ring)
        r.collect_all_interfaces()  # Собираем из истории
        r.find_link_between_devices()  # Соединяем

        # Все оборудование доступно
        for dev in r.ring_devs:
            dev.ping = True

        solutions = r.create_solutions().solutions

        # Решение 1 - NO STATUS
        self.assertDictEqual(
            solutions[0],
            {
                "info": {
                    "message": "Транспортное кольцо в данный момент развернуто, со стороны ring-dev55 "
                    "Убедитесь, что линия исправна, ведь дальнейшие действия развернут кольцо в штатное состояние"
                }
            },
        )

        # Решение 2 - STATUS REVERSED
        self.assertDictEqual(
            solutions[1],
            {
                "set_port_vlans": {
                    "status": "delete",
                    "vlans": (1, 2, 3),
                    "device": {  # `tail`
                        "name": r.ring_devs[-1].device.name,
                        "ip": r.ring_devs[-1].device.ip,
                    },
                    "port": "GE0/5/3",
                    "message": "Сначала будут удалены VLAN'ы {1, 2, 3} "
                    "на оборудовании ring-dev55 (127.0.0.1) на порту GE0/5/3",
                }
            },
        )

        # Решение 3 - STATUS FAIL
        self.assertDictEqual(
            solutions[2],
            {
                "set_port_status": {
                    "status": "up",
                    "device": {  # dev3
                        "name": r.ring_devs[2].device.name,
                        "ip": r.ring_devs[2].device.ip,
                    },
                    "port": "GE0/3/4",
                    "message": "Переводим кольцо в штатное состояние",
                }
            },
        )

    @patch("check.models.Devices.available", return_value=False)
    def test_perform_solutions_ok(self, *args):
        # Меняем IP TAIL и Dev3 чтобы они были доступны
        auth = AuthGroup.objects.create(login="admin", password="admin", name="test")
        Devices.objects.filter(ip="224.0.5.5").update(ip="127.0.0.1", auth_group=auth)
        Devices.objects.filter(ip="224.0.5.3").update(ip="127.0.0.2", auth_group=auth)
        # Также создаем группу авторизации для данного оборудования

        ring = TransportRing.objects.get(name=self.ring_name)

        r = TestTransportRingManager(ring=ring)
        r.collect_all_interfaces()  # Собираем из истории
        r.find_link_between_devices()  # Соединяем

        # Все оборудование доступно
        for dev in r.ring_devs:
            dev.ping = True

        solutions = r.create_solutions().solutions

        ring.solutions = solutions
        ring.solution_time = timezone.now()
        ring.save(update_fields=["solutions", "solution_time"])

        # Создаем фальшивую сессию и делаем её глобальной, для тестирования
        # Теперь `SolutionsPerformer` будет использовать для `tail` и `dev3` фальшивую сессию
        remote_connector.set_connector(
            "ring_manager.tests.test_rotate_to_normal_solutions.FakeTailAndDev3Session"
        )
        performer = SolutionsPerformer(ring=ring)
        performed_solutions = performer.perform_all()

        pprint.pprint(performed_solutions)

        # Найдено 3 решения
        self.assertEqual(len(performed_solutions), 3)

        # Первое действие над Tail это удаление VLAN
        self.assertEqual(
            FakeTailAndDev3Session.vlans_on_port_args,
            [["GE0/5/3", "delete", (1, 2, 3)]],  # port, status, vlans
        )
        # Второе действие - это закрытие порта на `dev3`
        self.assertEqual(
            FakeTailAndDev3Session.set_port_args,
            [["GE0/3/4", "up", True]],  # port, status, save_config
        )

        # Решение 1 - NO STATUS
        self.assertDictEqual(
            performed_solutions[0],
            {
                "info": {
                    "message": "Транспортное кольцо в данный момент развернуто, со стороны ring-dev55 "
                    "Убедитесь, что линия исправна, ведь дальнейшие действия развернут кольцо в штатное состояние"
                }
            },
        )

        # Решение 2 - STATUS DONE
        self.assertDictEqual(
            performed_solutions[1],
            {
                "set_port_vlans": {
                    "status": "delete",
                    "vlans": (1, 2, 3),
                    "device": {  # `tail`
                        "name": r.ring_devs[-1].device.name,
                        "ip": r.ring_devs[-1].device.ip,
                    },
                    "port": "GE0/5/3",
                    "message": "Сначала будут удалены VLAN'ы {1, 2, 3} "
                    "на оборудовании ring-dev55 (127.0.0.1) на порту GE0/5/3",
                    "perform_status": "done",
                }
            },
        )

        # Решение 3 - STATUS DONE
        self.assertDictEqual(
            performed_solutions[2],
            {
                "set_port_status": {
                    "status": "up",
                    "device": {  # dev3
                        "name": r.ring_devs[2].device.name,
                        "ip": r.ring_devs[2].device.ip,
                    },
                    "port": "GE0/3/4",
                    "message": "Переводим кольцо в штатное состояние",
                    "perform_status": "done",
                }
            },
        )
