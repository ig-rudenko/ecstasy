from django.urls import reverse
from rest_framework.test import APITestCase

from ..models import User


class CutBrasSessionTest(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_superuser(username="test_user", password="password")
        cls.url = reverse("devices-api:cut-session")

    def test_cut_bras_session(self):
        self.client.force_login(user=self.user)
        response = self.client.post(self.url, {"mac": "10:00:00:00:00:00"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.data, {"errors": [], "portReloadStatus": "SKIP"})

    def test_cut_bras_session_empty_port_device(self):
        self.client.force_login(user=self.user)
        response = self.client.post(
            self.url, {"mac": "10:00:00:00:00:00", "device": "", "port": ""}, format="json"
        )
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.data, {"errors": [], "portReloadStatus": "SKIP"})
