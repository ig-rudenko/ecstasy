from django.test import TestCase
from django.urls import reverse

from check.models import User
from maps.models import Maps


class TestPermissions(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            "maps.TestPermissions-superuser", "<EMAIL>"
        )
        cls.user = User.objects.create_user("maps.TestPermissions-user", "<EMAIL>")
        cls.map = Maps.objects.create(name="TestMap")

    def test_common_user_permissions(self):
        self.client.force_login(self.user)

        self.assertEqual(self.client.get(reverse("map-home")).status_code, 403)

        self.assertEqual(
            self.client.get(
                reverse("interactive-map-update", args=(self.map.id,))
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                reverse("interactive-map-layers", args=(self.map.id,))
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                reverse("interactive-map-render", args=(self.map.id,))
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                reverse("interactive-map-show", args=(self.map.id,))
            ).status_code,
            403,
        )

    def test_superuser_permissions(self):
        self.client.force_login(self.superuser)

        self.assertNotEqual(self.client.get(reverse("map-home")).status_code, 403)

        self.assertNotEqual(
            self.client.get(
                reverse("interactive-map-update", args=(self.map.id,))
            ).status_code,
            403,
        )
        self.assertNotEqual(
            self.client.get(
                reverse("interactive-map-layers", args=(self.map.id,))
            ).status_code,
            403,
        )
        self.assertNotEqual(
            self.client.get(
                reverse("interactive-map-render", args=(self.map.id,))
            ).status_code,
            403,
        )
        self.assertNotEqual(
            self.client.get(
                reverse("interactive-map-show", args=(self.map.id,))
            ).status_code,
            403,
        )
