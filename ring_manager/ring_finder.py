import re
from dataclasses import dataclass
from typing import List

import orjson

from check.models import Devices
from devicemanager.device import Interfaces
from devicemanager.device.interfaces import Interface
from .base.finder import find_links_between_points
from .base.types import BaseRingPoint


@dataclass
class RingDevice:
    device: Devices
    interfaces: Interfaces


@dataclass
class AdminDownInfo:
    device: Devices
    port: str
    to_device: str
    normal_status: bool = False


@dataclass
class RingStructure:
    port_start: str
    devices: List[BaseRingPoint]
    port_end: str
    _admin_down: List[AdminDownInfo] = None

    def find_links(self) -> None:
        find_links_between_points(self.devices)

    @property
    def head_name(self) -> str:
        return self.devices[0].device.name

    @property
    def ports(self) -> str:
        return f"{self.port_start} - {self.port_end}"

    @property
    def description(self) -> str:
        return f"Устройств в кольце: {len(self.devices)}\n"

    def json(self) -> dict:
        return {
            "portStart": self.port_start,
            "devices": self.devices,
            "portEnd": self.port_end,
        }

    def get_admin_down_info(self) -> List[AdminDownInfo]:
        """
        Эта функция возвращает список объектов AdminDownInfo для интерфейсов,
        отключенных административно на устройствах в кольцевой топологии.
        """
        if self._admin_down is not None:
            return self._admin_down

        ring_devices_names = [ring_dev.device.name for ring_dev in self.devices]

        admin_down = []

        for ring_dev in self.devices:
            for interface in ring_dev.interfaces:
                match = re.findall(r"SVSL\S+[AS]SW\d", interface.desc)

                # Если нашли на порту оборудование кольца и порт выключен
                if match and match[0] in ring_devices_names and interface.is_admin_down:
                    admin_down.append(
                        AdminDownInfo(
                            device=ring_dev.device,
                            port=interface.name,
                            to_device=match[0],
                            normal_status=bool(ring_dev == self.devices[0]),
                        )
                    )

        self._admin_down = admin_down
        return self._admin_down

    def is_normal_rotate_status(self) -> bool:
        self.get_admin_down_info()
        return bool(len(self._admin_down) == 1 and self._admin_down[0].normal_status)


@dataclass
class DeviceMatch:
    name: str = ""
    agg: bool = False

    def __bool__(self):
        return bool(self.name)


class AggregationRingFinder:
    """
    Принимает объект агрегации и находит кольцевые подключения доступов.
    """

    def __init__(self, agg: Devices):
        self._agg: Devices = agg
        self._result_rings: List[RingStructure] = []
        self._current_agg_port: str = ""
        self._passed_devices: List[str] = []
        self._passed_agg_ports: List[str] = []

        self._temp_passed_devices: List[str] = []
        self._temp_result_rings: List[BaseRingPoint] = []
        self._agg_interfaces: Interfaces = Interfaces()

    def start_find(self) -> None:
        self._find_rings(self._agg)

    def get_rings(self) -> List[RingStructure]:
        return self._result_rings

    def _get_agg_interfaces(self) -> Interfaces:
        if not self._agg_interfaces:
            self._agg_interfaces = Interfaces(orjson.loads(self._agg.devicesinfo.interfaces))
        return self._agg_interfaces

    def _clear_temp(self) -> None:
        self._temp_passed_devices = []
        self._temp_result_rings = []
        self._current_agg_port = ""

    @staticmethod
    def _match_device(string) -> DeviceMatch:
        match = re.findall(r"SVSL\S+ASW\d", string)
        if match:
            return DeviceMatch(name=match[0], agg=False)
        match = re.findall(r"SVSL\S+SSW\d", string)
        if match:
            return DeviceMatch(name=match[0], agg=True)
        return DeviceMatch()

    def _get_end_agg_port_to_dev(self, device_name: str) -> str:
        for interface in self._get_agg_interfaces():
            if self._match_device(interface.desc).name == device_name:
                return interface.name

    def _not_in_passed(self, device_name) -> bool:
        return bool(
            device_name not in self._temp_passed_devices and device_name not in self._passed_devices
        )

    def _set_start_port(self, interface: Interface) -> None:
        self._current_agg_port = interface.name
        self._passed_agg_ports.append(interface.name)

    def _add_new_ring(self, end_device: Devices) -> None:
        """
        Эта функция добавляет новое кольцо в список кольцевых структур с заданным конечным устройством.
        """
        agg_end_interface_name = self._get_end_agg_port_to_dev(device_name=end_device.name)
        self._result_rings.append(
            RingStructure(
                port_start=self._current_agg_port,
                devices=self._temp_result_rings,
                port_end=agg_end_interface_name,
            )
        )
        self._passed_agg_ports.append(agg_end_interface_name)

    def _not_first_in_chain(self, device: Devices) -> bool:
        return bool(
            len(self._temp_result_rings) >= 2
            and self._temp_result_rings[1].device.name != device.name
        )

    def _find_rings(self, dev: Devices) -> None:
        """
        Это рекурсивная функция, которая ищет кольца в топологии сети, перебирая устройства и их интерфейсы.
        """

        self._temp_passed_devices.append(dev.name)

        if not hasattr(dev, "devicesinfo"):
            return
        device_interfaces = Interfaces(orjson.loads(dev.devicesinfo.interfaces or "[]"))

        for interface in device_interfaces:
            match = self._match_device(interface.desc)

            # Начало кольца
            if not self._current_agg_port and dev == self._agg and match:
                if interface.name in self._passed_agg_ports:
                    continue
                self._set_start_port(interface)

            # Конец кольца
            elif self._not_first_in_chain(dev) and match.name == self._agg.name:
                # print("Конец кольца", dev.name)
                self._temp_result_rings.append(
                    BaseRingPoint(device=dev, interfaces=device_interfaces)
                )
                self._add_new_ring(end_device=dev)
                self._passed_devices += self._temp_passed_devices
                self._clear_temp()
                return

            # Ищем далее
            if match and self._not_in_passed(match.name) and not match.agg:
                self._temp_result_rings.append(
                    BaseRingPoint(device=dev, interfaces=device_interfaces)
                )
                try:
                    next_device = Devices.objects.get(name=match.name)
                    self._find_rings(next_device)
                except Devices.DoesNotExist:
                    self._temp_passed_devices.append(match.name)

            if dev == self._agg:
                self._passed_devices = self._temp_passed_devices
                self._clear_temp()
