from typing import ClassVar  # noqa: F401

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from check.models import User
from ring_manager.models import TransportRing


class TestPermissions(TestCase):
    superuser = None  # type: ClassVar[User]
    user = None  # type: ClassVar[User]
    transport_ring_api_urls = None  # type: ClassVar[list[str]]
    access_ring_api_urls = None  # type: ClassVar[list[str]]
    transport_ring = None  # type: ClassVar[TransportRing]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.superuser = User.objects.create_superuser("ring_manager.TestPermissions-superuser", "<EMAIL>")
        cls.user = User.objects.create_user("ring_manager.TestPermissions-user", "<EMAIL>")
        transport_ring: TransportRing = TransportRing.objects.create(
            name="TestTransportRing", description="TestTransportRing"
        )

        cls.transport_ring_api_urls = [
            reverse("ring-manager:api:transport-ring-detail", args=(transport_ring.name,)),
            reverse("ring-manager:api:transport-ring-status", args=(transport_ring.name,)),
            reverse("ring-manager:api:transport-ring-solutions", args=(transport_ring.name,)),
            reverse("ring-manager:api:transport-ring-solutions-last", args=(transport_ring.name,)),
            reverse("ring-manager:api:transport-rings"),
        ]

        cls.access_ring_api_urls = [
            reverse("ring-manager:api:access-rings"),
            reverse("ring-manager:api:access-ring-detail", args=("test",)),
        ]

        cls.transport_ring = transport_ring

    def test_common_user_permission(self) -> None:
        self.client.force_login(self.user)

        self.assertEqual(self.client.get(reverse("ring-manager:home")).status_code, 200)
        self.assertEqual(self.client.get(reverse("ring-manager:transport-rings")).status_code, 403)
        self.assertEqual(self.client.get(reverse("ring-manager:access-rings")).status_code, 403)

    def test_superuser_permission(self) -> None:
        self.client.force_login(self.superuser)

        self.assertEqual(self.client.get(reverse("ring-manager:home")).status_code, 200)
        self.assertNotEqual(self.client.get(reverse("ring-manager:transport-rings")).status_code, 403)
        self.assertNotEqual(self.client.get(reverse("ring-manager:access-rings")).status_code, 403)

    def test_common_user_permission_api(self) -> None:
        self.client.force_login(self.user)
        for url in self.transport_ring_api_urls + self.access_ring_api_urls:
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_api_with_access_ring_user_permission(self) -> None:
        self.user.user_permissions.add(Permission.objects.get(codename="access_rings"))
        self.client.force_login(self.user)
        for url in self.access_ring_api_urls:
            self.assertNotEqual(self.client.get(url).status_code, 403, url)

    def test_api_with_access_transport_ring_user_permission(self) -> None:
        self.user.user_permissions.add(Permission.objects.get(codename="access_transport_rings"))
        self.transport_ring.users.add(self.user)

        self.client.force_login(self.user)
        for url in self.transport_ring_api_urls:
            self.assertNotEqual(self.client.get(url).status_code, 403, url)

    def test_superuser_permission_api(self) -> None:
        self.client.force_login(self.superuser)
        for url in self.transport_ring_api_urls + self.access_ring_api_urls:
            self.assertNotEqual(self.client.get(url).status_code, 403, url)
