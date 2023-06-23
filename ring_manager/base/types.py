from dataclasses import dataclass

from check import models
from devicemanager.device import Interfaces
from devicemanager.zabbix_info_dataclasses import Interface


@dataclass
class BaseRingPoint:
    device: models.Devices
    ping: bool = None
    port_to_prev_dev: Interface = Interface()
    port_to_next_dev: Interface = Interface()
    interfaces: Interfaces = Interfaces()
    collect_vlans: bool = False
