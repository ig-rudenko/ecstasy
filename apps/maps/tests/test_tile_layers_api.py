import hashlib

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.maps.apps import create_default_tile_layers
from apps.maps.models import TileLayer


class TileLayerAPITests(APITestCase):
    """Тесты API подложек географических карт."""

    def setUp(self) -> None:
        """Создать пользователя и URL endpoint."""

        self.user = get_user_model().objects.create_user(username="operator", password="password")
        self.url = reverse("maps-api:tile-layers")
        TileLayer.objects.all().delete()

    def test_tile_layers_requires_authentication(self):
        """Анонимный пользователь не может получить список подложек."""

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_tile_layers_requires_maps_permission(self):
        """Пользователь без `accounting.can_view_maps` не может получить список подложек."""

        self.client.force_authenticate(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_tile_layers_returns_available_layers_for_user_with_maps_permission(self):
        """Пользователь с `accounting.can_view_maps` получает список доступных подложек."""

        self.user.user_permissions.add(Permission.objects.get(codename="can_view_maps"))
        TileLayer.objects.create(name="Custom", url="https://example.test/{z}/{x}/{y}.png", crs="EPSG:3857")
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            [{"name": "Custom", "url": "https://example.test/{z}/{x}/{y}.png", "crs": "EPSG:3857"}],
        )

    def test_create_default_tile_layers_is_idempotent(self):
        """Создание подложек по умолчанию можно безопасно вызывать повторно."""

        create_default_tile_layers(sender=None)
        create_default_tile_layers(sender=None)

        self.assertEqual(TileLayer.objects.count(), 2)

    def test_tile_layer_keeps_long_url_and_updates_its_hash(self):
        """Длинный URL сохраняется полностью, а уникальность обеспечивается его хэшем."""

        url = "https://tiles.example.test/" + "a" * 1900
        tile_layer = TileLayer.objects.create(name="Long URL", url=url, crs="EPSG:3857")

        self.assertEqual(tile_layer.url, url)
        self.assertEqual(tile_layer.url_hash, hashlib.sha256(url.encode("utf-8")).hexdigest())

        updated_url = url + "/updated"
        tile_layer.url = updated_url
        tile_layer.save()

        self.assertEqual(tile_layer.url_hash, hashlib.sha256(updated_url.encode("utf-8")).hexdigest())
