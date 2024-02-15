from dataclasses import dataclass, field

from check import models
from devicemanager.device import Interfaces
from devicemanager.device.interfaces import Interface


@dataclass
class BaseRingPoint:
    device: models.Devices
    ping: bool = None  # type: ignore
    port_to_prev_dev: Interface = field(default_factory=Interface)
    port_to_next_dev: Interface = field(default_factory=Interface)
    interfaces: Interfaces = field(default_factory=Interfaces)
    collect_vlans: bool = False
