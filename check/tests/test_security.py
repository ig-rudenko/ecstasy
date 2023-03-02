from django.test import TestCase
from django.shortcuts import reverse


class NoAccessWithNoLogin(TestCase):
    def test_show_devices_home_page(self):
        self.assertRedirects(
            self.client.get(reverse("home")), expected_url="/accounts/login/?next=/"
        )

    def test_device_info_page(self):
        self.assertRedirects(
            self.client.get(reverse("device_info", kwargs={"name": "Device"})),
            expected_url="/accounts/login/?next=/device/Device",
        )

    def test_port_reload_page(self):
        self.assertRedirects(
            self.client.get(reverse("port_reload")),
            expected_url="/accounts/login/?next=/device/port/reload",
        )

    def test_show_bras_session_page(self):
        resp = self.client.get(reverse("show-session"))
        self.assertEqual(resp.status_code, 403)

    def test_cut_session_bras_page(self):
        resp = self.client.post(reverse("cut-session"))
        self.assertEqual(resp.status_code, 403)


class ResponseHeadersTest(TestCase):
    def test_security_headers(self):
        resp = self.client.get("/")
        self.assertEqual(resp.headers["X-Frame-Options"], "DENY")
        self.assertEqual(resp.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(resp.headers["Referrer-Policy"], "same-origin")
        self.assertEqual(resp.headers["Cross-Origin-Opener-Policy"], "same-origin")
