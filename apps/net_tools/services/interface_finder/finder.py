import contextlib
import re
from datetime import datetime

import orjson
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.check.models import Devices, InterfacesComments
from devicemanager.device import Interfaces

from .types import (
    Comments,
    DescriptionFinderResult,
    DeviceInterfacesComments,
    DeviceInterfacesData,
    InterfaceComment,
    InterfaceCommentDict,
    InterfaceFinderFilter,
    InterfaceInfoDict,
)


class InterfacesFinder:
    def __init__(self, devices: QuerySet[Devices], filter_: InterfaceFinderFilter):
        self._devices_qs = devices
        self._filter = filter_

        # Фильтруем по названию оборудования
        if self._filter.device_name:
            if isinstance(self._filter.device_name, str):
                self._devices_qs = self._devices_qs.filter(name__icontains=self._filter.device_name)
            else:
                self._devices_qs = self._devices_qs.filter(name__iregex=self._filter.device_name.pattern)

        # Фильтруем по дате обнаружения интерфейсов
        self._devices_qs = self._devices_qs.select_related("devicesinfo")
        if self._filter.discovered_datetime_gt:
            self._devices_qs = self._devices_qs.filter(
                Q(devicesinfo__interfaces_date__gt=self._filter.discovered_datetime_gt)
                | Q(devicesinfo__vlans_date__gt=self._filter.discovered_datetime_gt)
            )

        device_info_values = self._devices_qs.values(
            "devicesinfo__interfaces",
            "devicesinfo__interfaces_date",
            "devicesinfo__vlans",
            "devicesinfo__vlans_date",
            "name",
        )

        self.devices: dict[str, DeviceInterfacesData] = {}
        for dev_info in device_info_values:
            interfaces = Interfaces(orjson.loads(dev_info["devicesinfo__interfaces"] or "[]"))
            vlans = Interfaces(orjson.loads(dev_info["devicesinfo__vlans"] or "[]"))

            if interfaces:
                valid_interfaces = interfaces
                for interface in interfaces:
                    interface.vlan = vlans[interface.name].vlan
            elif vlans:
                valid_interfaces = vlans
            else:
                continue

            self.devices[dev_info["name"]] = DeviceInterfacesData(
                interfaces=valid_interfaces,
                interfaces_date=dev_info["devicesinfo__interfaces_date"],
                vlans_date=dev_info["devicesinfo__vlans_date"],
            )

    def _build_interface_info(
        self,
        info: DeviceInterfacesData,
        interface_name: str,
        status: str,
        description: str,
    ) -> InterfaceInfoDict:
        """Создает типизированную структуру данных интерфейса."""
        return {
            "name": interface_name,
            "status": status,
            "description": description,
            "vlans": info.get_interface_vlans(interface_name),
            "savedTime": (info.interfaces_date or timezone.now()).isoformat(),
            "verboseSavedTime": self.get_natural_time(info.interfaces_date),
            "verboseVlansSavedTime": self.get_natural_time(info.vlans_date),
            "vlansSavedTime": (info.vlans_date or timezone.now()).isoformat(),
        }

    @staticmethod
    def _build_description_result(
        device_name: str,
        comments: list[InterfaceCommentDict],
        interface_info: InterfaceInfoDict,
    ) -> DescriptionFinderResult:
        """Создает типизированный результат поиска."""
        return {
            "device": device_name,
            "comments": comments,
            "interface": interface_info,
        }

    def find_description(self) -> list[DescriptionFinderResult]:
        """
        Поиск портов на всем оборудовании по фильтру
        """
        result: list[DescriptionFinderResult] = []

        comments: Comments = self.get_comments(self._filter.description_pattern)

        self._find_in_interfaces_history(comments, result)
        self._add_comments_to_result(comments, result)

        return result

    def _find_in_interfaces_history(self, comments: Comments, result: list[DescriptionFinderResult]) -> None:
        # Производим поочередный поиск
        for device_name, info in self.devices.items():
            # Смотрим данные интерфейсов в `interfaces` либо `vlans`
            for interface in info.interfaces:
                find_on_desc = False

                # Если имеется фильтр по состоянию интерфейса, то отбрасываем неподходящие
                if self._filter.interface_status and interface.status != self._filter.interface_status:
                    continue

                # Если НЕ нашли совпадение в НАЗВАНИИ порта - пропускаем
                if self._filter.interface_name and (
                    isinstance(self._filter.interface_name, re.Pattern)
                    and not self._filter.interface_name.search(interface.name)
                    or isinstance(self._filter.interface_name, str)
                    and self._filter.interface_name not in interface.desc
                ):
                    continue

                if self._filter.vlans_superset and not self._filter.vlans_superset.issuperset(interface.vlan):
                    continue

                interface_vlans = set(interface.vlan)

                # Если нет пересечения требуемых VLAN по фильтру и VLAN на интерфейсе
                if self._filter.vlans and not self._filter.vlans & interface_vlans:
                    continue

                # Если есть пересечение VLAN по фильтру исключения и VLAN на интерфейсе
                if self._filter.vlans_exclude and self._filter.vlans_exclude & interface_vlans:
                    continue

                # Если нашли совпадение в ОПИСАНИИ порта
                if (
                    isinstance(self._filter.description_pattern, re.Pattern)
                    and self._filter.description_pattern.search(interface.desc)
                    or isinstance(self._filter.description_pattern, str)
                    and self._filter.description_pattern in interface.desc
                ):
                    find_on_desc = True

                interface_comments = comments.get_interface(device_name, interface.name)

                # Если указан параметр искать только интерфейсы с комментариями и есть комментарии
                # Если такой параметр не указан, тогда, либо есть описание на порту, либо комментарий
                if (
                    self._filter.has_comment
                    and interface_comments
                    or not self._filter.has_comment
                    and (find_on_desc or interface_comments)
                ):
                    with contextlib.suppress(KeyError):  # Игнорируем, если ошибка ключа
                        result.append(
                            self._build_description_result(
                                device_name=device_name,
                                comments=[comment.to_dict() for comment in interface_comments],
                                interface_info=self._build_interface_info(
                                    info=info,
                                    interface_name=interface.name,
                                    status=interface.status,
                                    description=interface.desc,
                                ),
                            )
                        )

                    # Удаляем найденные комментарии
                    if interface_comments:
                        del comments.devices[device_name].interfaces[interface.name]

    def _add_comments_to_result(self, comments: Comments, result: list[DescriptionFinderResult]) -> None:
        for dev_name, dev_intf_comments in comments.devices.items():
            if dev_name not in self.devices:
                continue

            device_info = self.devices[dev_name]
            for interface in dev_intf_comments.interfaces:
                result.extend(
                    [
                        self._build_description_result(
                            device_name=dev_name,
                            comments=[comment.to_dict()],
                            interface_info=self._build_interface_info(
                                info=device_info,
                                interface_name=interface,
                                status=interface,
                                description=comment.text,
                            ),
                        )
                        for comment in dev_intf_comments.interfaces[interface]
                    ]
                )

    @staticmethod
    def get_natural_time(time_str: datetime | None) -> str:
        if time_str is not None:
            return naturaltime(time_str)
        return "No Datetime"

    def get_comments(self, pattern: str | re.Pattern[str]) -> Comments:
        """Возвращает список всех комментариев поискового запроса."""
        qs = InterfacesComments.objects.filter(device__in=self._devices_qs)

        if isinstance(pattern, str):
            qs = qs.filter(comment__icontains=pattern)
        else:
            qs = qs.filter(comment__iregex=pattern.pattern)

        comments = list(
            qs.select_related("user", "device").values(
                "user__username", "device__name", "interface", "comment", "datetime"
            )
        )
        comments_result: Comments = Comments()

        for comment in comments:
            comments_result.devices.setdefault(comment["device__name"], DeviceInterfacesComments())
            comments_result.devices[comment["device__name"]].interfaces.setdefault(comment["interface"], [])

            comments_result.devices[comment["device__name"]].interfaces[comment["interface"]].append(
                InterfaceComment(
                    user=comment["user__username"] or "Anonymous",
                    text=comment["comment"],
                    created_time=comment["datetime"],
                )
            )
        return comments_result
