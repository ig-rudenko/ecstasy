import json
from datetime import datetime

from django import test

from check.models import Devices
from motr.models import RingDevs, TransportRing
from net_tools.models import DevicesInfo


class TestRingBase(test.TransactionTestCase):
    TEST_DEVICES: list

    def setUp(self):
        # Добавляем оборудования

        model_devices_list = []

        for test_data in self.TEST_DEVICES:
            dev = Devices.objects.create(ip=test_data["ip"], name=test_data["name"])

            # Добавляем созданное оборудование в список
            model_devices_list.append(dev)

            # Создаем историю для интерфейсов
            if test_data.get("interfaces"):
                DevicesInfo.objects.create(
                    dev=dev,
                    interfaces=json.dumps(test_data.get("interfaces")),
                    interfaces_date=datetime.now(),
                )

            # Создаем историю для интерфейсов и VLANS
            if test_data.get("interfaces_vlans"):
                DevicesInfo.objects.create(
                    dev=dev,
                    vlans=json.dumps(test_data.get("interfaces_vlans")),
                    vlans_date=datetime.now(),
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
            first_ring_dev = RingDevs.objects.create(
                ring_name="ring1",
                device=model_devices_list[i],
                next_dev=first_ring_dev,
            )
            if last_ring_dev is None:
                last_ring_dev = first_ring_dev

        # Создаем кольцо
        TransportRing.objects.create(
            name="ring1",
            head=first_ring_dev,
            tail=last_ring_dev,
            vlans=[1, 2, 3],
        )
