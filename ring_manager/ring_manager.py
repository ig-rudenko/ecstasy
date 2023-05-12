from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Tuple, Set

from devicemanager.device import Interfaces, Interface, DeviceManager
from check import models
from .models import RingDev, TransportRing
from .solutions import Solutions


class InvalidRingStructureError(Exception):
    def __init__(self, message: str):
        self.message = message


class RingStatusError(Exception):
    def __init__(self, message: str):
        self.message = message


@dataclass
class RingPoint:
    device: models.Devices
    point: RingDev
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
        self.vlans: List[int] = ring.vlans
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

        iter_dev: RingDev = self.ring.head

        # Перебирает устройства в кольце и добавляет в список
        # Начинается с головного устройства кольца и продолжается добавление пока не достигнет конца кольца
        # (т. е. атрибут next_dev текущего устройства равен None).
        while True:
            devs.append(RingPoint(point=iter_dev, device=iter_dev.device))
            if iter_dev.next_dev is None:
                break

            if iter_dev == iter_dev.next_dev:
                raise InvalidRingStructureError(
                    f"Устройство {iter_dev.device} на позиции ({len(devs)}) в кольце ссылается само на себя"
                )

            iter_dev = iter_dev.next_dev

            if len(devs) > 100:
                raise InvalidRingStructureError(
                    f"Превышен лимит (100) устройств в кольце. "
                    f"Вероятно образовалась ссылочная петля и устройства в кольце ссылаются друг на друга"
                )

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

            elif self.ring_devs[i].point.prev_dev != self.ring_devs[i - 1].point:
                self.ring_devs[i].point.prev_dev = self.ring_devs[i - 1].point
                self.ring_devs[i].point.save(update_fields=["prev_dev"])

        return self


class TransportRingManager(TransportRingBase):
    device_manager = DeviceManager

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

    def _check_ring_status(self):
        if all(not point.ping for point in self.ring_devs):
            # Всё оборудование недоступно, проблемы на сети
            raise RingStatusError("Все устройства в кольце недоступны")

        # Если недоступно `head` устройство
        if not self.head.ping:
            raise RingStatusError(f"Головное устройство {self.head.device} в кольце недоступно")

        # Если недоступно `tail` устройство
        if not self.tail.ping:
            raise RingStatusError(f"Конечное устройство {self.tail.device} в кольце недоступно")

        # Проверяем, находятся ли указанные для данного кольца VLAN на головном устройстве
        # Ведь на нем они должны находиться всегда
        # Разница VLAN
        diff = set(self.vlans) - set(self.head.port_to_next_dev.vlan)
        if diff:
            raise RingStatusError(
                f"Указанные для разворота VLAN: {diff} "
                f"отсутствуют на порту ({self.head.port_to_next_dev}) "
                f"головного устройства {self.head.device}"
            )

    def create_solutions(self) -> Solutions:
        """
        Создает решения, которые необходимо сделать с кольцом, чтобы достичь оптимального состояния

        :return: Список решений
        """

        self._check_ring_status()

        SOLUTIONS = Solutions()

        # Последний доступный, перед недоступным сос стороны `head`
        last_available = None
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
                # Также теперь можно определить последний доступный со стороны `head`
                if i:  # Если это не сам `head`
                    last_available = self.ring_devs[i - 1]

            # Используется для поиска первого доступного устройства
            # после цепочки недоступных устройств в кольце.
            if first_unavailable is not None and first_available_after is None and dev.ping:
                first_available_after = dev

            # Если после цепочки недоступных появляется еще одно недоступное устройство, то видимо проблемы на сети
            # Неопределенность.
            if first_unavailable is not None and first_available_after is not None and not dev.ping:
                SOLUTIONS.error(
                    "uncertainty",
                    "После цепочки недоступных появляется еще одно недоступное устройство, видимо проблемы на сети",
                )
                return SOLUTIONS

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

            SOLUTIONS.error("uncertainty", message)

            return SOLUTIONS

        # ================== ADMIN DOWN PORTS ==================

        # Было обнаружено несколько выключенных портов (admin down)
        if len(closed_ports) == 2:
            # Создаем решение - включить порт, который ДАЛЬШЕ всего находится от `head`
            SOLUTIONS.port_set_up(
                device=closed_ports[-1]["point"].device,
                port=closed_ports[-1]["port"].name,
                message="Было обнаружено несколько выключенных портов, открываем один из них",
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

                    SOLUTIONS.info(
                        "Все оборудование доступно, но имеется закрытый порт! "
                        "Убедитесь, что линия исправна, ведь дальнейшие действия развернут кольцо "
                        "в штатное состояние"
                    )

                    # Если на `tail` есть некоторые VLANS
                    if tail_exists_vlans:
                        # Необходимо удалить их
                        SOLUTIONS.delete_vlans(
                            vlans=tuple(required_vlans),
                            device=self.tail.device,
                            port=self.tail.port_to_prev_dev.name,
                            message=f"Будут удалены VLAN - {required_vlans} на {self.tail.device} "
                            f"на порту {self.tail.port_to_prev_dev.name}",
                        )

                    # Создаем решение - включить порт
                    SOLUTIONS.port_set_up(
                        device=closed_ports[0]["point"].device,
                        port=closed_ports[0]["port"].name,
                        message="Переводим кольцо в штатное состояние",
                    )
                    return SOLUTIONS

                # Если нашли обрыв, то надо закрыть порт со стороны `head`
                elif len(broken_links) == 1:
                    b_link = broken_links[0]

                    SOLUTIONS.port_set_down(
                        device=broken_links[0]["from_dev"]["device"].device,
                        port=broken_links[0]["from_dev"]["port"].name,
                        message="Нашли обрыв между: "
                        f"{b_link['from_dev']['device'].device} - порт ({b_link['from_dev']['port'].name})"
                        f" и {b_link['to_dev']['device'].device} - порт ({b_link['to_dev']['port'].name})",
                    )
                else:
                    # Если на `tail` есть некоторые VLANS
                    if tail_exists_vlans:
                        SOLUTIONS.info(
                            "Кольцо находится в исправном состоянии, но необходимо удалить зацикленные "
                            "VLANS"
                        )
                        # Необходимо удалить их
                        SOLUTIONS.delete_vlans(
                            vlans=tuple(required_vlans),
                            device=self.tail.device,
                            port=self.tail.port_to_prev_dev.name,
                            message=f"Будут удалены VLAN - {required_vlans} на {self.tail.device} "
                            f"на порту {self.tail.port_to_prev_dev.name}",
                        )
                    SOLUTIONS.info("Кольцо находится в исправном состоянии")
                    return SOLUTIONS

            # Если имеется некоторое недоступное оборудование и есть VLANS, которые необходимо прописать на `tail`.
            else:

                # Если имеется закрытый порт
                if len(closed_ports):
                    pass

                # Если нет закрытых портов, то надо закрыть
                else:
                    # Со стороны первого доступного, ПЕРЕД недоступными в сторону `tail`
                    SOLUTIONS.port_set_down(
                        device=last_available.device,
                        port=last_available.port_to_next_dev.name,
                        message="Закрываем порт в сторону tail, готовимся разворачивать кольцо",
                    )

            # Разворачиваем кольцо - прописываем VLANS на `tail`
            SOLUTIONS.add_vlans(
                vlans=tuple(tail_required_vlans),
                device=self.tail.device,
                port=self.tail.port_to_prev_dev.name,
                message=f"Прописываем VLANS {tail_required_vlans} на {self.tail.device} "
                f"на порту {self.tail.port_to_prev_dev.name}",
            )

        # Если на `tail` уже не требуется прописывать никакие VLAN, значит кольцо развернуто
        else:

            # Если кольцо развернуто и никакие порты не были закрыты, и нет обрыва
            # тогда необходимо убрать VLANS с порта `tail`.
            # Так как по штатному состоянию VLAN должны идти c `head`
            if len(closed_ports) == 0 and len(broken_links) == 0:

                SOLUTIONS.delete_vlans(
                    vlans=tuple(required_vlans),
                    device=self.tail.device,
                    port=self.tail.port_to_prev_dev.name,
                    message=f"Если в кольце все исправно, то надо убрать VLANS {required_vlans} "
                    f"на {self.tail.device} на порту {self.tail.port_to_prev_dev.name}",
                )

            # Имеется закрытый порт и все оборудование доступно, можно развернуть в штатное состояние
            elif len(closed_ports) and first_unavailable is None and first_available_after is None:
                SOLUTIONS.info(
                    f"Транспортное кольцо в данный момент развернуто, со стороны {self.tail.device.name} "
                    "Убедитесь, что линия исправна, ведь дальнейшие действия развернут кольцо "
                    "в штатное состояние"
                )
                SOLUTIONS.delete_vlans(
                    vlans=tuple(required_vlans),
                    device=self.tail.device,
                    port=self.tail.port_to_prev_dev.name,
                    message=f"Сначала будут удалены VLAN'ы {required_vlans} на оборудовании "
                    f"{self.tail.device} на порту {self.tail.port_to_prev_dev.name}",
                )
                SOLUTIONS.port_set_up(
                    device=closed_ports[0]["point"].device,
                    port=closed_ports[0]["port"].name,
                    message="Переводим кольцо в штатное состояние",
                )

            # Если имеется НЕ закрытый порт, а также некоторые недоступные оборудования в кольце
            elif len(closed_ports) == 0 and first_unavailable and first_available_after:
                # Если нет закрытых портов, то надо закрыть
                # Со стороны первого доступного, ПЕРЕД недоступными в сторону `tail`
                SOLUTIONS.port_set_down(
                    device=last_available.device,
                    port=last_available.port_to_next_dev.name,
                    message="Закрываем порт в сторону tail, готовимся разворачивать кольцо",
                )

            # Если есть обрыв
            elif len(broken_links):
                b_link = broken_links[0]

                SOLUTIONS.port_set_down(
                    device=broken_links[0]["from_dev"]["device"].device,
                    port=broken_links[0]["from_dev"]["port"].name,
                    message="Нашли обрыв между: "
                    f"{b_link['from_dev']['device'].device} - порт ({b_link['from_dev']['port'].name})"
                    f" и {b_link['to_dev']['device'].device} - порт ({b_link['to_dev']['port'].name})",
                )

        return SOLUTIONS
