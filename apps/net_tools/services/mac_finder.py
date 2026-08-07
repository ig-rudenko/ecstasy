from dataclasses import dataclass

import requests
from rest_framework.exceptions import ValidationError

from ecstasy_project.error_handler import ExternalServiceProblem


@dataclass(kw_only=True, slots=True)
class MACInfo:
    vendor: str
    address: str


def get_mac_info(mac: str, *, proxy: str | None = None) -> MACInfo:
    """Определяет производителя оборудования по MAC-адресу через внешний сервис."""

    proxies = {}
    if proxy:
        proxies = {"http": proxy, "https": proxy}

    try:
        resp = requests.get("https://api.maclookup.app/v2/macs/" + mac, timeout=2, proxies=proxies)
    except requests.RequestException as exc:
        raise ExternalServiceProblem(
            {"detail": "MAC vendor lookup service is unavailable.", "mac": mac}
        ) from exc

    if resp.status_code == 400:
        raise ValidationError({"mac": resp.json().get("error", "Invalid MAC")})
    if resp.status_code != 200:
        raise ValidationError({"mac": "Invalid MAC"})

    data = resp.json()
    return MACInfo(
        vendor=data.get("company", "Unknown"),
        address=data.get("address", "Unknown"),
    )
