from django.test import TestCase
from django.urls import reverse


class NoAccessWithNoLogin(TestCase):
    def test_show_bras_session_page(self):
        resp = self.client.get(reverse("devices-api:show-session"))
        self.assertEqual(resp.status_code, 401)

    def test_cut_session_bras_page(self):
        resp = self.client.post(reverse("devices-api:cut-session"))
        self.assertEqual(resp.status_code, 401)


class ResponseHeadersTest(TestCase):
    def test_security_headers(self):
        resp = self.client.get("/api/v1/devices")
        self.assertEqual(resp.headers["X-Frame-Options"], "SAMEORIGIN")
        self.assertEqual(resp.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(resp.headers["Referrer-Policy"], "same-origin")
        self.assertEqual(resp.headers["Cross-Origin-Opener-Policy"], "same-origin")
