from django.http import HttpRequest
from django.test import TestCase
from django.contrib.auth.models import User, Group, Permission

from ..protected_serve import MapMediaServeLimitation


class MapMediaServeLimitationTestCase(TestCase):
    def test_check_with_superuser(self):
        request = HttpRequest()
        request.user = User.objects.create_user(username="test", password="test", is_superuser=True)
        self.assertTrue(MapMediaServeLimitation.check(request, "map_layer_files"))

    def test_check_with_groups_permission(self):
        group = Group.objects.create(name="group")
        permission = Permission.objects.get(codename="view_layers")
        group.permissions.add(permission)

        request = HttpRequest()
        request.user = User.objects.create_user(username="test", password="test")
        request.user.groups.add(group)

        self.assertTrue(MapMediaServeLimitation.check(request, "map_layer_files"))

    def test_check_without_permission(self):
        group = Group.objects.create(name="group")

        request = HttpRequest()
        request.user = User.objects.create_user(username="test", password="test")
        request.user.groups.add(group)

        self.assertFalse(MapMediaServeLimitation.check(request, "map_layer_files"))

    def test_check_not_map_layer_files(self):
        request = HttpRequest()
        request.user = User.objects.create_user(username="test", password="test", is_superuser=False)
        self.assertTrue(MapMediaServeLimitation.check(request, "not_map_layer_files"))
