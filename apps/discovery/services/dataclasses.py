from dataclasses import dataclass, field

from apps.check.models import AuthGroup


@dataclass(slots=True)
class DiscoveryAttemptData:
    """DTO результата одной сетевой попытки discovery."""

    ip: str
    method: str
    status: str
    duration_ms: int = 0
    error: str = ""


@dataclass(slots=True)
class DeviceFingerprint:
    """Нормализованный fingerprint найденного устройства."""

    ip: str
    name: str = ""
    vendor: str = ""
    model: str = ""
    serial_number: str = ""
    os_version: str = ""
    mac_address: str = ""
    sys_name: str = ""
    sys_descr: str = ""
    sys_object_id: str = ""
    source: str = "PING"
    detected_protocols: dict[str, bool] = field(default_factory=dict)
    selected_auth_group: AuthGroup | None = None
    selected_snmp_community: str = ""
    raw: dict = field(default_factory=dict)
    last_error: str = ""

    def has_identity(self) -> bool:
        """Вернуть True, если fingerprint содержит данные, похожие на сетевое оборудование."""

        return bool(
            self.vendor
            or self.model
            or self.serial_number
            or self.sys_name
            or self.sys_descr
            or self.selected_auth_group
        )
