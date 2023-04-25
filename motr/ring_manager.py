from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List

from devicemanager.device import Interfaces, Interface
from check import models
from .models import RingDevs, TransportRing


class InvalidRingStructure(Exception):
    pass


@dataclass
class RingPoint:
    device: models.Devices
    point: RingDevs
    port_to_prev_dev: Interface = Interface()
    port_to_next_dev: Interface = Interface()
    ping: bool = None
    collect_vlans: bool = False
    interfaces: Interfaces = Interfaces()


class TransportRingBase:

    @staticmethod
    def validate_ring(ring):
        if not isinstance(ring, TransportRing):
            raise TypeError(f"Менеджер колец не принимает тип {type(ring)}, только `model.TransportRing`")

        if ring.head is None:
            raise InvalidRingStructure("В кольце не указано головное устройство")

        if ring.tail is None:
            raise InvalidRingStructure("В кольце не указано замыкающее устройство")

        if not ring.vlans:
            raise InvalidRingStructure("Для разворота требуется указать VLAN")

    def __init__(self, ring: TransportRing):
        self.validate_ring(ring)

        self.ring = ring
        self.vlans = ring.vlans

        self.ring_devs = self.ring_devices()

    def ring_devices(self) -> List[RingPoint]:
        """
        Функция «ring_devices» возвращает список устройств в кольце по порядку
        """
        last_device = self.ring.tail

        devs = []

        iter_dev: RingDevs = self.ring.head

        # Перебирает устройства в кольце и добавляет в список
        # Начинается с головного устройства кольца и продолжается добавление пока не достигнет конца кольца
        # (т. е. атрибут next_dev текущего устройства равен None).
        while True:
            devs.append(RingPoint(point=iter_dev, device=iter_dev.device))
            if iter_dev.next_dev is None:
                break
            iter_dev = iter_dev.next_dev

        # Если указано замыкающее устройство, но оно не совпадает с цепочкой устройств в кольце
        if last_device and iter_dev.id != last_device.id:
            raise InvalidRingStructure(
                f"Кольцо замыкается на устройстве ({iter_dev.device}), а  требуется ({last_device.device})"
            )

        # Интерфейсы и VLANs необходимо собирать только у `head` и `tail`
        devs[0].collect_vlans = True
        if last_device:  # Если имеется `tail`
            devs[-1].collect_vlans = True

        return devs


class TransportRingNormalizer(TransportRingBase):
    """
    Класс TransportRingNormalizer нормализует список кольцевых устройств, устанавливая предыдущее устройство для каждого
    устройства в списке, кроме головного.
    """

    def normalize(self):
        """
        Эта функция нормализует список кольцевых устройств, устанавливая предыдущее устройство
        каждого для устройства в списке, кроме головного.
        """
        for i in range(len(self.ring_devs)):
            if i == 0:
                self.ring_devs[i].point.prev_dev = None
                self.ring_devs[i].point.save(update_fields=["prev_dev"])
            else:
                self.ring_devs[i].point.prev_dev = self.ring_devs[i - 1].point
                self.ring_devs[i].point.save(update_fields=["prev_dev"])

        return self


class TransportRingManager(TransportRingBase):
    device_manager = None

    def check_devices_availability(self):
        """
        Эта функция проверяет наличие устройств в списке и обновляет их статус ping.
        :return: список объектов RingPoint, где каждый объект RingPoint имеет логическое значение,
         указывающее доступность устройства, которое он представляет.
        """
        with ThreadPoolExecutor() as ex:
            futures = []
            for point in self.ring_devs:
                # Проверяем пинг
                futures.append(ex.submit(self.ping_point, point=point))

            for i, f in enumerate(futures):
                self.ring_devs[i].ping = f.result()

    @staticmethod
    def ping_point(point: RingPoint):
        # Дважды
        return point.device.available and point.device.available

    def get_device_manager(self):
        """
        Эта функция возвращает диспетчер устройств или вызывает NotImplementedError, если он не определен.
        """
        if not self.device_manager:
            raise NotImplementedError(
                "Необходимо указать device_manager, или переопределить get_device_manager()"
            )
        return self.device_manager

    def collect_all_interfaces(self):
        """
        Эта функция использует ThreadPoolExecutor для сбора всех интерфейсов устройств в кольце.
        """
        with ThreadPoolExecutor() as ex:
            futures = []
            for dev_point in self.ring_devs:
                # Собираем интерфейсы
                futures.append(ex.submit(self.get_device_interfaces, dev_point))

            for i, f in enumerate(futures):
                self.ring_devs[i].interfaces = f.result()

    def get_device_interfaces(self, point: RingPoint) -> Interfaces:
        device_manager = self.get_device_manager()
        dev = device_manager.from_model(point.device, zabbix_info=False)
        # Собираем текущее состояние интерфейсов, если оборудование доступно
        dev.collect_interfaces(vlans=point.collect_vlans, current_status=point.ping)
        return dev.interfaces

    def find_link_between_devices(self):
        length = len(self.ring_devs)

        # Проходимся по кольцу
        for i in range(length):

            # Необходимо пройти два барьера - найти связь с предыдущим устройством и с последующим
            link_with_prev = 1
            link_with_next = 1

            # Текущий элемент
            current_node = self.ring_devs[i]

            # Предыдущий элемент в кольце
            prev_node = self.ring_devs[i - 1]

            increment = 1
            if i == length - 1:
                # Этот код используется для обработки последнего элемента кольца.
                # Когда `i` равно `length - 1`, это означает, что текущий элемент является последним элементом кольца.
                # В этом случае для `increment` устанавливается значение `-i`, что означает, что следующим элементом
                # для проверки будет первый элемент кольца.
                # Это делается для того, чтобы последний элемент был соединен с первым элементом кольца.
                increment = -i

            # Следующий элемент в кольце
            next_node = self.ring_devs[i + increment]

            # Смотрим по очереди интерфейсы на текущем оборудовании
            for interface in current_node.interfaces:
                # Если имя следующего устройства находится в описании на порту текущего
                if next_node.device.name in interface.desc:
                    current_node.port_to_next_dev = interface
                    link_with_next -= 1  # Нашли связь

                # Если имя предыдущего устройства находится в описании на порту текущего
                if prev_node.device.name in interface.desc:
                    current_node.port_to_prev_dev = interface
                    link_with_prev -= 1  # Нашли связь

            # Проверка связи между текущим и следующим оборудованием
            if link_with_next > 0:
                InvalidRingStructure(
                    f"Не удалось найти связь между {current_node.device} и {next_node.device}"
                )
            if link_with_next < 0:
                InvalidRingStructure(
                    f"Найдено {link_with_next} связи между {current_node.device} и {next_node.device}, неоднозначность"
                )

            # Проверка связи между текущим и предыдущим оборудованием
            if link_with_prev > 0:
                InvalidRingStructure(
                    f"Не удалось найти связь между {current_node.device} и {prev_node.device}"
                )
            if link_with_prev < 0:
                InvalidRingStructure(
                    f"Найдено {link_with_prev} связи между {current_node.device} и {prev_node.device}, неоднозначность"
                )

    def check_ring_status(self):
        if not all(point.ping for point in self.ring_devs):
            # Всё оборудование недоступно, проблемы на сети
            return