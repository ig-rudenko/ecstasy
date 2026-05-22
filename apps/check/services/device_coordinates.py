from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from apps.check.models import Devices
from apps.check.services.zabbix import (
    DeviceCoords,
    ZabbixHostCoordinates,
    get_zabbix_hosts_coordinates,
    get_zabbix_hosts_coordinates_inventory,
    update_zabbix_host_coordinates,
)

COORDINATE_PRECISION = Decimal("0.000001")


@dataclass(slots=True, frozen=True)
class Coordinates:
    """Validated decimal geographic coordinates."""

    latitude: Decimal
    longitude: Decimal


def get_devices_coordinates(device_names: list[str]) -> dict[str, DeviceCoords]:
    """Return coordinates by device name, preferring Ecstasy DB with Zabbix fallback."""
    if not device_names:
        return {}

    coordinates: dict[str, DeviceCoords] = {}
    devices = Devices.objects.filter(name__in=device_names).only("name", "latitude", "longitude")
    for device in devices:
        try:
            device_coordinates = parse_coordinates(device.latitude, device.longitude)
        except ValueError:
            continue
        if device_coordinates is None:
            continue

        coordinates[device.name] = DeviceCoords(
            lat=float(device_coordinates.latitude),
            lon=float(device_coordinates.longitude),
        )

    missing_names = [name for name in device_names if name not in coordinates]
    zabbix_coordinates = get_zabbix_hosts_coordinates(missing_names)
    for name, raw_coordinates in zabbix_coordinates.items():
        try:
            parsed_coordinates = parse_coordinates(raw_coordinates.lat, raw_coordinates.lon)
        except ValueError:
            continue
        if parsed_coordinates is None:
            continue

        coordinates[name] = DeviceCoords(
            lat=float(parsed_coordinates.latitude),
            lon=float(parsed_coordinates.longitude),
        )
    return coordinates


def sync_device_coordinates_with_zabbix(
    *,
    device_ids: list[int] | None = None,
    dry_run: bool = False,
    update_ecstasy: bool = True,
    update_zabbix: bool = True,
) -> dict[str, int]:
    """Synchronize device coordinates between Ecstasy and Zabbix without resolving conflicts."""
    if device_ids is not None:
        devices_qs = Devices.objects.filter(id__in=device_ids)
    else:
        devices_qs = Devices.objects.filter(active=True)
    devices_qs = devices_qs.only("id", "name", "latitude", "longitude")
    devices = list(devices_qs)
    zabbix_hosts = get_zabbix_hosts_coordinates_inventory([device.name for device in devices])
    summary = _empty_sync_summary()

    for device in devices:
        zabbix_host = zabbix_hosts.get(device.name)
        if not zabbix_host:
            summary["missing_zabbix_host"] += 1
            continue

        try:
            ecstasy_coordinates = parse_coordinates(device.latitude, device.longitude)
        except ValueError:
            summary["errors"] += 1
            continue

        try:
            zabbix_coordinates = parse_coordinates(zabbix_host.lat, zabbix_host.lon)
        except ValueError:
            summary["invalid_zabbix"] += 1
            continue

        if ecstasy_coordinates is None and zabbix_coordinates is None:
            summary["unchanged"] += 1
            continue

        if ecstasy_coordinates is None and zabbix_coordinates is not None:
            _update_ecstasy_coordinates(device, zabbix_coordinates, dry_run, update_ecstasy, summary)
            continue

        if ecstasy_coordinates is not None and zabbix_coordinates is None:
            _update_zabbix_coordinates(zabbix_host, ecstasy_coordinates, dry_run, update_zabbix, summary)
            continue

        if coordinates_equal(ecstasy_coordinates, zabbix_coordinates):
            summary["unchanged"] += 1
            continue

        summary["conflicts"] += 1

    return summary


def parse_coordinates(latitude: Any, longitude: Any) -> Coordinates | None:
    """Parse a nullable coordinate pair and reject invalid or 0,0 coordinates."""
    latitude_is_empty = _coordinate_is_empty(latitude)
    longitude_is_empty = _coordinate_is_empty(longitude)
    if latitude_is_empty and longitude_is_empty:
        return None
    if latitude_is_empty != longitude_is_empty:
        raise ValueError("Coordinate pair is incomplete.")

    try:
        parsed_latitude = _to_decimal(latitude)
        parsed_longitude = _to_decimal(longitude)
    except InvalidOperation as exc:
        raise ValueError("Coordinates must be decimal numbers.") from exc

    if parsed_latitude == Decimal("0") and parsed_longitude == Decimal("0"):
        raise ValueError("Coordinates 0,0 are invalid.")
    if not Decimal("-90") <= parsed_latitude <= Decimal("90"):
        raise ValueError("Latitude is out of range.")
    if not Decimal("-180") <= parsed_longitude <= Decimal("180"):
        raise ValueError("Longitude is out of range.")
    return Coordinates(latitude=parsed_latitude, longitude=parsed_longitude)


def coordinates_equal(first: Coordinates | None, second: Coordinates | None) -> bool:
    """Compare coordinates using six decimal places."""
    if first is None or second is None:
        return first is second
    first_latitude = first.latitude.quantize(COORDINATE_PRECISION)
    first_longitude = first.longitude.quantize(COORDINATE_PRECISION)
    second_latitude = second.latitude.quantize(COORDINATE_PRECISION)
    second_longitude = second.longitude.quantize(COORDINATE_PRECISION)
    return first_latitude == second_latitude and first_longitude == second_longitude


def _empty_sync_summary() -> dict[str, int]:
    """Build sync counters returned by coordinate synchronization."""
    return {
        "updated_ecstasy": 0,
        "updated_zabbix": 0,
        "conflicts": 0,
        "invalid_zabbix": 0,
        "missing_zabbix_host": 0,
        "unchanged": 0,
        "errors": 0,
    }


def _update_ecstasy_coordinates(
    device: Devices,
    coordinates: Coordinates,
    dry_run: bool,
    update_ecstasy: bool,
    summary: dict[str, int],
) -> None:
    """Update Ecstasy coordinates when synchronization rules allow it."""
    if update_ecstasy and not dry_run:
        Devices.objects.filter(id=device.id).update(
            latitude=coordinates.latitude,
            longitude=coordinates.longitude,
        )
    summary["updated_ecstasy"] += 1


def _update_zabbix_coordinates(
    zabbix_host: ZabbixHostCoordinates,
    coordinates: Coordinates,
    dry_run: bool,
    update_zabbix: bool,
    summary: dict[str, int],
) -> None:
    """Update Zabbix coordinates when synchronization rules allow it."""
    if update_zabbix and not dry_run:
        updated = update_zabbix_host_coordinates(
            zabbix_host.hostid,
            coordinates.latitude,
            coordinates.longitude,
        )
        if not updated:
            summary["errors"] += 1
            return
    summary["updated_zabbix"] += 1


def _coordinate_is_empty(value: Any) -> bool:
    """Return True when a raw coordinate value is missing."""
    return value is None or str(value).strip() == ""


def _to_decimal(value: Any) -> Decimal:
    """Convert Zabbix or DB coordinate value to Decimal."""
    return Decimal(str(value).strip().replace(",", "."))
