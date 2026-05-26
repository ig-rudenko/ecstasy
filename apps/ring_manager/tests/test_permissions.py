from typing import ClassVar

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.check.models import User

from ..models import TransportRing


class TestPermissions(TestCase):
    superuser: ClassVar[User | None] = None
    user: ClassVar[User | None] = None
    transport_ring_api_urls: ClassVar[list[str] | None] = None
    access_ring_api_urls: ClassVar[list[str] | None] = None
    transport_ring: ClassVar[TransportRing | None] = None

    @classmethod
    def setUpTestData(cls) -> None:
        cls.superuser = User.objects.create_superuser("ring_manager.TestPermissions-superuser", "<EMAIL>")
        cls.user = User.objects.create_user("ring_manager.TestPermissions-user", "<EMAIL>")
        transport_ring: TransportRing = TransportRing.objects.create(
            name="TestTransportRing", description="TestTransportRing"
        )

        cls.transport_ring_api_urls = [
            reverse("ring-manager-api:transport-ring-detail", args=(transport_ring.name,)),
            reverse("ring-manager-api:transport-ring-status", args=(transport_ring.name,)),
            reverse("ring-manager-api:transport-ring-solutions", args=(transport_ring.name,)),
            reverse("ring-manager-api:transport-ring-solutions-last", args=(transport_ring.name,)),
            reverse("ring-manager-api:transport-rings"),
        ]

        cls.access_ring_api_urls = [
            reverse("ring-manager-api:access-rings"),
            reverse("ring-manager-api:access-ring-detail", args=("test",)),
        ]

        cls.transport_ring = transport_ring

    def test_common_user_permission_api(self) -> None:
        assert self.user is not None
        assert self.transport_ring_api_urls is not None
        assert self.access_ring_api_urls is not None
        self.client.force_login(self.user)
        for url in self.transport_ring_api_urls + self.access_ring_api_urls:
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_api_with_access_ring_user_permission(self) -> None:
        assert self.user is not None
        assert self.access_ring_api_urls is not None
        self.user.user_permissions.add(Permission.objects.get(codename="access_rings"))
        self.client.force_login(self.user)
        for url in self.access_ring_api_urls:
            self.assertNotEqual(self.client.get(url).status_code, 403, url)

    def test_api_with_access_transport_ring_user_permission(self) -> None:
        assert self.user is not None
        assert self.transport_ring is not None
        assert self.transport_ring_api_urls is not None
        self.user.user_permissions.add(Permission.objects.get(codename="access_transport_rings"))
        self.transport_ring.users.add(self.user)

        self.client.force_login(self.user)
        for url in self.transport_ring_api_urls:
            self.assertNotEqual(self.client.get(url).status_code, 403, url)

    def test_superuser_permission_api(self) -> None:
        assert self.superuser is not None
        assert self.transport_ring_api_urls is not None
        assert self.access_ring_api_urls is not None
        self.client.force_login(self.superuser)
        for url in self.transport_ring_api_urls + self.access_ring_api_urls:
            self.assertNotEqual(self.client.get(url).status_code, 403, url)
