from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from apps.check.models import AuthGroup, DeviceGroup, Devices, UsersActions
from apps.check.services.device.interfaces_collector import DeviceDBSynchronizer
from devicemanager.device import DeviceManager

from ..models import DiscoveryCandidate, DiscoveryProfile


def accept_candidate(
    candidate: DiscoveryCandidate,
    *,
    profile: DiscoveryProfile | None = None,
    device_group: DeviceGroup | None = None,
    auth_group: AuthGroup | None = None,
    cmd_protocol: str = "",
    port_scan_protocol: str = "",
    snmp_community: str = "",
    collect_interfaces: bool = False,
    user=None,
) -> Devices:
    """Создать `Devices` из подтвержденного discovery candidate."""

    if candidate.status == DiscoveryCandidate.Status.CREATED and candidate.device:
        return candidate.device
    if candidate.status == DiscoveryCandidate.Status.DUPLICATE:
        raise ValidationError({"detail": "Кандидат совпадает с существующим оборудованием"})

    resolved_group = device_group or (profile.device_group if profile else None)
    resolved_auth_group = auth_group or candidate.selected_auth_group
    if resolved_auth_group is None and profile is not None:
        resolved_auth_group = profile.auth_groups.first()
    if resolved_group is None:
        raise ValidationError({"deviceGroup": "Необходимо указать группу оборудования"})
    if resolved_auth_group is None:
        raise ValidationError({"authGroup": "Необходимо указать группу авторизации"})

    device_name = candidate.name or f"discovered-{candidate.ip.replace('.', '-')}"
    resolved_cmd_protocol = cmd_protocol or resolve_candidate_cmd_protocol(candidate, profile)
    resolved_port_scan_protocol = port_scan_protocol or resolve_candidate_port_scan_protocol(candidate, profile)
    resolved_snmp_community = snmp_community or candidate.selected_snmp_community

    try:
        with transaction.atomic():
            device = Devices.objects.create(
                ip=candidate.ip,
                name=device_name,
                group=resolved_group,
                auth_group=resolved_auth_group,
                vendor=candidate.vendor,
                model=candidate.model,
                serial_number=candidate.serial_number,
                os_version=candidate.os_version,
                snmp_community=resolved_snmp_community,
                port_scan_protocol=resolved_port_scan_protocol,
                cmd_protocol=resolved_cmd_protocol,
                active=False,
            )
            candidate.device = device
            candidate.status = DiscoveryCandidate.Status.CREATED
            candidate.save(update_fields=["device", "status"])
            if user is not None and getattr(user, "is_authenticated", False):
                UsersActions.objects.create(
                    user=user,
                    device=device,
                    action=f"accept discovery candidate {candidate.ip}",
                )
    except IntegrityError as exc:
        raise ValidationError({"detail": "Устройство с таким IP или именем уже существует"}) from exc

    if collect_interfaces:
        collect_initial_interfaces(device)

    return device


def resolve_candidate_cmd_protocol(candidate: DiscoveryCandidate, profile: DiscoveryProfile | None) -> str:
    """Определить cmd_protocol из fingerprint кандидата или профиля."""

    cli_protocol = str(candidate.raw_fingerprint.get("cliProtocol", "")).lower()
    if cli_protocol in {"ssh", "telnet"}:
        return cli_protocol
    if candidate.detected_protocols.get("ssh"):
        return "ssh"
    if candidate.detected_protocols.get("telnet"):
        return "telnet"
    return profile.cmd_protocol if profile else "ssh"


def resolve_candidate_port_scan_protocol(candidate: DiscoveryCandidate, profile: DiscoveryProfile | None) -> str:
    """Определить port_scan_protocol из fingerprint кандидата или профиля."""

    if candidate.detected_protocols.get("snmp"):
        return "snmp"
    if candidate.detected_protocols.get("ssh"):
        return "ssh"
    if candidate.detected_protocols.get("telnet"):
        return "telnet"
    return profile.port_scan_protocol if profile else "snmp"


def collect_initial_interfaces(device: Devices) -> None:
    """Выполнить первичный сбор интерфейсов и активировать устройство при успехе."""

    synchronizer = DeviceDBSynchronizer(
        device=device,
        device_collector=DeviceManager.from_model(device),
        with_vlans=device.port_scan_protocol != "snmp",
    )
    synchronizer.collect_current_interfaces(make_session_global=False)
    synchronizer.sync_device_info_to_db()
    synchronizer.save_interfaces_to_db()
    device.active = True
    device.save(update_fields=["active"])
