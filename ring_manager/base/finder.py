from typing import List

from .types import BaseRingPoint
from .exceptions import InvalidRingStructureError


def find_links_between_points(ring_devs: List[BaseRingPoint]):
    length = len(ring_devs)

    # Проходимся по кольцу
    for i in range(length):
        # Необходимо пройти два барьера - найти связь с предыдущим устройством и с последующим
        link_with_prev = 1
        link_with_next = 1

        # Текущий элемент
        current_node = ring_devs[i]

        # Предыдущий элемент в кольце
        prev_node = ring_devs[i - 1]

        increment = 1
        if i == length - 1:
            # Этот код используется для обработки последнего элемента кольца.
            # Когда `i` равно `length - 1`, это означает, что текущий элемент является последним элементом кольца.
            # В этом случае для `increment` устанавливается значение `-i`, что означает, что следующим элементом
            # для проверки будет первый элемент кольца.
            # Это делается для того, чтобы последний элемент был соединен с первым элементом кольца.
            increment = -i

        # Следующий элемент в кольце
        next_node = ring_devs[i + increment]

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
