import re
from collections.abc import Sequence
from dataclasses import dataclass, field

import tabulate

from devicemanager.vendors.base.helpers import range_to_numbers
from ecstasy_project.settings import NON_ABON_INTERFACES_PATTERN


@dataclass
class Interface:
    name: str = ""
    status: str = ""
    desc: str = ""
    vlan: list = field(default_factory=list)

    @property
    def has_desc(self):
        if "HUAWEI, Quidway Series" in self.desc:
            return False

        return len(self.desc.strip()) > 1

    @property
    def is_up(self) -> bool:
        status = self.status.lower()
        return "down" not in status and "disable" not in status and "dormant" not in status

    @property
    def is_admin_down(self) -> bool:
        status = self.status.lower()
        return "admin" in status or "disable" in status

    @property
    def is_down(self) -> bool:
        return not self.is_up and not self.is_admin_down


class Interfaces:
    """
    Взаимодействие с интерфейсами оборудования

    >>> Interfaces(['eth1', 'up', 'description', [10, 20]])

    >>> Interfaces([{"Interface": "eth1", "Status": "up", "Description": "desc", "VLAN's": [10, 20]}])

    >>> Interfaces([{"name": "eth1", "status": "up", "description": "desc", "vlans": [10, 20]}])

    >>> Interfaces([{'Interface': '1', 'Admin Status': 'up', 'Link': 'up', 'Description': 'desc', "VLAN's": [1, 2]}])

    >>> Interfaces([Interface()])
    """

    def __init__(self, data: Sequence | None = None):
        self.__interfaces: list[Interface] = []
        if not data:  # Если не были переданы интерфейсы
            return

        for intf in data:
            # Если был передан словарь
            if isinstance(intf, dict):
                if (
                    intf.get("Status") is None
                    and intf.get("status") is None
                    and intf.get("Admin Status")
                    and intf.get("Link")
                ):
                    # Преобразование из старого формата
                    status = "admin down" if intf["Admin Status"] == "down" else intf["Link"]
                else:
                    status = intf.get("Status", "") or intf.get("status", "")

                interface_name: str = intf.get("Interface", "") or intf.get("name", "")
                interface_desc: str = intf.get("Description", "") or intf.get("description", "")
                vlans: list = intf.get("VLAN's", []) or intf.get("vlans", [])

                self.__interfaces.append(
                    Interface(
                        name=interface_name.strip(),
                        status=status.strip(),
                        desc=interface_desc.strip(),
                        vlan=self._parse_vlans_line(vlans),
                    )
                )

            # Если был передан список, кортеж
            elif isinstance(intf, (list, tuple)):
                if len(intf) == 3:  # Без VLAN
                    self.__interfaces.append(Interface(intf[0].strip(), intf[1], intf[2].strip(), []))
                elif len(intf) == 4:  # + VLAN
                    self.__interfaces.append(
                        Interface(
                            intf[0].strip(),
                            intf[1],
                            intf[2].strip(),
                            self._parse_vlans_line(intf[3]),
                        )
                    )

            # Если был передан объект Interface
            elif isinstance(intf, Interface):
                self.__interfaces.append(intf)

    def __str__(self):
        if not self.__interfaces:
            return "None"
        return tabulate.tabulate(
            [
                [
                    i.name,
                    i.status,
                    i.desc.strip(),
                    ", ".join(map(str, i.vlan)) or " " if i.vlan else " ",
                ]
                for i in self.__interfaces
            ],
            headers=["Interface", "Status", "Description", "VLAN"],
            maxcolwidths=[None, None, None, 40],
            tablefmt="simple",
        )

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, Interfaces):
            return self.__interfaces == other.__interfaces
        raise TypeError(f"Нельзя сравнивать интерфейсы с типом `{type(other)}`")

    def __getitem__(self, item):
        """Обращение к интерфейсам"""
        if not self.__interfaces:
            # Если не существует интерфейсов, то возвращаем пустой, чтобы не было ошибки
            return Interface()
        if isinstance(item, int):
            return self.__interfaces[item]
        if isinstance(item, str):
            for i in self.__interfaces:
                if i.name == item:
                    return i
        return Interface()

    def __enter__(self):
        return self.__interfaces

    def __iter__(self):
        return iter(self.__interfaces)

    def __bool__(self):
        return bool(self.__interfaces)

    @property
    def count(self) -> int:
        """Количество интерфейсов"""
        return len(self.__interfaces)

    def json(self):
        return [
            {
                "name": line.name,
                "status": line.status,
                "description": line.desc,
                "vlans": line.vlan,
            }
            for line in self.__interfaces
        ]

    def physical(self):
        res = []
        i = 0
        intf = self.__interfaces

        while i < len(intf):
            # Комбо-порт. Надо выбрать один.
            if (
                "(C)" in intf[i].name
                and "(F)" in intf[i + 1].name
                and re.findall(r"^\d+", intf[i].name) == re.findall(r"^\d+", intf[i].name)
            ):
                # Выбираем, какой комбо порт добавить.
                # Смотрим состояние и добавляем активный.
                combo_interface = intf[i] if intf[i].is_up else intf[i + 1]
                # Выбираем описание комбо порта, если нет на (C), то берем с (F).
                combo_interface.desc = intf[i].desc if intf[i].has_desc else intf[i + 1].desc
                res.append(combo_interface)
                i += 2  # Пропускаем 2 комбо-порта.

            else:
                # Добавляем обычные порты.
                res.append(intf[i])
                i += 1

        return Interfaces(res)

    def up(self, only_count=False):
        """
        Интерфейсы, состояние которых UP

        :param only_count: bool Только кол-во?
        """
        count = 0
        intf = []
        for i in self.__interfaces:
            if i.is_up:
                count += 1
                if not only_count:
                    intf.append(i)
        return count if only_count else Interfaces(intf)

    def with_description(self, only_count=False):
        """
        Интерфейсы, на которых есть описание
        :param only_count: bool Только кол-во?
        """
        count = 0
        intf = []
        for i in self.__interfaces:
            if i.has_desc:
                count += 1
                if not only_count:
                    intf.append(i)
        return count if only_count else Interfaces(intf)

    def down(self, only_count=False):
        """Интерфейсы, состояние которых DOWN

        :param only_count: bool Только кол-во?
        """
        count = 0
        intf = []
        for i in self.__interfaces:
            if not i.is_up:
                count += 1
                if not only_count:
                    intf.append(i)
        return count if only_count else Interfaces(intf)

    def admin_down(self, only_count=False):
        """Интерфейсы, состояние которых ADMIN DOWN

        :param only_count: bool Только кол-во?
        """
        count = 0
        intf = []
        for i in self.__interfaces:
            if i.status == "admin down":
                count += 1
                if not only_count:
                    intf.append(i)
        return count if only_count else Interfaces(intf)

    def free(self, only_count=False):
        """
        Возвращает список свободных интерфейсов или только их кол-во

        :param only_count: bool Только кол-во?
        """
        count = 0
        intf = []
        for i in self.__interfaces:
            if not i.is_up and not i.has_desc:
                count += 1
                if not only_count:
                    intf.append(i)
        return count if only_count else Interfaces(intf)

    def non_system(self, only_count=False):
        """
        Возвращает список интерфейсов, которые не используются для связи с другими узлами сети

        :param only_count: bool Только кол-во?
        """
        count = 0
        intf = []
        for i in self.__interfaces:
            if NON_ABON_INTERFACES_PATTERN.findall(i.desc):
                continue
            if not only_count:
                intf.append(i)
        return count if only_count else Interfaces(intf)

    @property
    def unique_vlans(self) -> list:
        """Возвращает отсортированный список VLAN'ов, которые имеются на портах"""
        vlans: set = set()
        for i in self.__interfaces:
            vlans = vlans.union({v for v in i.vlan if v.isdigit()})
        return sorted([int(v) for v in vlans])

    def with_vlans(self, vlans: list):
        """
        Интерфейсы, которые имеют переданные vlans

        :param vlans: Список vlan'ов
        :return: Interfaces
        """
        if isinstance(vlans, list):
            vlans = list(map(int, vlans))
            return Interfaces([i for i in self.__interfaces if set(vlans) & set(i.vlan)])
        return Interfaces()

    def filter_by_desc(self, pattern: str):
        """Интерфейсы, описание которых совпадает с шаблоном"""
        return Interfaces([i for i in self.__interfaces if re.match(pattern, i.desc)])

    def filter_by_name(self, pattern: str):
        """Интерфейсы, имя которых совпадает с шаблоном"""
        return Interfaces([i for i in self.__interfaces if re.match(pattern, i.name)])

    @staticmethod
    def _parse_vlans_line(vlans: list) -> list[int]:
        """
        Эта функция принимает список VLAN, преобразует любые диапазоны VLAN, указанные в виде строк, в список
        целых чисел и возвращает список всех VLAN в виде целых чисел.

        Сначала функция проверяет, является ли каждый элемент во входном списке строкой или целым числом.
        Если это строка, она использует функцию `range_to_numbers()`, чтобы преобразовать ее в список целых чисел
        и добавить ее в `vlans_list`.

        :param vlans: Ожидается, что параметр "vlans" будет списком VLAN, который может быть либо целым числом, либо
        строкой, представляющей диапазон VLAN.

        :return: Список целых чисел, представляющих VLAN. Если ввод не является списком, возвращается пустой список.
        """

        if not isinstance(vlans, list):
            return []

        vlans_list = []
        for vlan in vlans:
            if isinstance(vlan, str):
                vlans_list += range_to_numbers(vlan)
            if isinstance(vlan, int):
                vlans_list.append(vlan)
        return vlans_list
