from collections.abc import Iterable
from time import monotonic

from apps.check.models import AuthGroup
from devicemanager.dc import DeviceRemoteConnector
from devicemanager.exceptions import BaseDeviceException
from devicemanager import snmp

from ..models import DiscoveryAttempt, DiscoveryCandidate, DiscoveryProfile
from .dataclasses import DeviceFingerprint, DiscoveryAttemptData


VENDOR_HINTS = {
    "cisco": "Cisco",
    "d-link": "D-Link",
    "dlink": "D-Link",
    "edge-core": "Edge-Core",
    "eltex": "Eltex",
    "extreme": "Extreme",
    "huawei": "Huawei",
    "iskratel": "Iskratel",
    "juniper": "Juniper",
    "mikrotik": "MikroTik",
    "procurve": "ProCurve",
    "qtech": "Qtech",
    "q-tech": "Qtech",
    "zte": "ZTE",
    "zyxel": "Zyxel",
}


def guess_vendor(sys_descr: str, sys_object_id: str = "") -> str:
    """Определить вендора по SNMP-описанию эвристикой."""

    haystack = f"{sys_descr} {sys_object_id}".lower()
    for marker, vendor in VENDOR_HINTS.items():
        if marker in haystack:
            return vendor
    return ""


def merge_fingerprints(base: DeviceFingerprint, extra: DeviceFingerprint) -> DeviceFingerprint:
    """Объединить два fingerprint, предпочитая уже найденные точные значения."""

    for field_name in [
        "name",
        "vendor",
        "model",
        "serial_number",
        "os_version",
        "mac_address",
        "sys_name",
        "sys_descr",
        "sys_object_id",
        "selected_snmp_community",
        "last_error",
    ]:
        if not getattr(base, field_name) and getattr(extra, field_name):
            setattr(base, field_name, getattr(extra, field_name))

    if extra.selected_auth_group and not base.selected_auth_group:
        base.selected_auth_group = extra.selected_auth_group

    base.detected_protocols.update(extra.detected_protocols)
    base.raw.update(extra.raw)
    if extra.source != DiscoveryCandidate.Source.PING:
        base.source = extra.source
    return base


class SnmpFingerprinter:
    """Получает identity оборудования через SNMP v2c."""

    def __init__(self, communities: Iterable[str], timeout: int) -> None:
        """Сохранить SNMP communities и таймаут."""

        self.communities = [str(community) for community in communities if str(community)]
        self.timeout = timeout

    def collect(self, ip: str) -> tuple[DeviceFingerprint, list[DiscoveryAttemptData]]:
        """Попробовать получить SNMP identity для IP."""

        attempts = []
        for community in self.communities:
            started = monotonic()
            try:
                identity = snmp.get_system_identity(ip, community=community, timeout=self.timeout)
            except Exception as exc:
                attempts.append(
                    DiscoveryAttemptData(
                        ip=ip,
                        method=DiscoveryAttempt.Method.SNMP,
                        status=DiscoveryAttempt.Status.FAILED,
                        duration_ms=int((monotonic() - started) * 1000),
                        error=safe_error(exc),
                    )
                )
                continue

            attempts.append(
                DiscoveryAttemptData(
                    ip=ip,
                    method=DiscoveryAttempt.Method.SNMP,
                    status=DiscoveryAttempt.Status.SUCCESS if identity else DiscoveryAttempt.Status.FAILED,
                    duration_ms=int((monotonic() - started) * 1000),
                )
            )
            if not identity:
                continue

            sys_descr = identity.get("sys_descr", "")
            sys_name = identity.get("sys_name", "")
            sys_object_id = identity.get("sys_object_id", "")
            fingerprint = DeviceFingerprint(
                ip=ip,
                name=sys_name,
                vendor=guess_vendor(sys_descr, sys_object_id),
                sys_name=sys_name,
                sys_descr=sys_descr,
                sys_object_id=sys_object_id,
                source=DiscoveryCandidate.Source.SNMP,
                detected_protocols={"snmp": True},
                selected_snmp_community=community,
                raw={"snmp": identity},
            )
            return fingerprint, attempts

        return DeviceFingerprint(ip=ip, detected_protocols={"snmp": False}), attempts


class CliFingerprinter:
    """Получает identity оборудования через SSH/Telnet и существующий devicemanager."""

    def __init__(self, protocols: Iterable[str], auth_groups: Iterable[AuthGroup], snmp_community: str = "") -> None:
        """Сохранить протоколы и группы авторизации для CLI fingerprint."""

        self.protocols = [protocol for protocol in protocols if protocol in {"ssh", "telnet"}]
        self.auth_groups = list(auth_groups)
        self.snmp_community = snmp_community

    def collect(self, ip: str) -> tuple[DeviceFingerprint, list[DiscoveryAttemptData]]:
        """Попробовать подключиться к IP по CLI и получить system info."""

        attempts = []
        for protocol in self.protocols:
            for auth_group in self.auth_groups:
                started = monotonic()
                try:
                    with DeviceRemoteConnector(
                        ip=ip,
                        protocol=protocol,
                        auth_obj=auth_group,
                        snmp_community=self.snmp_community,
                    ) as session:
                        system_info = session.get_system_info()
                except BaseDeviceException as exc:
                    attempts.append(self._build_failed_attempt(ip, protocol, started, exc))
                    continue
                except Exception as exc:
                    attempts.append(self._build_failed_attempt(ip, protocol, started, exc))
                    continue

                attempts.append(
                    DiscoveryAttemptData(
                        ip=ip,
                        method=protocol.upper(),
                        status=DiscoveryAttempt.Status.SUCCESS,
                        duration_ms=int((monotonic() - started) * 1000),
                    )
                )
                return DeviceFingerprint(
                    ip=ip,
                    name="",
                    vendor=system_info.get("vendor", ""),
                    model=system_info.get("model", ""),
                    serial_number=system_info.get("serialno", ""),
                    os_version=system_info.get("os_version", ""),
                    mac_address=system_info.get("mac", ""),
                    source=DiscoveryCandidate.Source.CLI,
                    detected_protocols={protocol: True},
                    selected_auth_group=auth_group,
                    raw={"cli": system_info, "cliProtocol": protocol},
                ), attempts

        return DeviceFingerprint(ip=ip), attempts

    @staticmethod
    def _build_failed_attempt(
        ip: str,
        protocol: str,
        started: float,
        exc: Exception,
    ) -> DiscoveryAttemptData:
        """Построить безопасную запись неуспешной CLI-попытки."""

        status = DiscoveryAttempt.Status.AUTH_FAILED if "логин" in str(exc).lower() else DiscoveryAttempt.Status.FAILED
        return DiscoveryAttemptData(
            ip=ip,
            method=protocol.upper(),
            status=status,
            duration_ms=int((monotonic() - started) * 1000),
            error=safe_error(exc),
        )


class DeviceFingerprinter:
    """Комбинирует SNMP и CLI fingerprint для одного IP."""

    def __init__(self, profile: DiscoveryProfile, include_cli: bool = True) -> None:
        """Сохранить профиль discovery."""

        self.profile = profile
        self.include_cli = include_cli

    def collect(self, ip: str, detected_protocols: dict[str, bool]) -> tuple[DeviceFingerprint, list[DiscoveryAttemptData]]:
        """Собрать максимально полный fingerprint для IP."""

        fingerprint = DeviceFingerprint(
            ip=ip,
            source=DiscoveryCandidate.Source.TCP if any(detected_protocols.values()) else DiscoveryCandidate.Source.PING,
            detected_protocols=dict(detected_protocols),
        )
        attempts = []

        snmp_fingerprint, snmp_attempts = SnmpFingerprinter(
            self.profile.snmp_communities,
            timeout=self.profile.timeout_seconds,
        ).collect(ip)
        attempts.extend(snmp_attempts)
        fingerprint = merge_fingerprints(fingerprint, snmp_fingerprint)

        if self.include_cli:
            open_protocols = [
                protocol
                for protocol in self.profile.try_protocols
                if protocol in {"ssh", "telnet"} and detected_protocols.get(protocol)
            ]
            cli_fingerprint, cli_attempts = CliFingerprinter(
                protocols=open_protocols,
                auth_groups=self.profile.auth_groups.all(),
                snmp_community=fingerprint.selected_snmp_community,
            ).collect(ip)
            attempts.extend(cli_attempts)
            fingerprint = merge_fingerprints(fingerprint, cli_fingerprint)

        if not fingerprint.name:
            fingerprint.name = fingerprint.sys_name

        return fingerprint, attempts


def safe_error(exc: Exception) -> str:
    """Вернуть безопасный текст ошибки без секретов."""

    message = str(exc)
    if len(message) > 500:
        return message[:497] + "..."
    return message
