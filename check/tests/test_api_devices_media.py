import pathlib
import shutil
from typing import ClassVar  # noqa: F401

from django.core.files import File
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..api.serializers import DeviceMediaSerializer
from ..models import AuthGroup, DeviceGroup, DeviceMedia, Devices, User


@override_settings(MEDIA_ROOT="/tmp/media")
class DeviceMediaListCreateAPIViewTestCase(APITestCase):
    user = None  # type: ClassVar[User]
    group = None  # type: ClassVar[DeviceGroup]
    device = None  # type: ClassVar[Devices]
    device_media = None  # type: ClassVar[DeviceMedia]
    auth_group = None  # type: ClassVar[AuthGroup]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(username="test_user", password="password")
        cls.group = DeviceGroup.objects.create(name="ASW")
        cls.auth_group = AuthGroup.objects.create(name="test", login="test", password="test")
        cls.user.profile.devices_groups.add(cls.group)
        cls.device = Devices.objects.create(
            ip="172.20.0.10",
            name="dev1",
            group=cls.group,
            auth_group=cls.auth_group,
        )
        with pathlib.Path(__file__).open("rb") as file:
            cls.device_media = DeviceMedia.objects.create(
                device=cls.device,
                file=File(file, name="file-name"),
                description="Описание файла",
            )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(pathlib.Path("/tmp/media"), ignore_errors=True)

    def setUp(self):
        self.client.force_login(user=self.user)

    def test_get_device_media_list(self):
        url = reverse(
            "devices-api:device-media-list-create",
            kwargs={"device_name": self.device.name},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), DeviceMediaSerializer([self.device_media], many=True).data)

    def test_create_device_media(self):
        url = reverse(
            "devices-api:device-media-list-create",
            kwargs={"device_name": self.device.name},
        )
        with pathlib.Path(__file__).open("rb") as f:
            response = self.client.post(
                url,
                {
                    "file": f,
                    "description": "test media",
                },
                format="multipart",
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.device.medias.count(), 2)
