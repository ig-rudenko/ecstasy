from abc import ABC, abstractmethod
from collections.abc import Callable
from functools import cache

from apps.app_settings.models import ZabbixConfig
from apps.check.models import Devices
from devicemanager.device import Interfaces, zabbix_api
from devicemanager.exceptions import BaseDeviceException
from devicemanager.vendors import BaseDevice


class AbstractRealtimeCollector(ABC):
    """
    # This class is used for collecting realtime information from the device
    """

    def __init__(
        self,
        device: Devices,
        session: BaseDevice,
        interfaces: Interfaces,
        interfaces_desc: dict[str, str] | None = None,
        normalize_interface: Callable[[str], str] | None = None,
    ) -> None:
        if not zabbix_api.zabbix_url:
            zabbix_api.set_lazy_attributes(ZabbixConfig.load())

        self.device: Devices = device
        self.interfaces: Interfaces = interfaces or Interfaces()
        self.interfaces_desc: dict[str, str] = interfaces_desc or {}
        self.session = session
        self.normalize_interface = (
            cache(normalize_interface)
            if normalize_interface
            else cache(
                lambda i: self.session.normalize_interface_name(
                    self.session.normalize_interface_name_realtime(i)
                )
            )
        )

    def run_gathering(self) -> None:
        try:
            if not self.interfaces_desc:
                # Нормализация имени интерфейса необходима из-за разных вариантов записи одного и того же порта.
                # Например - `1/1` и `1`, `26(C)` и `26(F)`.
                self.interfaces_desc = self.format_interfaces(self.interfaces)

            self.collect()

        except BaseDeviceException:
            pass

    @abstractmethod
    def collect(self) -> None:
        pass

    def format_interfaces(self, old_interfaces: Interfaces) -> dict:
        """
        ## Принимает список интерфейсов, и формирует словарь из интерфейсов и их описаний

        :return: Словарь интерфейсов и соответствующих им описаний.
        """
        interfaces = {}

        # Перебираем список интерфейсов
        for line in old_interfaces:
            normal_interface = self.normalize_interface(line.name)

            # Проверка, не является ли имя интерфейса пустым.
            if normal_interface:
                # Добавление имени интерфейса в качестве ключа и описания в качестве значения в словарь.
                interfaces[normal_interface] = line.desc

        return interfaces
