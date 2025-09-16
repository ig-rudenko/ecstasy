import copy
import json
from pprint import pprint

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from check.models import AuthGroup, DeviceGroup, Devices
from gpon.tests.data import CREATE_TECH_DATA
from net_tools.models import DevicesInfo


class TestTechDataAPIView(APITestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_superuser(username="test_user", password="password")
        self.device = Devices.objects.create(
            auth_group=AuthGroup.objects.create(name="test", login="login", password="password"),
            group=DeviceGroup.objects.create(name="test"),
            ip="10.10.10.10",
            name="device1",
        )
        DevicesInfo.objects.create(
            dev=self.device,
            interfaces=json.dumps(
                [
                    {"Interface": "0/1/1"},
                    {"Interface": "0/1/2"},
                    {"Interface": "0/1/3"},
                ]
            ),
        )

        self.data = copy.deepcopy(CREATE_TECH_DATA)

    def test_api(self):
        self.client.force_login(self.user)
        resp = self.client.post(path=reverse("gpon-api:tech-data"), data=self.data, format="json")
        self.assertEqual(resp.status_code, 201)

        self.data["oltState"]["devicePort"] = "0/1/1"
        resp = self.client.post(path=reverse("gpon-api:tech-data"), data=self.data, format="json")
        self.assertEqual(resp.status_code, 201)

        self.data["oltState"]["devicePort"] = "0/1/2"
        for _ in range(8):
            self.client.post(path=reverse("gpon-api:tech-data"), data=self.data, format="json")

        with self.assertNumQueries(14):
            resp = self.client.get(path=reverse("gpon-api:tech-data"))
            self.assertEqual(resp.status_code, 200)
            pprint(resp.data)
