import pprint
from datetime import datetime

from check.models import Devices, AuthGroup
from devicemanager.device import DeviceManager
from devicemanager.session_control import DEVICE_SESSIONS
from .base import TestRingBase
from ..models import TransportRing
from ..ring_manager import TransportRingManager
from ..solutions import SolutionsPerformer

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


class TestTransportRingManager(TransportRingManager):
    device_manager = DeviceManager


class FakePexpectSession:
    @staticmethod
    def isalive():
        return True


class TailSession:
    def __init__(self):
        self.session = FakePexpectSession()
        self.vlans_on_port_args = []
        self.port_vlans = ["4"]

    def vlans_on_port(self, port, operation, vlans):
        """Будет смотреть сколько раз вызывался данный метод и какие параметры были переданы"""
        self.vlans_on_port_args.append([port, operation, vlans])
        if operation == "add":
            self.port_vlans += vlans
        else:
            self.port_vlans = ["4"]

    def get_vlans(self):
        """
        Необходимо вернуть порт GE0/5/3 без VLAN {1, 2, 3}
        :return:
        """
        return [
            {
                "Interface": "GE0/5/3",
                "Status": "up",  # ================ TO DEV4 - UP
                "Description": "desc3_to_dev4",
                "VLAN's": self.port_vlans,  # ============ NO VLANS
            },
            {
                "Interface": "GE0/5/4",
                "Status": "up",  # ================ TO DEV1 - UP
                "Description": "desc4_to_dev1",
                "VLAN's": ["4", "30 to 32"],
            },
        ]


class FakeDev3Session:
    def __init__(self):
        self.session = FakePexpectSession()
        self.set_port_args = []
        self.port_status = "admin down"

    def set_port(self, port, status, save_config):
        """Будет смотреть сколько раз вызывался данный метод и какие параметры были переданы"""
        self.set_port_args.append([port, status, save_config])
        if status == "up":
            self.port_status = "up"
        else:
            self.port_status = "admin down"

    def get_interfaces(self):
        return (
            [
                {
                    "Interface": "GE0/3/3",
                    "Status": "up",  # ================== TO DEV2 - UP
                    "Description": "desc3_to_dev2",
                },
                {
                    "Interface": "GE0/3/4",
                    "Status": self.port_status,  # ==================
                    "Description": "desc4_to_dev4",
                },
            ],
        )


class TestRotateToNormalSolutions(TestRingBase):
    TEST_DEVICES = TEST_DEVICES

    def test_rotate_to_normal_solutions(self):
        """
        Кольцо уже было развернуто, на оборудовании dev3 порт выключен в сторону dev4.
        На dev5 (tail) необходимые VLAN's добавлены.
        Необходимо проверить создание решений, для разворота в штатное состояние
        :return:
        """

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
                    "device": {  # `tail`
                        "name": r.ring_devs[-1].device.name,
                        "ip": r.ring_devs[-1].device.ip,
                    },
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
                    "device": {  # dev3
                        "name": r.ring_devs[2].device.name,
                        "ip": r.ring_devs[2].device.ip,
                    },
                    "port": "GE0/3/4",
                    "message": "Переводим кольцо в штатное состояние",
                }
            },
        )

    def test_perform_solutions_fail_first(self):
        ring = TransportRing.objects.get(name="ring1")

        r = TestTransportRingManager(ring=ring)
        r.collect_all_interfaces()  # Собираем из истории
        r.find_link_between_devices()  # Соединяем

        # Все оборудование доступно
        for dev in r.ring_devs:
            dev.ping = True

        solutions = r.create_solutions().solutions

        print(solutions)

        ring.solutions = solutions
        ring.solution_time = datetime.now()
        ring.save(update_fields=["solutions", "solution_time"])

        performer = SolutionsPerformer(ring=ring)
        performed_solutions = performer.perform_all()

        # Найдено 3 решения
        self.assertEqual(len(performed_solutions), 3)

        # Решение 1 - NO STATUS
        self.assertDictEqual(
            performed_solutions[0],
            {
                "info": {
                    "message": "Транспортное кольцо в данный момент развернуто, со стороны dev5 "
                    "Убедитесь, что линия исправна, ведь дальнейшие действия развернут кольцо в штатное состояние"
                }
            },
        )

        # Решение 2 - STATUS FAIL
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
                    "на оборудовании dev5 (224.0.0.5) на порту GE0/5/3",
                    "perform_status": "fail",
                    "error": "Оборудование dev5 (224.0.0.5) недоступно",
                }
            },
        )

        # Решение 3 - NO STATUS
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
                }
            },
        )

    def test_perform_solutions_fail_last(self):
        # Меняем IP TAIL чтобы он был доступен
        Devices.objects.filter(ip="224.0.0.5").update(
            ip="127.0.0.1",
            auth_group=AuthGroup.objects.create(login="admin", password="admin", name="test"),
        )
        # Также создаем группу авторизации для данного оборудования

        ring = TransportRing.objects.get(name="ring1")

        r = TestTransportRingManager(ring=ring)
        r.collect_all_interfaces()  # Собираем из истории
        r.find_link_between_devices()  # Соединяем

        # Все оборудование доступно
        for dev in r.ring_devs:
            dev.ping = True

        solutions = r.create_solutions().solutions

        ring.solutions = solutions
        ring.solution_time = datetime.now()
        ring.save(update_fields=["solutions", "solution_time"])

        # Создаем фальшивую сессию и делаем её глобальной, для тестирования
        tail_fake_session = TailSession()
        DEVICE_SESSIONS.add_connection(r.ring_devs[-1].device.ip, tail_fake_session)

        # Теперь `SolutionsPerformer` будет использовать для `tail` фальшивую сессию
        performer = SolutionsPerformer(ring=ring)
        performed_solutions = performer.perform_all()

        pprint.pprint(performed_solutions)

        # Найдено 3 решения
        self.assertEqual(len(performed_solutions), 3)

        # Первое действие над Tail это удаление VLAN, затем неудачная попытка поменять состояние
        # порта на другом оборудовании и второе действие - добавление VLAN
        self.assertEqual(
            tail_fake_session.vlans_on_port_args,
            [["GE0/5/3", "delete", (1, 2, 3)], ["GE0/5/3", "add", (1, 2, 3)]],
        )

        self.assertEqual(len(tail_fake_session.vlans_on_port_args), 2)

        # Решение 1 - NO STATUS
        self.assertDictEqual(
            performed_solutions[0],
            {
                "info": {
                    "message": "Транспортное кольцо в данный момент развернуто, со стороны dev5 "
                    "Убедитесь, что линия исправна, ведь дальнейшие действия развернут кольцо в штатное состояние"
                }
            },
        )

        # Решение 2 - STATUS REVERSED
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
                    "на оборудовании dev5 (127.0.0.1) на порту GE0/5/3",
                    "perform_status": "reversed",
                }
            },
        )

        # Решение 3 - STATUS FAIL
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
                    "perform_status": "fail",
                    "error": f"Оборудование {r.ring_devs[2].device.name} ({r.ring_devs[2].device.ip}) недоступно",
                }
            },
        )

    def test_perform_solutions_ok(self):
        # Меняем IP TAIL и Dev3 чтобы они были доступны
        auth = AuthGroup.objects.create(login="admin", password="admin", name="test")
        Devices.objects.filter(ip="224.0.0.5").update(ip="127.0.0.1", auth_group=auth)
        Devices.objects.filter(ip="224.0.0.3").update(ip="127.0.0.2", auth_group=auth)
        # Также создаем группу авторизации для данного оборудования

        ring = TransportRing.objects.get(name="ring1")

        r = TestTransportRingManager(ring=ring)
        r.collect_all_interfaces()  # Собираем из истории
        r.find_link_between_devices()  # Соединяем

        # Все оборудование доступно
        for dev in r.ring_devs:
            dev.ping = True

        solutions = r.create_solutions().solutions

        ring.solutions = solutions
        ring.solution_time = datetime.now()
        ring.save(update_fields=["solutions", "solution_time"])

        # Создаем фальшивую сессию и делаем её глобальной, для тестирования
        tail_fake_session = TailSession()
        dev3_fake_session = FakeDev3Session()
        DEVICE_SESSIONS.add_connection(r.ring_devs[-1].device.ip, tail_fake_session)
        DEVICE_SESSIONS.add_connection(r.ring_devs[2].device.ip, dev3_fake_session)

        # Теперь `SolutionsPerformer` будет использовать для `tail` и `dev3` фальшивую сессию
        performer = SolutionsPerformer(ring=ring)
        performed_solutions = performer.perform_all()

        pprint.pprint(performed_solutions)

        # Найдено 3 решения
        self.assertEqual(len(performed_solutions), 3)

        # Первое действие над Tail это удаление VLAN
        self.assertEqual(
            tail_fake_session.vlans_on_port_args,
            [["GE0/5/3", "delete", (1, 2, 3)]],  # port, status, vlans
        )
        # Второе действие - это закрытие порта на `dev3`
        self.assertEqual(
            dev3_fake_session.set_port_args,
            [["GE0/3/4", "up", True]],  # port, status, save_config
        )

        # Решение 1 - NO STATUS
        self.assertDictEqual(
            performed_solutions[0],
            {
                "info": {
                    "message": "Транспортное кольцо в данный момент развернуто, со стороны dev5 "
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
                    "на оборудовании dev5 (127.0.0.1) на порту GE0/5/3",
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
