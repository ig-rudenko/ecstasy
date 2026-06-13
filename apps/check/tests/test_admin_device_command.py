import re

from django.contrib import admin
from django.test import TestCase

from ..admin import DeviceCommandAdmin, DeviceCommandModelForm
from ..models import AuthGroup, DeviceCommand, DeviceGroup, Devices


class DeviceCommandModelFormTestCase(TestCase):
    """Test command template validation in the admin form."""

    @classmethod
    def setUpTestData(cls):
        """Create a vendor available in the command form."""
        group = DeviceGroup.objects.create(name="ASW")
        auth_group = AuthGroup.objects.create(name="test", login="test", password="test")
        Devices.objects.create(
            ip="192.0.2.1",
            name="switch-1",
            vendor="D-Link",
            group=group,
            auth_group=auth_group,
        )

    def build_form(self, command: str) -> DeviceCommandModelForm:
        """Return a bound form with the given command template."""
        return DeviceCommandModelForm(
            data={
                "name": "Test command",
                "description": "",
                "command": command,
                "device_vendor": "D-Link",
                "model_regexp": "",
                "valid_regexp": "",
                "perm_groups": [],
            }
        )

    def test_accepts_macros_supported_by_command_service(self):
        """Accept every macro form handled during command execution."""
        form = self.build_form(
            r"show {port#uplink} {ip} {mac#client} {number:1:4094#vlan} " r"{word#state} {if:{Y/n\}:y}"
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_accepts_escaped_literal_opening_brace(self):
        """Accept an escaped opening brace as plain command text."""
        commands = (r"show switch \{", r"show version \{}", r"show version \{x}")

        for command in commands:
            with self.subTest(command=command):
                form = self.build_form(command)
                self.assertTrue(form.is_valid(), form.errors)

    def test_rejects_unescaped_or_incorrectly_escaped_opening_brace(self):
        """Reject every unescaped opening brace that does not start a known macro."""
        commands = (
            "show switch {",
            r"show switch \\{",
            r"show version {s\}",
            "show version {}",
            "show version {x}",
            r"show version \\{x}",
        )

        for command in commands:
            with self.subTest(command=command):
                form = self.build_form(command)
                self.assertFalse(form.is_valid())
                self.assertIn("command", form.errors)

    def test_rejects_unknown_macro(self):
        """Reject a macro that would otherwise be sent to the device unchanged."""
        form = self.build_form("show interface {porrt}")

        self.assertFalse(form.is_valid())
        self.assertIn("command", form.errors)

    def test_rejects_number_macro_with_reversed_range(self):
        """Reject a numeric macro whose range cannot accept any value."""
        form = self.build_form("show vlan {number:4094:1}")

        self.assertFalse(form.is_valid())
        self.assertIn("command", form.errors)

    def test_rejects_condition_macro_with_invalid_regexp(self):
        """Reject an invalid prompt regexp before command execution."""
        form = self.build_form("reload {if:[confirm:y}")

        self.assertFalse(form.is_valid())
        self.assertIn("command", form.errors)


class DeviceCommandAdminTestCase(TestCase):
    """Test command macro highlighting in the admin list."""

    def setUp(self):
        """Create the model admin used to render command text."""
        self.model_admin = DeviceCommandAdmin(DeviceCommand, admin.site)

    def render_command(self, command: str) -> str:
        """Render one unsaved command with the admin display method."""
        obj = DeviceCommand(name="Test", command=command, device_vendor="D-Link")
        return str(self.model_admin.command_html(obj))

    def test_highlights_regular_and_condition_macros_separately(self):
        """Use separate visual styles and detailed tooltips for if macros."""
        html = self.render_command(r"show {port#uplink} {if:\{Y/N\}:Y}")

        self.assertIn('class="device-command-macro"', html)
        self.assertIn('class="device-command-macro device-command-macro-if"', html)
        self.assertIn("ожидать регулярное выражение", html)
        self.assertIn(r"\{Y/N\}", html)

    def test_highlights_macro_names_with_consistent_distinct_colors(self):
        """Use one color per name and different colors for different names."""
        html = self.render_command("show {port#uplink} {word#uplink} {number#vlan}")
        matches = re.findall(
            r'class="device-command-macro-name" style="([^"]+)">([^<]+)</span>',
            html,
        )

        self.assertEqual(3, len(matches))
        self.assertEqual(matches[0][0], matches[1][0])
        self.assertNotEqual(matches[0][0], matches[2][0])

    def test_escapes_command_html(self):
        """Do not render command text as executable HTML."""
        html = self.render_command(r"show <script>alert(1)</script> \{port}")

        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn('class="device-command-macro"', html)
