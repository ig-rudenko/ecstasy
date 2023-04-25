from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Tuple, Dict, Set

from devicemanager.device import Interfaces, Interface
from check import models
from .models import RingDevs, TransportRing


class InvalidRingStructureError(Exception):
    pass


class RingStatusError(Exception):
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
            raise TypeError(
                f"Менеджер колец не принимает тип {type(ring)}, только `model.TransportRing`"
            )

        if ring.head is None:
            raise InvalidRingStructureError("В кольце не указано головное устройство")

        if ring.tail is None:
            raise InvalidRingStructureError("В кольце не указано замыкающее устройство")

        if not ring.vlans:
            raise InvalidRingStructureError("Для разворота требуется указать VLAN")

    def __init__(self, ring: TransportRing):
        self.validate_ring(ring)

        self.ring = ring
        self.vlans = ring.vlans
        self.ring_devs = self.ring_devices()

        self.head = self.ring_devs[0]
        self.tail = self.ring_devs[-1]

        # Интерфейсы и VLANs необходимо собирать только у `head` и `tail`
        self.head.collect_vlans = True
        self.tail.collect_vlans = True

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
            raise InvalidRingStructureError(
                f"Кольцо замыкается на устройстве ({iter_dev.device}), а  требуется ({last_device.device})"
            )

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
                InvalidRingStructureError(
                    f"Не удалось найти связь между {current_node.device} и {next_node.device}"
                )
            if link_with_next < 0:
                InvalidRingStructureError(
                    f"Найдено {link_with_next} связи между {current_node.device} и {next_node.device}, неоднозначность"
                )

            # Проверка связи между текущим и предыдущим оборудованием
            if link_with_prev > 0:
                InvalidRingStructureError(
                    f"Не удалось найти связь между {current_node.device} и {prev_node.device}"
                )
            if link_with_prev < 0:
                InvalidRingStructureError(
                    f"Найдено {link_with_prev} связи между {current_node.device} и {prev_node.device}, неоднозначность"
                )

    def check_ring_status(self):
        if not all(not point.ping for point in self.ring_devs):
            # Всё оборудование недоступно, проблемы на сети
            raise RingStatusError("Все устройства в кольце недоступны")

        # Если недоступно `tail` устройство
        if not self.tail.ping:
            raise RingStatusError(f"Конечное устройство {self.tail.device} в кольце недоступно")

        # Проверяем, находятся ли указанные для данного кольца VLAN на головном устройстве
        # Ведь на нем они должны находиться всегда
        # Разница VLAN
        diff = set(self.vlans) - set(self.head.port_to_next_dev.vlan)
        if diff:
            raise RingStatusError(
                f"Указанные для разворота VLAN: {diff} отсутствуют на порту ({self.head.port_to_next_dev})"
                f" головного устройства {self.head.device}"
            )

    def create_solutions(self) -> Tuple[Dict[str, ...], ...]:
        """
        Создает решения, которые необходимо сделать с кольцом, чтобы достичь оптимального состояния

        :return: Список решений
        """

        SOLUTIONS = []

        # Первый недоступный узел в кольце
        first_unavailable = None
        # Первый доступный узел, после недоступных
        first_available_after = None

        # Вместе с этим смотрим, какие порты закрыты в кольце, либо нет таких вообще
        closed_ports = []
        # А также, какие порты имеют link down, в случае обрыва
        broken_links = []

        for i, dev in enumerate(self.ring_devs):

            # Используется для поиска первого недоступного устройства в кольце.
            if first_unavailable is None and not dev.ping:
                first_unavailable = dev

            # Используется для поиска первого доступного устройства
            # после цепочки недоступных устройств в кольце.
            if first_unavailable is not None and dev.ping:
                first_available_after = dev

            # Если после цепочки недоступных появляется еще одно недоступное устройство, то видимо проблемы на сети
            # Неопределенность.
            if first_unavailable is not None and first_available_after is not None and not dev.ping:
                return (
                    {
                        "error": {
                            "status": "uncertainty",
                            "message": "После цепочки недоступных появляется еще одно недоступное устройство, "
                            "видимо проблемы на сети",
                        }
                    },
                )

            # Смотрим какие порты admin down (у доступного оборудования)
            if dev.port_to_prev_dev and dev.ping and dev.port_to_prev_dev.is_admin_down:
                closed_ports.append({"point": dev, "port": dev.port_to_prev_dev})
            if dev.port_to_next_dev and dev.ping and dev.port_to_next_dev.is_admin_down:
                closed_ports.append({"point": dev, "port": dev.port_to_next_dev})

            # Обрыв?
            if (
                dev.port_to_next_dev  # Имеется следующее устройство в кольце
                and dev.ping  # Текущее устройство доступно
                and dev.port_to_next_dev.is_down  # К следующему link down
                and (
                    not self.ring_devs[i + 1].ping  # Следующее оборудование Недоступно
                    or self.ring_devs[i + 1].ping  # Либо доступно и ...
                    and self.ring_devs[i + 1].port_to_prev_dev.is_down  # ... link down
                )
            ):
                # Нашли обрыв между `self.ring_devs[i]` и `self.ring_devs[i + 1]`
                broken_links.append(
                    {
                        "from_dev": {
                            "device": dev,
                            "port": dev.port_to_next_dev,
                        },
                        "to_dev": {
                            "device": self.ring_devs[i + 1],
                            "port": self.ring_devs[i + 1].port_to_prev_dev,
                        },
                    }
                )

        # ================= BROKEN LINKS =====================

        if len(broken_links) > 1:
            # Два обрыва в кольце? Ошибочка!

            message = f"Обнаружено {len(broken_links)} обрыва в кольце, фигня какая-то\n"
            for link in broken_links:
                message += (
                    f"Между: {link['from_dev']['device'].device} - порт ({link['from_dev']['port'].name})"
                    f" и {link['to_dev']['device'].device} - порт ({link['to_dev']['port'].name})\n"
                )

            return (
                {
                    "error": {
                        "status": "uncertainty",
                        "message": message,
                    }
                },
            )

        # ================== ADMIN DOWN PORTS ==================

        # Было обнаружено несколько выключенных портов (admin down)
        if len(closed_ports) == 2:
            # Создаем решение - включить порт, который ДАЛЬШЕ всего находится от `head`
            SOLUTIONS.append(
                {
                    "set_port_status": {
                        "status": "up",
                        "device": closed_ports[-1]["point"].device,
                        "port": closed_ports[-1]["port"].name,
                        "message": "Было обнаружено несколько выключенных портов, открываем один из них",
                    }
                }
            )

        # =================== SET PORT STATUS DOWN =====================

        if len(closed_ports) == 0 and len(broken_links) == 1:
            # Если нашли обрыв, то надо закрыть порт со стороны `head`

            b_link = broken_links[0]
            message = (
                f"Нашли обрыв между: {b_link['from_dev']['device'].device} - порт ({b_link['from_dev']['port'].name})"
                f" и {b_link['to_dev']['device'].device} - порт ({b_link['to_dev']['port'].name})\n"
            )

            SOLUTIONS.append(
                {
                    "set_port_status": {
                        "status": "down",
                        "device": broken_links[0]["from_dev"]["device"].device,
                        "port": broken_links[0]["from_dev"]["port"].name,
                        "message": message,
                    }
                }
            )

        # После того, как определили границы недоступных устройств, посмотрим какие VLAN уже прописаны на `tail`.

        # ================== VLANS REQUIRED ====================

        # Определим множества для имеющихся VLAN на `tail` и требуемых
        tail_current_vlans: Set[int] = set(self.tail.port_to_prev_dev.vlan)
        required_vlans: Set[int] = set(self.vlans)

        # VLAN, которые требуются, но уже имеются на `tail`
        tail_exists_vlans: Tuple[int] = tuple(required_vlans & tail_current_vlans)

        # VLAN, которые необходимо еще прописать
        tail_required_vlans: Tuple[int] = tuple(required_vlans - tail_current_vlans)

        # ==================== COMPLEX DEFINITION =======================

        # Смотрим, есть ли VLANS, которые необходимо прописать на `tail`
        if tail_required_vlans:

            # Если все оборудование доступно
            if first_available_after is None and first_available_after is None:

                # Если имеется закрытый порт (admin down)
                if len(closed_ports):

                    SOLUTIONS.append(
                        {
                            "info": {
                                "message": "Все оборудование доступно, но имеется закрытый порт! "
                                "Убедитесь, что линия исправна, ведь дальнейшие действия развернут кольцо "
                                "в штатное состояние",
                            }
                        }
                    )

                    # Если на `tail` есть некоторые VLANS
                    if tail_exists_vlans:
                        # Необходимо удалить их
                        SOLUTIONS.append(
                            {
                                "set_port_vlans": {
                                    "status": "delete",
                                    "vlans": tuple(required_vlans),
                                    "device": self.tail.device,
                                    "port": self.tail.port_to_prev_dev.name,
                                }
                            }
                        )

                    # Создаем решение - включить порт, который ДАЛЬШЕ всего находится от `head`
                    SOLUTIONS.append(
                        {
                            "set_port_status": {
                                "status": "up",
                                "device": closed_ports[-1]["point"].device,
                                "port": closed_ports[-1]["port"].name,
                                "message": "Было обнаружено несколько выключенных портов, открываем один из них",
                            }
                        }
                    )

        # Если на `tail` уже не требуется прописывать никакие VLAN, значит кольцо развернуто
        else:

            # Если кольцо развернуто и никакие порты не были закрыты, и нет обрыва
            # тогда необходимо убрать VLANS с порта `tail`.
            # Так как по штатному состоянию VLAN должны идти c `head`
            if len(closed_ports) == 0 and len(broken_links) == 0:
                SOLUTIONS.append(
                    {
                        "set_port_vlans": {
                            "status": "delete",
                            "vlans": tuple(required_vlans),
                            "device": self.tail.device,
                            "port": self.tail.port_to_prev_dev.name,
                        }
                    }
                )

            # Если имеется закрытый порт, а также некоторые недоступные оборудования в кольце
            elif len(closed_ports) and first_unavailable and first_available_after:
                # Кольцо развернуто, но некоторое оборудование не поднялось,
                # возможна проблема на линии, либо в оборудовании
                pass

        return tuple(SOLUTIONS)
