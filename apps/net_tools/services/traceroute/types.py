from dataclasses import dataclass
from typing import Any, NamedTuple


class TracerouteResult(NamedTuple):
    """
    Представляет собой именованный кортеж, который содержит информацию об узле сети, его
    следующем узле, ширине линии, описании линии и статусе административного отключения.
    """

    node: str
    next_node: str
    line_width: int
    line_description: dict[str, Any]
    admin_down_status: str


@dataclass(frozen=True)
class VlanPortMatch:
    """Описывает точность совпадения VLAN на порту."""

    confidence: str
    broad_trunk: bool
    exact_match: bool
    vlan_count: int
    device_vlan_count: int
    matched_range: tuple[int, int] | None
    largest_range_size: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        """Возвращает структуру для передачи во frontend."""
        data: dict[str, Any] = {
            "confidence": self.confidence,
            "broad_trunk": self.broad_trunk,
            "exact_match": self.exact_match,
            "vlan_count": self.vlan_count,
            "device_vlan_count": self.device_vlan_count,
            "largest_range_size": self.largest_range_size,
            "reason": self.reason,
        }
        if self.matched_range:
            data["matched_range"] = {"from": self.matched_range[0], "to": self.matched_range[1]}
        return data
