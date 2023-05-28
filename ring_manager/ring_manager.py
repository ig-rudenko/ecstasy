from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Tuple, Set, Optional

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


class RingStatus:
    def __init__(self, transport_ring_manager: "TransportRingManager"):
        self.transport_ring_manager = transport_ring_manager

        # Последний доступный, перед недоступным со стороны `head`
        self.last_available: Optional[RingPoint] = None
        # Первый недоступный узел в кольце
        self.first_unavailable: Optional[RingPoint] = None
        # Первый доступный узел, после недоступных
        self.first_available_after: Optional[RingPoint] = None
        # Порты со статусом admin down
        self.closed_ports: list = []
        # Обрывы портов
        self.broken_links: list = []

        # VLAN, которые в данный момент имеются на `tail`
        self.tail_current_vlans: Set[int] = set()
        # Требуемые VLAN для разворота кольца
        self.required_vlans: Set[int] = set()

        # VLAN, которые требуются, но уже имеются на `tail`
        self.tail_exists_vlans: Tuple[int] = tuple()

        # VLAN, которые необходимо еще прописать
        self.tail_required_vlans: Tuple[int] = tuple()

        self.solutions = Solutions()

    def _try_to_find_first_unavailable_and_last_available(self, ring_index: int, point: RingPoint):
        """
        Используется для поиска первого недоступного устройства в кольце и последнего доступного со стороны `head`.
        :param ring_index: Позиция переданной точки в кольце.
        :param point: Объект `RingPoint` кольца.
        """
        if self.first_unavailable is None and not point.ping:
            self.first_unavailable = point
            # Также теперь можно определить последний доступный со стороны `head`
            if ring_index != 0:  # Если это не сам `head`
                self.last_available = self.transport_ring_manager.ring_devs[ring_index - 1]

    def _try_to_find_first_available_after_unavailable(self, point: RingPoint):
        """
        Используется для поиска первого доступного устройства после цепочки недоступных устройств в кольце.
        :param point: Объект `RingPoint` кольца.
        """
        if self.first_unavailable is not None and self.first_available_after is None and point.ping:
            self.first_available_after = point

    def _try_to_find_admin_down_ports(self, point: RingPoint):
        """Смотрим какие порты admin down переданного оборудования"""
        if point.port_to_prev_dev and point.ping and point.port_to_prev_dev.is_admin_down:
            self.closed_ports.append({"point": point, "port": point.port_to_prev_dev})
        if point.port_to_next_dev and point.ping and point.port_to_next_dev.is_admin_down:
            self.closed_ports.append({"point": point, "port": point.port_to_next_dev})

    def _try_to_find_broken_links(self, ring_index: int, point: RingPoint):
        """
        Находит обрыв линии.
        :param ring_index: Позиция переданной точки в кольце.
        :param point: Объект `RingPoint` кольца.
        :return:
        """
        # Обрыв?
        if (
            point.port_to_next_dev  # Имеется следующее устройство в кольце
            and point.ping  # Текущее устройство доступно
            and point.port_to_next_dev.is_down  # К следующему link down
            and (
                not self.transport_ring_manager.ring_devs[
                    ring_index + 1
                ].ping  # Следующее оборудование Недоступно
                or self.transport_ring_manager.ring_devs[ring_index + 1].ping  # Либо доступно и ...
                and self.transport_ring_manager.ring_devs[
                    ring_index + 1
                ].port_to_prev_dev.is_down  # ... link down
            )
        ):
            # Нашли обрыв между `self.ring_devs[ring_index]` и `self.ring_devs[ring_index + 1]`
            self.broken_links.append(
                {
                    "from_dev": {
                        "device": point,
                        "port": point.port_to_next_dev,
                    },
                    "to_dev": {
                        "device": self.transport_ring_manager.ring_devs[ring_index + 1],
                        "port": self.transport_ring_manager.ring_devs[
                            ring_index + 1
                        ].port_to_prev_dev,
                    },
                }
            )

    def collect_ring_status(self):
        """
        Просматриваем все устройства в кольце и собираем информацию о его статусе.
        """

        for i, dev in enumerate(self.transport_ring_manager.ring_devs):
            # Используется для поиска первого недоступного устройства в кольце.
            self._try_to_find_first_unavailable_and_last_available(ring_index=i, point=dev)

            self._try_to_find_first_available_after_unavailable(point=dev)

            # Если после цепочки недоступных появляется еще одно недоступное устройство, то видимо проблемы на сети
            # Неопределенность.
            if (
                self.first_unavailable is not None
                and self.first_available_after is not None
                and not dev.ping
            ):
                self.solutions.error(
                    "uncertainty",
                    "После цепочки недоступных появляется еще одно недоступное устройство, видимо проблемы на сети",
                )
                return

            self._try_to_find_admin_down_ports(point=dev)

            self._try_to_find_broken_links(ring_index=i, point=dev)

    def find_multiple_broken_links(self):
        """Находим множественные обрывы в кольце, если такие есть"""
        if len(self.broken_links) > 1:
            # Два обрыва в кольце? Ошибочка!
            message = f"Обнаружено {len(self.broken_links)} обрыва в кольце, фигня какая-то\n"
            for link in self.broken_links:
                message += (
                    f"Между: {link['from_dev']['device'].device} - порт ({link['from_dev']['port'].name})"
                    f" и {link['to_dev']['device'].device} - порт ({link['to_dev']['port'].name})\n"
                )
            self.solutions.error("uncertainty", message)

    def find_multiple_admin_down_ports(self):
        """Находим множественные порты со статусом `admin down` в кольце, если такие есть"""
        if len(self.closed_ports) > 1:
            # Было обнаружено несколько выключенных портов (admin down)
            # Создаем решение - включить порт, который ДАЛЬШЕ всего находится от `head`
            self.solutions.port_set_up(
                device=self.closed_ports[-1]["point"].device,
                port=self.closed_ports[-1]["port"].name,
                message="Было обнаружено несколько выключенных портов, открываем один из них",
            )

    def find_tail_vlans(self):
        # Определим множества для имеющихся VLAN на `tail` и требуемых
        self.tail_current_vlans = set(self.transport_ring_manager.tail.port_to_prev_dev.vlan)
        self.required_vlans = set(self.transport_ring_manager.vlans)

        # VLAN, которые требуются, но уже имеются на `tail`
        self.tail_exists_vlans = tuple(self.required_vlans & self.tail_current_vlans)

        # VLAN, которые необходимо еще прописать
        self.tail_required_vlans = tuple(self.required_vlans - self.tail_current_vlans)

    def _compute_if_tail_required_vlans(self):
        """
        Если есть VLANS, которые необходимо прописать на `tail`
        """

        # Если все оборудование доступно
        if self.first_unavailable is None and self.first_available_after is None:
            # Если имеется закрытый порт (admin down)
            if len(self.closed_ports):
                self.solutions.info(
                    "Все оборудование доступно, но имеется закрытый порт! "
                    "Убедитесь, что линия исправна, ведь дальнейшие действия развернут кольцо "
                    "в штатное состояние"
                )

                # Если на `tail` есть некоторые VLANS
                if self.tail_exists_vlans:
                    # Необходимо удалить их
                    self.solutions.delete_vlans(
                        vlans=tuple(self.required_vlans),
                        device=self.transport_ring_manager.tail.device,
                        port=self.transport_ring_manager.tail.port_to_prev_dev.name,
                        message=f"Будут удалены VLAN - {self.required_vlans} на "
                        f"{self.transport_ring_manager.tail.device} "
                        f"на порту {self.transport_ring_manager.tail.port_to_prev_dev.name}",
                    )

                # Создаем решение - включить порт
                self.solutions.port_set_up(
                    device=self.closed_ports[0]["point"].device,
                    port=self.closed_ports[0]["port"].name,
                    message="Переводим кольцо в штатное состояние",
                )
                return

            # Если нашли обрыв, то надо закрыть порт со стороны `head`
            elif len(self.broken_links) == 1:
                b_link = self.broken_links[0]

                self.solutions.port_set_down(
                    device=self.broken_links[0]["from_dev"]["device"].device,
                    port=self.broken_links[0]["from_dev"]["port"].name,
                    message="Нашли обрыв между: "
                    f"{b_link['from_dev']['device'].device} - порт ({b_link['from_dev']['port'].name})"
                    f" и {b_link['to_dev']['device'].device} - порт ({b_link['to_dev']['port'].name})",
                )
            else:
                # Если на `tail` есть некоторые VLANS
                if self.tail_exists_vlans:
                    self.solutions.info(
                        "Кольцо находится в исправном состоянии, но необходимо удалить зацикленные "
                        "VLANS"
                    )
                    # Необходимо удалить их
                    self.solutions.delete_vlans(
                        vlans=tuple(self.required_vlans),
                        device=self.transport_ring_manager.tail.device,
                        port=self.transport_ring_manager.tail.port_to_prev_dev.name,
                        message=f"Будут удалены VLAN - {self.required_vlans} на"
                        f" {self.transport_ring_manager.tail.device} "
                        f"на порту {self.transport_ring_manager.tail.port_to_prev_dev.name}",
                    )
                self.solutions.info("Кольцо находится в исправном состоянии")
                return

        # Если имеется некоторое недоступное оборудование и есть VLANS, которые необходимо прописать на `tail`.
        else:
            # Если имеется закрытый порт
            if len(self.closed_ports):
                pass

            # Если нет закрытых портов, то надо закрыть
            else:
                # Со стороны первого доступного, ПЕРЕД недоступными в сторону `tail`
                self.solutions.port_set_down(
                    device=self.last_available.device,
                    port=self.last_available.port_to_next_dev.name,
                    message="Закрываем порт в сторону tail, готовимся разворачивать кольцо",
                )

        # Разворачиваем кольцо - прописываем VLANS на `tail`
        self.solutions.add_vlans(
            vlans=tuple(self.tail_required_vlans),
            device=self.transport_ring_manager.tail.device,
            port=self.transport_ring_manager.tail.port_to_prev_dev.name,
            message=f"Прописываем VLANS {self.tail_required_vlans} на {self.transport_ring_manager.tail.device} "
            f"на порту {self.transport_ring_manager.tail.port_to_prev_dev.name}",
        )

    def _compute_if_tail_has_vlans(self):
        """
        Если на `tail` уже не требуется прописывать никакие VLAN, значит кольцо развернуто
        """

        # Если кольцо развернуто и никакие порты не были закрыты, и нет обрыва
        # тогда необходимо убрать VLANS с порта `tail`.
        # Так как по штатному состоянию VLAN должны идти c `head`
        if len(self.closed_ports) == 0 and len(self.broken_links) == 0:
            self.solutions.delete_vlans(
                vlans=tuple(self.required_vlans),
                device=self.transport_ring_manager.tail.device,
                port=self.transport_ring_manager.tail.port_to_prev_dev.name,
                message=f"Если в кольце все исправно, то надо убрать VLANS {self.required_vlans} "
                f"на {self.transport_ring_manager.tail.device} на порту"
                f" {self.transport_ring_manager.tail.port_to_prev_dev.name}",
            )

        # Имеется закрытый порт и все оборудование доступно, можно развернуть в штатное состояние
        elif (
            len(self.closed_ports)
            and self.first_unavailable is None
            and self.first_available_after is None
        ):
            self.solutions.info(
                f"Транспортное кольцо в данный момент развернуто, со стороны"
                f" {self.transport_ring_manager.tail.device.name} "
                "Убедитесь, что линия исправна, ведь дальнейшие действия развернут кольцо "
                "в штатное состояние"
            )
            self.solutions.delete_vlans(
                vlans=tuple(self.required_vlans),
                device=self.transport_ring_manager.tail.device,
                port=self.transport_ring_manager.tail.port_to_prev_dev.name,
                message=f"Сначала будут удалены VLAN'ы {self.required_vlans} на оборудовании "
                f"{self.transport_ring_manager.tail.device} на порту "
                f"{self.transport_ring_manager.tail.port_to_prev_dev.name}",
            )
            self.solutions.port_set_up(
                device=self.closed_ports[0]["point"].device,
                port=self.closed_ports[0]["port"].name,
                message="Переводим кольцо в штатное состояние",
            )

        # Если имеется НЕ закрытый порт, а также некоторые недоступные оборудования в кольце
        elif len(self.closed_ports) == 0 and self.first_unavailable and self.first_available_after:
            # Если нет закрытых портов, то надо закрыть
            # Со стороны первого доступного, ПЕРЕД недоступными в сторону `tail`
            self.solutions.port_set_down(
                device=self.last_available.device,
                port=self.last_available.port_to_next_dev.name,
                message="Закрываем порт в сторону tail, готовимся разворачивать кольцо",
            )

        # Если есть обрыв
        elif len(self.broken_links):
            b_link = self.broken_links[0]

            self.solutions.port_set_down(
                device=self.broken_links[0]["from_dev"]["device"].device,
                port=self.broken_links[0]["from_dev"]["port"].name,
                message="Нашли обрыв между: "
                f"{b_link['from_dev']['device'].device} - порт ({b_link['from_dev']['port'].name})"
                f" и {b_link['to_dev']['device'].device} - порт ({b_link['to_dev']['port'].name})",
            )

    def compute_solutions(self):
        """
        По ранее собранной информации о кольце вычисляем какие необходимо выполнить решения.
        """

        # Смотрим, есть ли VLANS, которые необходимо прописать на `tail`
        if self.tail_required_vlans:
            self._compute_if_tail_required_vlans()

        # Если на `tail` уже не требуется прописывать никакие VLAN, значит кольцо развернуто
        else:
            self._compute_if_tail_has_vlans()


class TransportRingManager:
    device_manager = DeviceManager

    def __init__(self, ring: TransportRing):
        self._validate_ring(ring)

        self.ring = ring
        self.vlans: List[int] = ring.vlans
        self.ring_devs = self._get_ring_devices()

        self.head = self.ring_devs[0]
        self.tail = self.ring_devs[-1]

        # Интерфейсы и VLANs необходимо собирать только у `head` и `tail`
        self.head.collect_vlans = True
        self.tail.collect_vlans = True

        # Состояние кольца
        self._ring_status = RingStatus(transport_ring_manager=self)

    def get_device_manager(self):
        """
        Эта функция возвращает диспетчер устройств или вызывает NotImplementedError, если он не определен.
        """
        if not self.device_manager:
            raise NotImplementedError(
                "Необходимо указать device_manager, или переопределить get_device_manager()"
            )
        return self.device_manager

    def normalize(self) -> None:
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

    def check_devices_availability(self):
        """
        Эта функция проверяет наличие устройств в списке и обновляет их статус ping.
        :return: Список объектов RingPoint, где каждый объект RingPoint имеет логическое значение,
         указывающее доступность устройства, которое он представляет.
        """
        with ThreadPoolExecutor() as ex:
            futures = []
            for point in self.ring_devs:
                # Проверяем пинг
                futures.append(ex.submit(self._ping_point, point=point))

            for i, f in enumerate(futures):
                self.ring_devs[i].ping = f.result()

    def collect_all_interfaces(self):
        """
        Эта функция использует ThreadPoolExecutor для сбора всех интерфейсов устройств в кольце.
        """
        with ThreadPoolExecutor() as ex:
            futures = []
            for dev_point in self.ring_devs:
                # Собираем интерфейсы
                futures.append(ex.submit(self._get_device_interfaces, dev_point))

            for i, f in enumerate(futures):
                self.ring_devs[i].interfaces = f.result()

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

    def create_solutions(self) -> Solutions:
        """
        Создает решения, которые необходимо сделать с кольцом, чтобы достичь оптимального состояния

        :return: Список решений
        """

        self._check_ring_before_compute_solutions()

        self._ring_status.collect_ring_status()

        self._ring_status.find_multiple_broken_links()
        self._ring_status.find_multiple_admin_down_ports()

        if self._ring_status.solutions.has_errors:
            return self._ring_status.solutions

        self._ring_status.find_tail_vlans()

        self._ring_status.compute_solutions()

        return self._ring_status.solutions

    def _get_device_interfaces(self, point: RingPoint) -> Interfaces:
        device_manager = self.get_device_manager()
        dev = device_manager.from_model(point.device, zabbix_info=False)
        # Собираем текущее состояние интерфейсов, если оборудование доступно
        dev.collect_interfaces(vlans=point.collect_vlans, current_status=point.ping)
        return dev.interfaces

    @staticmethod
    def _validate_ring(ring):
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

    def _get_ring_devices(self) -> List[RingPoint]:
        """
        Функция «ring_devices» возвращает список устройств в кольце по порядку
        """
        last_device = self.ring.tail

        devs = []

        iter_dev: RingDev = self.ring.head

        # Перебирает устройства в кольце и добавляет в список.
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

    @staticmethod
    def _ping_point(point: RingPoint):
        # Дважды
        return point.device.available and point.device.available

    def _check_ring_before_compute_solutions(self):
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
