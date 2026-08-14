import re

from apps.check.models import Devices

from ..models import DiscoveryCandidate, DiscoveryProfile
from .dataclasses import DeviceFingerprint


def calculate_confidence(fingerprint: DeviceFingerprint, duplicate: bool = False) -> int:
    """Рассчитать confidence кандидата discovery."""

    confidence = 0
    if any(fingerprint.detected_protocols.values()):
        confidence += 20
    if fingerprint.sys_descr or fingerprint.sys_name:
        confidence += 30
    if fingerprint.vendor:
        confidence += 20
    if fingerprint.model:
        confidence += 15
    if fingerprint.selected_auth_group:
        confidence += 15
    if duplicate:
        confidence -= 40
    return max(0, min(confidence, 100))


def suggested_name(fingerprint: DeviceFingerprint) -> str:
    """Вернуть безопасное предложенное имя кандидата."""

    raw_name = (fingerprint.name or fingerprint.sys_name or "").strip()
    if raw_name:
        return re.sub(r"\s+", "-", raw_name)[:100]
    return f"discovered-{fingerprint.ip.replace('.', '-')}"


def find_duplicate_device(fingerprint: DeviceFingerprint) -> Devices | None:
    """Найти существующее устройство по IP."""

    return Devices.objects.filter(ip=fingerprint.ip).first()


def find_available_cli_protocol(candidate: DiscoveryCandidate) -> str | None:
    """Выбрать доступный CLI-протокол кандидата."""

    detected_protocols = candidate.detected_protocols
    cli_protocol = str(candidate.raw_fingerprint.get("cliProtocol", "")).lower()
    if cli_protocol in {"ssh", "telnet"} and detected_protocols.get(cli_protocol) is True:
        return cli_protocol
    for protocol in ("ssh", "telnet"):
        if detected_protocols.get(protocol) is True:
            return protocol
    return None


def update_created_device_protocols(candidate: DiscoveryCandidate) -> None:
    """Заменить недоступные протоколы ранее созданного оборудования."""

    if (
        candidate.status not in {DiscoveryCandidate.Status.CREATED, DiscoveryCandidate.Status.DUPLICATE}
        or candidate.device_id is None
    ):
        return

    available_cli_protocol = find_available_cli_protocol(candidate)
    if available_cli_protocol is None:
        return

    device = candidate.device
    if not device:
        return

    update_fields = []
    if candidate.detected_protocols.get(device.cmd_protocol) is False:
        device.cmd_protocol = available_cli_protocol
        update_fields.append("cmd_protocol")
    if candidate.detected_protocols.get(device.port_scan_protocol) is False:
        device.port_scan_protocol = available_cli_protocol
        update_fields.append("port_scan_protocol")
    if update_fields:
        device.save(update_fields=update_fields)


def upsert_candidate(profile: DiscoveryProfile, fingerprint: DeviceFingerprint) -> DiscoveryCandidate:
    """Создать или обновить discovery candidate по fingerprint."""

    duplicate_device = find_duplicate_device(fingerprint)
    duplicate = duplicate_device is not None
    confidence = calculate_confidence(fingerprint, duplicate=duplicate)
    name = suggested_name(fingerprint)
    device_is_linked = bool(
        duplicate_device
        and DiscoveryCandidate.objects.filter(device=duplicate_device).exclude(ip=fingerprint.ip).exists()
    )
    raw_fingerprint = dict(fingerprint.raw)
    if device_is_linked and duplicate_device is not None:
        raw_fingerprint["duplicateDeviceId"] = duplicate_device.id

    if duplicate:
        status = DiscoveryCandidate.Status.DUPLICATE
    elif fingerprint.has_identity() and confidence >= 40:
        status = DiscoveryCandidate.Status.READY
    elif any(fingerprint.detected_protocols.values()):
        status = DiscoveryCandidate.Status.NEW
    else:
        status = DiscoveryCandidate.Status.FAILED

    defaults = {
        "name": name,
        "vendor": fingerprint.vendor,
        "model": fingerprint.model,
        "serial_number": fingerprint.serial_number,
        "os_version": fingerprint.os_version,
        "mac_address": fingerprint.mac_address,
        "sys_name": fingerprint.sys_name,
        "sys_descr": fingerprint.sys_descr,
        "sys_object_id": fingerprint.sys_object_id,
        "source": fingerprint.source,
        "confidence": confidence,
        "detected_protocols": fingerprint.detected_protocols,
        "selected_auth_group": fingerprint.selected_auth_group,
        "selected_snmp_community": fingerprint.selected_snmp_community,
        "device": None if device_is_linked else duplicate_device,
        "raw_fingerprint": raw_fingerprint,
        "last_error": fingerprint.last_error,
    }

    candidate, created = DiscoveryCandidate.objects.update_or_create(ip=fingerprint.ip, defaults=defaults)
    if not created and profile.auto_create:
        update_created_device_protocols(candidate)
    if not created and candidate.status in {
        DiscoveryCandidate.Status.CREATED,
        DiscoveryCandidate.Status.IGNORED,
    }:
        return candidate

    candidate.status = status
    candidate.save(update_fields=["status"])
    return candidate
