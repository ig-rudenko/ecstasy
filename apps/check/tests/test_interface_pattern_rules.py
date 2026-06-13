from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.check.models import AuthGroup, DeviceGroup, DeviceInterfacePatternRule, Devices
from apps.check.services.device.interface_patterns import InterfacePatternResolver
from apps.check.services.device.interfaces_collector import DeviceInterfacesGather
from devicemanager.device import Interfaces


class InterfacePatternRuleTest(TestCase):
    """Test device interface pattern rules."""

    @classmethod
    def setUpTestData(cls):
        """Create a reusable Cisco device for resolver tests."""
        cls.group = DeviceGroup.objects.create(name="test")
        cls.auth_group = AuthGroup.objects.create(name="test", login="test", password="test")
        cls.device = Devices.objects.create(
            name="switch-1",
            ip="192.0.2.1",
            vendor=" Cisco ",
            model=" WS-C2960G-8TC-L ",
            group=cls.group,
            auth_group=cls.auth_group,
        )

    def setUp(self):
        """Clear resolver cache before each test."""
        InterfacePatternResolver.clear_cache()

    def test_rule_validates_interface_regexp(self):
        """Rule rejects invalid interface regexp."""
        rule = DeviceInterfacePatternRule(
            name="bad interface regexp",
            vendor="Cisco",
            interface_pattern="[Gi",
        )

        with self.assertRaises(ValidationError):
            rule.full_clean()

    def test_rule_validates_model_regexp(self):
        """Rule rejects invalid model regexp when regexp matching is selected."""
        rule = DeviceInterfacePatternRule(
            name="bad model regexp",
            vendor="Cisco",
            model_match_type=DeviceInterfacePatternRule.MODEL_MATCH_REGEXP,
            model_pattern="[WS",
            interface_pattern="^Gi",
        )

        with self.assertRaises(ValidationError):
            rule.full_clean()

    def test_rule_requires_vendor(self):
        """Rule without vendor is invalid, so there is no global rule."""
        rule = DeviceInterfacePatternRule(
            name="global rule",
            vendor="",
            interface_pattern="^Gi",
        )

        with self.assertRaises(ValidationError):
            rule.full_clean()

    def test_vendor_only_rule_matches_device(self):
        """Vendor-only rule applies to all models for that vendor."""
        DeviceInterfacePatternRule.objects.create(
            name="Cisco default",
            vendor="cisco",
            interface_pattern="^Gi",
        )

        pattern = InterfacePatternResolver.from_cache().resolve(self.device)

        self.assertEqual(pattern, "^Gi")

    def test_model_rule_overrides_vendor_only_rule(self):
        """Model-specific rule is preferred over vendor-only rule."""
        DeviceInterfacePatternRule.objects.create(
            name="Cisco default",
            vendor="Cisco",
            interface_pattern="^Fa",
            priority=100,
        )
        DeviceInterfacePatternRule.objects.create(
            name="Cisco 2960",
            vendor="Cisco",
            model_pattern="WS-C2960G-8TC-L",
            model_match_type=DeviceInterfacePatternRule.MODEL_MATCH_EXACT,
            interface_pattern="^Gi",
            priority=1,
        )

        pattern = InterfacePatternResolver.from_cache().resolve(self.device)

        self.assertEqual(pattern, "^Gi")

    def test_priority_selects_single_rule_between_same_specificity_rules(self):
        """Rules are not merged; one highest-priority rule is selected."""
        DeviceInterfacePatternRule.objects.create(
            name="lower priority",
            vendor="Cisco",
            model_pattern="2960G",
            model_match_type=DeviceInterfacePatternRule.MODEL_MATCH_CONTAINS,
            interface_pattern="^Fa",
            priority=1,
        )
        DeviceInterfacePatternRule.objects.create(
            name="higher priority",
            vendor="Cisco",
            model_pattern="2960G",
            model_match_type=DeviceInterfacePatternRule.MODEL_MATCH_CONTAINS,
            interface_pattern="^Gi",
            priority=10,
        )

        pattern = InterfacePatternResolver.from_cache().resolve(self.device)

        self.assertEqual(pattern, "^Gi")

    def test_device_pattern_overrides_rules(self):
        """Device-level pattern remains the strongest override."""
        self.device.interface_pattern = "^Fa"
        DeviceInterfacePatternRule.objects.create(
            name="Cisco default",
            vendor="Cisco",
            interface_pattern="^Gi",
        )

        pattern = InterfacePatternResolver.from_cache().resolve(self.device)

        self.assertEqual(pattern, "^Fa")

    def test_disabled_rules_are_ignored(self):
        """Disabled rules do not affect the resolved pattern."""
        DeviceInterfacePatternRule.objects.create(
            name="disabled",
            enabled=False,
            vendor="Cisco",
            interface_pattern="^Gi",
        )

        pattern = InterfacePatternResolver.from_cache().resolve(self.device)

        self.assertEqual(pattern, "")

    def test_resolver_does_not_query_database_after_rules_are_loaded(self):
        """Resolver serves repeated matches from already loaded rule data."""
        DeviceInterfacePatternRule.objects.create(
            name="Cisco default",
            vendor="Cisco",
            interface_pattern="^Gi",
        )
        resolver = InterfacePatternResolver.from_cache()

        with self.assertNumQueries(0):
            self.assertEqual(resolver.resolve(self.device), "^Gi")
            self.assertEqual(resolver.resolve(self.device), "^Gi")


class DeviceInterfacesGatherPatternTest(TestCase):
    """Test interface collection filtering with effective pattern rules."""

    @classmethod
    def setUpTestData(cls):
        """Create a reusable Cisco device for gather tests."""
        group = DeviceGroup.objects.create(name="test")
        auth_group = AuthGroup.objects.create(name="test", login="test", password="test")
        cls.device = Devices.objects.create(
            name="switch-1",
            ip="192.0.2.1",
            vendor="Cisco",
            model="WS-C2960G-8TC-L",
            group=group,
            auth_group=auth_group,
        )

    def setUp(self):
        """Clear resolver cache before each test."""
        InterfacePatternResolver.clear_cache()

    def test_collect_current_interfaces_uses_resolved_rule_pattern(self):
        """Current interface collection filters by the matched rule pattern."""
        DeviceInterfacePatternRule.objects.create(
            name="Cisco 2960",
            vendor="Cisco",
            model_pattern="WS-C2960G-8TC-L",
            model_match_type=DeviceInterfacePatternRule.MODEL_MATCH_EXACT,
            interface_pattern="^Gi",
        )
        collector = FakeDeviceCollector()
        gather = DeviceInterfacesGather(
            device=self.device,
            device_collector=collector,
            with_vlans=False,
        )

        interfaces = gather.collect_current_interfaces(make_session_global=False)

        self.assertEqual([interface["name"] for interface in interfaces.json()], ["Gi0/1"])


class FakeDeviceCollector:
    """Small fake collector for interface filtering tests."""

    def __init__(self):
        """Initialize empty interfaces collection."""
        self.interfaces = Interfaces()

    def collect_interfaces(self, **kwargs) -> None:
        """Set a deterministic interface list."""
        self.interfaces = Interfaces(
            [
                {"name": "Gi0/1", "status": "up", "description": "uplink"},
                {"name": "Vlan1", "status": "up", "description": "system"},
                {"name": "Null0", "status": "up", "description": "system"},
            ]
        )
