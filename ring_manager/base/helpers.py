from concurrent.futures import ThreadPoolExecutor

from devicemanager.device import DeviceManager, Interfaces

from .types import BaseRingPoint


def _ping_point(point: BaseRingPoint):
    # Дважды
    return point.device.available and point.device.available


def thread_ping(devices: list[BaseRingPoint]):
    """
    Эта функция проверяет наличие устройств в списке и обновляет их статус ping.
    :return: Список объектов RingPoint, где каждый объект RingPoint имеет логическое значение,
     указывающее доступность устройства, которое он представляет.
    """
    with ThreadPoolExecutor() as ex:
        futures = []
        for point in devices:
            # Проверяем пинг
            futures.append(ex.submit(_ping_point, point=point))

        for i, f in enumerate(futures):
            devices[i].ping = f.result()


def _get_device_interfaces(point: BaseRingPoint, device_manager: type[DeviceManager]) -> Interfaces:
    dev = device_manager.from_model(point.device, zabbix_info=False)
    # Собираем текущее состояние интерфейсов, если оборудование доступно
    dev.collect_interfaces(vlans=point.collect_vlans, current_status=point.ping)
    return dev.interfaces


def collect_current_interfaces(
    devices: list[BaseRingPoint], device_manager: type[DeviceManager] = DeviceManager
):
    """
    Эта функция использует ThreadPoolExecutor для сбора всех интерфейсов устройств в кольце.
    """
    with ThreadPoolExecutor() as ex:
        futures = []
        for dev_point in devices:
            # Собираем интерфейсы
            futures.append(ex.submit(_get_device_interfaces, dev_point, device_manager))

        for i, f in enumerate(futures):
            devices[i].interfaces = f.result()
