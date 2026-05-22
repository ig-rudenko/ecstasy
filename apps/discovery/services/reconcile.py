import re

from django.db.models import Q

from apps.check.models import Devices

from ..models import DiscoveryCandidate
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
    """Найти существующее устройство по IP, имени или серийному номеру."""

    query = Q(ip=fingerprint.ip)
    name = suggested_name(fingerprint)
    if name:
        query |= Q(name=name)
    if fingerprint.serial_number:
        query |= Q(serial_number=fingerprint.serial_number)
    return Devices.objects.filter(query).first()


def upsert_candidate(fingerprint: DeviceFingerprint) -> DiscoveryCandidate:
    """Создать или обновить discovery candidate по fingerprint."""

    duplicate_device = find_duplicate_device(fingerprint)
    duplicate = duplicate_device is not None
    confidence = calculate_confidence(fingerprint, duplicate=duplicate)
    name = suggested_name(fingerprint)

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
        "device": duplicate_device,
        "raw_fingerprint": fingerprint.raw,
        "last_error": fingerprint.last_error,
    }

    candidate, created = DiscoveryCandidate.objects.update_or_create(ip=fingerprint.ip, defaults=defaults)
    if not created and candidate.status in {
        DiscoveryCandidate.Status.CREATED,
        DiscoveryCandidate.Status.IGNORED,
    }:
        return candidate

    candidate.status = status
    candidate.save(update_fields=["status"])
    return candidate
