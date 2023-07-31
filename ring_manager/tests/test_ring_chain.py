from check.models import Devices
from devicemanager.device import Interfaces
from devicemanager.device import DeviceManager
from .base import TestRingBase
from ..models import TransportRing, RingDev
from ..ring_manager import TransportRingManager, RingPoint, InvalidRingStructureError

#    DEV1 (gi4) --> (gi3) DEV2
#    (gi3)               (gi4)
#      \                  /
#       \                /
#        \              /
#        (gi4) DEV3 (gi3)

TEST_DEVICES = [
    {
        "ip": "224.0.4.1",
        "name": "ring-dev41",
        "interfaces_vlans": [
            {
                "Interface": "GE0/1/1",
                "Status": "admin down",
                "Description": "desc1",
                "VLAN's": ["1-4", "30 to 32"],
            },
            {
                "Interface": "GE0/1/2",
                "Status": "admin down",
                "Description": "desc2",
                "VLAN's": ["1-4", "30 to 32"],
            },
            {
                "Interface": "GE0/1/3",
                "Status": "admin down",
                "Description": "desc3_to_ring-dev43",
                "VLAN's": ["1-4", "30 to 32"],
            },
            {
                "Interface": "GE0/1/4",
                "Status": "up",
                "Description": "desc4_to_ring-dev42",
                "VLAN's": ["1-4", "30 to 32"],
            },
        ],
    },
    {
        "ip": "224.0.4.2",
        "name": "ring-dev42",
        "interfaces": [
            {
                "Interface": "GE0/2/1",
                "Status": "admin down",
                "Description": "desc1",
            },
            {
                "Interface": "GE0/2/2",
                "Status": "admin down",
                "Description": "desc2",
            },
            {
                "Interface": "GE0/2/3",
                "Status": "admin down",
                "Description": "desc3_to_ring-dev41",
            },
            {
                "Interface": "GE0/2/4",
                "Status": "up",
                "Description": "desc4_to_ring-dev43",
            },
        ],
    },
    {
        "ip": "224.0.4.3",
        "name": "ring-dev43",
        "interfaces_vlans": [
            {
                "Interface": "GE0/3/1",
                "Status": "admin down",
                "Description": "desc1",
                "VLAN's": ["30 to 32"],
            },
            {
                "Interface": "GE0/3/2",
                "Status": "admin down",
                "Description": "desc2",
                "VLAN's": ["30 to 32"],
            },
            {
                "Interface": "GE0/3/3",
                "Status": "admin down",
                "Description": "desc3_to_ring-dev42",
                "VLAN's": ["4", "30 to 32"],
            },
            {
                "Interface": "GE0/3/4",
                "Status": "up",
                "Description": "desc4_to_ring-dev41",
                "VLAN's": ["4", "30 to 32"],
            },
        ],
    },
]


class TestRingChain(TestRingBase):
    TEST_DEVICES = TEST_DEVICES
    ring_name = "ring41"

    def test_invalid_init_ring(self):
        """
        Проверяем неверную инициализацию кольца
        """
        # Неверный тип переменной передается в кольцо
        with self.assertRaises(TypeError):
            TransportRingManager("TransportRing")

        # Кольцо, которое не указывает на начальное оборудование `model.RingDev`
        # Т.е. поле `head` == `null`
        with self.assertRaises(InvalidRingStructureError):
            TransportRingManager(TransportRing.objects.create(name="invalid", vlans=[1]))

        # Не указаны VLAN для транспортного кольца
        with self.assertRaises(InvalidRingStructureError):
            TransportRingManager(
                TransportRing.objects.create(
                    name="without_vlans", head=RingDev.objects.first(), vlans=[1]
                )
            )

    def test_init_ring(self):
        """
        Проверяем инициализацию менеджера кольца
        """
        point1 = RingDev.objects.get(device__name="ring-dev41")
        point2 = RingDev.objects.get(device__name="ring-dev42")
        point3 = RingDev.objects.get(device__name="ring-dev43")
        self.maxDiff = None
        r = TransportRingManager(ring=TransportRing.objects.get(name=self.ring_name))

        print(r.ring_devs)

        self.assertEqual(
            r.ring_devs,
            [
                RingPoint(point=point1, device=point1.device, collect_vlans=True),
                RingPoint(point=point2, device=point2.device, collect_vlans=False),
                RingPoint(point=point3, device=point3.device, collect_vlans=True),
            ],
        )

        # Проверяем преобразование из JSON строки в список
        self.assertEqual(
            TransportRing.objects.get(name=self.ring_name).vlans,
            [1, 2, 3],
        )

    def test_ring_normalizer(self):
        """
        Проверяем нормализацию менеджера кольца
        """
        ring = TransportRing.objects.get(name=self.ring_name)

        point1 = RingDev.objects.get(device__name="ring-dev41")
        point2 = RingDev.objects.get(device__name="ring-dev42")
        point3 = RingDev.objects.get(device__name="ring-dev43")

        # Проверяем отсутствие обратной связи
        self.assertEqual(point1.prev_dev, None)
        self.assertEqual(point2.prev_dev, None)
        self.assertEqual(point3.prev_dev, None)

        # Проверяем, что кольцо исправно
        r = TransportRingManager(ring=ring)
        self.assertEqual(
            r.ring_devs,
            [
                RingPoint(point=point1, device=point1.device, collect_vlans=True),
                RingPoint(point=point2, device=point2.device, collect_vlans=False),
                RingPoint(point=point3, device=point3.device, collect_vlans=True),
            ],
        )

        # ========= Выполняем нормализацию ===========
        r.normalize()

        point1 = RingDev.objects.get(device__name="ring-dev41")
        point2 = RingDev.objects.get(device__name="ring-dev42")
        point3 = RingDev.objects.get(device__name="ring-dev43")

        # Проверяем обратную связь
        self.assertEqual(point1.prev_dev, None)
        self.assertEqual(point2.prev_dev, point1)
        self.assertEqual(point3.prev_dev, point2)

        # Проверяем, что кольцо исправно
        self.assertEqual(
            r.ring_devs,
            [
                RingPoint(point=point1, device=point1.device, collect_vlans=True),
                RingPoint(point=point2, device=point2.device, collect_vlans=False),
                RingPoint(point=point3, device=point3.device, collect_vlans=True),
            ],
        )

    def test_ring_check_devices_availability(self):
        """
        Проверяем ping для менеджера кольца
        """
        point1 = RingDev.objects.get(device__name="ring-dev41")
        point2 = RingDev.objects.get(device__name="ring-dev42")
        point3 = RingDev.objects.get(device__name="ring-dev43")

        r = TransportRingManager(ring=TransportRing.objects.get(name=self.ring_name))

        r.check_devices_availability()

        self.assertEqual(
            r.ring_devs,
            [
                RingPoint(point=point1, device=point1.device, ping=False, collect_vlans=True),
                RingPoint(point=point2, device=point2.device, ping=False, collect_vlans=False),
                RingPoint(point=point3, device=point3.device, ping=False, collect_vlans=True),
            ],
        )

        # Одно оборудование доступно

        Devices.objects.filter(name="ring-dev41").update(ip="127.0.0.1")

        r = TransportRingManager(ring=TransportRing.objects.get(name=self.ring_name))

        r.check_devices_availability()

        self.assertEqual(
            r.ring_devs,
            [
                RingPoint(point=point1, device=point1.device, ping=True, collect_vlans=True),
                RingPoint(point=point2, device=point2.device, ping=False, collect_vlans=False),
                RingPoint(point=point3, device=point3.device, ping=False, collect_vlans=True),
            ],
        )

    def test_collect_interfaces(self):
        """
        Проверяем сбор интерфейсов для менеджера кольца
        """

        class TestTransportRingManager(TransportRingManager):
            device_manager = DeviceManager

        r = TestTransportRingManager(ring=TransportRing.objects.get(name=self.ring_name))

        # No ping, так что интерфейсы будут собраны из истории
        for p in r.ring_devs:
            p.ping = False

        r.collect_all_interfaces()

        interfaces = []
        for data in TEST_DEVICES:
            interfaces.append(Interfaces(data.get("interfaces") or data.get("interfaces_vlans")))

        self.assertEqual(str(r.ring_devs[0].interfaces), str(interfaces[0]))
        self.assertEqual(str(r.ring_devs[1].interfaces), str(interfaces[1]))
        self.assertEqual(str(r.ring_devs[2].interfaces), str(interfaces[2]))

    def test_find_link_between_devices(self):
        """
        Функция представляет собой тестовый пример для поиска связи между устройствами.
        """

        class TestTransportRingManager(TransportRingManager):
            device_manager = DeviceManager

        r = TestTransportRingManager(ring=TransportRing.objects.get(name=self.ring_name))

        # No ping, так что интерфейсы будут собраны из истории
        for p in r.ring_devs:
            p.ping = False

        r.collect_all_interfaces()
        r.find_link_between_devices()

        #    DEV1 (gi1/4) -----> (gi2/3) DEV2
        #    (gi1/3)                 (gi2/4)
        #      \                       /
        #       \                     /
        #        \                   /
        #       (gi3/4)  DEV3  (gi3/3)

        # DEV1
        self.assertEqual(r.ring_devs[0].port_to_prev_dev.name, "GE0/1/3")
        self.assertEqual(r.ring_devs[0].port_to_next_dev.name, "GE0/1/4")

        # DEV2
        self.assertEqual(r.ring_devs[1].port_to_prev_dev.name, "GE0/2/3")
        self.assertEqual(r.ring_devs[1].port_to_next_dev.name, "GE0/2/4")

        # DEV3
        self.assertEqual(r.ring_devs[2].port_to_prev_dev.name, "GE0/3/3")
        self.assertEqual(r.ring_devs[2].port_to_next_dev.name, "GE0/3/4")

    def test_ring_status_all_unavailable(self):
        class TestTransportRingManager(TransportRingManager):
            device_manager = DeviceManager

        r = TestTransportRingManager(ring=TransportRing.objects.get(name=self.ring_name))
        # No ping
        for p in r.ring_devs:
            p.ping = False

        r.ring_devs[0].point.delete()
