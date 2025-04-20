from unittest.mock import Mock

from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory

from check import models
from check.api.permissions import DevicePermission
from check.models import AuthGroup
from check.permissions import profile_permission


class ReadPermissionsDecoratorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.request = RequestFactory()
        cls.request.user = User.objects.create_user(username="read_permission_user", password="password")

    def test_read_perms(self):
        @profile_permission(models.Profile.READ)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")

    def test_reboot_with_read_perms(self):
        @profile_permission(models.Profile.REBOOT)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)

    def test_up_down_with_read_perms(self):
        @profile_permission(models.Profile.UP_DOWN)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)

    def test_bras_with_read_perms(self):
        @profile_permission(models.Profile.BRAS)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)


class RebootPermissionsDecoratorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.request = RequestFactory()
        user = User.objects.create_user(username="reboot_permission_user", password="password")
        cls.request.user = user
        user.profile.permissions = models.Profile.REBOOT
        user.profile.save()

    def test_read_perms(self):
        @profile_permission(models.Profile.READ)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")

    def test_reboot_with_read_perms(self):
        @profile_permission(models.Profile.REBOOT)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")

    def test_up_down_with_read_perms(self):
        @profile_permission(models.Profile.UP_DOWN)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)

    def test_bras_with_read_perms(self):
        @profile_permission(models.Profile.BRAS)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)


class UpDownPermissionsDecoratorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.request = RequestFactory()
        user = User.objects.create_user(username="up_down_permission_user", password="password")
        cls.request.user = user
        user.profile.permissions = models.Profile.UP_DOWN
        user.profile.save()

    def test_read_perms(self):
        @profile_permission(models.Profile.READ)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")

    def test_reboot_with_read_perms(self):
        @profile_permission(models.Profile.REBOOT)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")

    def test_up_down_with_read_perms(self):
        @profile_permission(models.Profile.UP_DOWN)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")

    def test_bras_with_read_perms(self):
        @profile_permission(models.Profile.BRAS)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)


class BrasPermissionsDecoratorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.request = RequestFactory()
        user = User.objects.create_user(username="bras_permission_user", password="password")
        cls.request.user = user
        user.profile.permissions = models.Profile.BRAS
        user.profile.save()

    def test_read_perms(self):
        @profile_permission(models.Profile.READ)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")

    def test_reboot_with_read_perms(self):
        @profile_permission(models.Profile.REBOOT)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")

    def test_up_down_with_read_perms(self):
        @profile_permission(models.Profile.UP_DOWN)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")

    def test_bras_with_read_perms(self):
        @profile_permission(models.Profile.BRAS)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")


class DevicePermissionTest(TestCase):
    """
    # Класс DevicePermissionTest проверяет,
    есть ли у пользователя разрешение на доступ к устройству на основе его доступа к группе устройств.
    """

    def setUp(self):
        self.permission = DevicePermission()
        self.device_group = models.DeviceGroup.objects.create(name="test_group")
        self.auth_group = AuthGroup.objects.create(name="test", login="test", password="test")

        self.device = models.Devices.objects.create(
            name="test_device", ip="20.20.20.20", group=self.device_group, auth_group=self.auth_group
        )
        self.user = User(
            username="device_permission_user",
            email="testuser@example.com",
            password="secret",
        )
        self.user.save()

    def tearDown(self) -> None:
        models.Profile.objects.all().delete()

    def test_user_without_access(self):
        # Пользователь без доступа к группам устройств не может получить разрешение
        request = Mock(user=self.user)
        result = self.permission.has_object_permission(request, None, self.device)
        self.assertFalse(result)

    def test_user_with_access(self):
        # Пользователь с доступом к группам устройств может получить разрешение
        self.user.profile.devices_groups.add(self.device_group)
        request = Mock(user=self.user)
        result = self.permission.has_object_permission(request, None, self.device)
        self.assertTrue(result)

    def test_device_with_different_group(self):
        # Пользователь с доступом к группам устройств не может получить разрешение на устройство,
        # которое принадлежит другой группе устройств
        other_device_group = models.DeviceGroup.objects.create(name="other_test_group")
        other_device = models.Devices.objects.create(
            name="other_test_device", group=other_device_group, ip="10.10.10.10", auth_group=self.auth_group
        )

        self.user.profile.devices_groups.add(self.device_group)
        result = self.permission.has_object_permission(Mock(user=self.user), None, other_device)
        self.assertFalse(result)
