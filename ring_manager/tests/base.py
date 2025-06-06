import json

from django.test import TransactionTestCase
from django.utils import timezone

from check.models import Devices, DeviceGroup, AuthGroup
from net_tools.models import DevicesInfo
from ring_manager.models import RingDev, TransportRing


class TestRingBase(TransactionTestCase):
    TEST_DEVICES: list
    RING_VLANS = [1, 2, 3]
    ring_name: str

    # @classmethod
    def setUp(self):
        # Добавляем оборудования

        model_devices_list = []
        group = DeviceGroup.objects.create(name="test")
        auth_group = AuthGroup.objects.create(name="test", login="test", password="test")

        for test_data in self.TEST_DEVICES:
            dev = Devices.objects.create(
                ip=test_data["ip"], name=test_data["name"], group=group, auth_group=auth_group
            )

            # Добавляем созданное оборудование в список
            model_devices_list.append(dev)

            # Создаем историю для интерфейсов
            if test_data.get("interfaces"):
                DevicesInfo.objects.create(
                    dev=dev,
                    interfaces=json.dumps(test_data.get("interfaces")),
                    interfaces_date=timezone.now(),
                )

            # Создаем историю для интерфейсов и VLANS
            if test_data.get("interfaces_vlans"):
                DevicesInfo.objects.create(
                    dev=dev,
                    vlans=json.dumps(test_data.get("interfaces_vlans")),
                    vlans_date=timezone.now(),
                )

        # Последнее в цепочке оборудование
        last_ring_dev = None
        # Цикл идет с конца, первое в цепочке оборудование сформируется после цикла
        first_ring_dev = None

        for i in range(len(model_devices_list) - 1, -1, -1):
            # Цикл, который перебирает `model_devices_list` в обратном порядке.
            # Функция `range()` используется для генерации последовательности чисел, начиная с индекса последнего
            # элемента в списке (`len(model_devices_list) - 1`) и заканчивая индексом 0 (`-1`), с шагом -1 (`-1`).
            # Это означает, что цикл начнется с последнего элемента в списке и будет двигаться назад к первому элементу.
            first_ring_dev = RingDev.objects.create(
                ring_name=self.ring_name,
                device=model_devices_list[i],
                next_dev=first_ring_dev,
            )
            if last_ring_dev is None:
                last_ring_dev = first_ring_dev

        # Создаем кольцо
        print(
            "Создаем кольцо",
            TransportRing.objects.create(
                name=self.ring_name,
                head=first_ring_dev,
                tail=last_ring_dev,
                vlans=self.RING_VLANS,
            ),
        )
