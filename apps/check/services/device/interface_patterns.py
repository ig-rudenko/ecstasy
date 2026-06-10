import re
from dataclasses import dataclass

from django.core.cache import cache

from apps.check.models import DeviceInterfacePatternRule, Devices


@dataclass(frozen=True, slots=True)
class InterfacePatternRuleSnapshot:
    """Cached immutable representation of an interface pattern rule."""

    id: int
    vendor: str
    model_pattern: str
    model_match_type: str
    interface_pattern: str
    priority: int

    @property
    def specificity(self) -> int:
        """Return specificity score used to prefer model rules over vendor-only rules."""
        return 1 if self.model_pattern.strip() else 0

    def matches_device(self, device: Devices) -> bool:
        """Return whether this cached rule matches the provided device."""
        device_vendor = (device.vendor or "").strip().casefold()
        rule_vendor = self.vendor.strip().casefold()
        if not device_vendor or device_vendor != rule_vendor:
            return False
        return self._model_matches(device.model or "")

    def _model_matches(self, model: str) -> bool:
        """Return whether the model value satisfies this rule."""
        rule_model = self.model_pattern.strip()
        if not rule_model:
            return True

        model = model.strip()
        if not model:
            return False

        if self.model_match_type == DeviceInterfacePatternRule.MODEL_MATCH_EXACT:
            return model.casefold() == rule_model.casefold()
        if self.model_match_type == DeviceInterfacePatternRule.MODEL_MATCH_CONTAINS:
            return rule_model.casefold() in model.casefold()

        try:
            return re.search(rule_model, model, flags=re.IGNORECASE) is not None
        except re.error:
            return False


class InterfacePatternResolver:
    """Resolve the effective interface regexp for a device."""

    def __init__(self, rules: list[InterfacePatternRuleSnapshot]) -> None:
        """Initialize resolver with already loaded rules."""
        self._rules = sorted(
            rules,
            key=lambda rule: (rule.specificity, rule.priority, -rule.id),
            reverse=True,
        )

    @classmethod
    def from_cache(cls) -> "InterfacePatternResolver":
        """Create resolver from cached enabled rules or load rules from the database."""
        rules = cache.get(DeviceInterfacePatternRule.CACHE_KEY)
        if rules is None:
            rules = cls._load_rules()
            cache.set(DeviceInterfacePatternRule.CACHE_KEY, rules, timeout=None)
        return cls(rules)

    @classmethod
    def clear_cache(cls) -> None:
        """Clear cached rule snapshots."""
        cache.delete(DeviceInterfacePatternRule.CACHE_KEY)

    @staticmethod
    def _load_rules() -> list[InterfacePatternRuleSnapshot]:
        """Load enabled rules from the database as plain snapshots."""
        rows = DeviceInterfacePatternRule.objects.filter(enabled=True).values(
            "id",
            "vendor",
            "model_pattern",
            "model_match_type",
            "interface_pattern",
            "priority",
        )
        return [
            InterfacePatternRuleSnapshot(
                id=row["id"],
                vendor=row["vendor"],
                model_pattern=row["model_pattern"],
                model_match_type=row["model_match_type"],
                interface_pattern=row["interface_pattern"],
                priority=row["priority"],
            )
            for row in rows
        ]

    def resolve(self, device: Devices) -> str:
        """Return device override or the best matching rule pattern."""
        device_pattern = device.interface_pattern.strip()
        if device_pattern:
            return device_pattern

        for rule in self._rules:
            if rule.matches_device(device):
                return rule.interface_pattern.strip()
        return ""
