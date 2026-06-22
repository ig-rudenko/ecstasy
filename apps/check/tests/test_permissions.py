from unittest.mock import Mock

from django.contrib.auth.models import Group, User
from django.test import RequestFactory, TestCase

from .. import models
from ..api.permissions import DevicePermission
from ..models import AccessGroup, AuthGroup
from ..permissions import profile_permission


class NoDevicePermissionsDecoratorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.request = RequestFactory()
        cls.request.user = User.objects.create_user(username="no_device_permission_user", password="password")

    def test_reboot_without_perms(self):
        @profile_permission(models.Profile.INTERFACE_REBOOT)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)  # type: ignore

    def test_up_down_without_perms(self):
        @profile_permission(models.Profile.INTERFACE_UP_DOWN)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)  # type: ignore

    def test_bras_without_perms(self):
        @profile_permission(models.Profile.BRAS_READ)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)  # type: ignore

    def test_bras_write_without_perms(self):
        @profile_permission(models.Profile.BRAS_READ_WRITE)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)  # type: ignore


class RebootPermissionsDecoratorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.request = RequestFactory()
        user = User.objects.create_user(username="reboot_permission_user", password="password")
        cls.request.user = user
        user.profile.set_permission(models.Profile.INTERFACE_REBOOT)

    def test_reboot_perms(self):
        @profile_permission(models.Profile.INTERFACE_REBOOT)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")

    def test_up_down_with_reboot_perms(self):
        @profile_permission(models.Profile.INTERFACE_UP_DOWN)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)  # type: ignore

    def test_bras_with_reboot_perms(self):
        @profile_permission(models.Profile.BRAS_READ)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)  # type: ignore


class UpDownPermissionsDecoratorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.request = RequestFactory()
        user = User.objects.create_user(username="up_down_permission_user", password="password")
        cls.request.user = user
        user.profile.set_permission(models.Profile.INTERFACE_UP_DOWN)

    def test_reboot_with_up_down_perms(self):
        @profile_permission(models.Profile.INTERFACE_REBOOT)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)  # type: ignore

    def test_up_down_perms(self):
        @profile_permission(models.Profile.INTERFACE_UP_DOWN)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")

    def test_bras_with_up_down_perms(self):
        @profile_permission(models.Profile.BRAS_READ)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)  # type: ignore


class BrasPermissionsDecoratorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.request = RequestFactory()
        user = User.objects.create_user(username="bras_permission_user", password="password")
        cls.request.user = user
        user.profile.set_permission(models.Profile.BRAS_READ_WRITE)

    def test_reboot_with_bras_perms(self):
        @profile_permission(models.Profile.INTERFACE_REBOOT)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)  # type: ignore

    def test_up_down_with_bras_perms(self):
        @profile_permission(models.Profile.INTERFACE_UP_DOWN)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)  # type: ignore

    def test_bras_read_with_bras_write_perms(self):
        @profile_permission(models.Profile.BRAS_READ)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)  # type: ignore

    def test_bras_write_perms(self):
        @profile_permission(models.Profile.BRAS_READ_WRITE)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")

    def test_bras_read_endpoint_accepts_bras_write_perms(self):
        @profile_permission(models.Profile.BRAS_READ, models.Profile.BRAS_READ_WRITE)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")


class BrasReadPermissionsDecoratorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.request = RequestFactory()
        user = User.objects.create_user(username="bras_read_permission_user", password="password")
        cls.request.user = user
        user.profile.set_permission(models.Profile.BRAS_READ)

    def test_bras_read_perms(self):
        @profile_permission(models.Profile.BRAS_READ)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")

    def test_bras_write_with_bras_read_perms(self):
        @profile_permission(models.Profile.BRAS_READ_WRITE)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)  # type: ignore


class ConfigPermissionsDecoratorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.request = RequestFactory()
        user = User.objects.create_user(username="config_view_permission_user", password="password")
        cls.request.user = user
        user.profile.set_permission(models.Profile.CONFIG_VIEW)

    def test_config_view_perms(self):
        @profile_permission(models.Profile.CONFIG_VIEW)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")

    def test_config_collect_with_config_view_perms(self):
        @profile_permission(models.Profile.CONFIG_COLLECT)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)  # type: ignore

    def test_config_delete_with_config_view_perms(self):
        @profile_permission(models.Profile.CONFIG_DELETE)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)  # type: ignore


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
        result = self.permission.has_object_permission(request, None, self.device)  # type: ignore
        self.assertFalse(result)

    def test_user_with_access(self):
        # Пользователь с доступом к группам устройств может получить разрешение
        self.user.profile.devices_groups.add(self.device_group)
        request = Mock(user=self.user)
        result = self.permission.has_object_permission(request, None, self.device)  # type: ignore
        self.assertTrue(result)

    def test_device_with_different_group(self):
        # Пользователь с доступом к группам устройств не может получить разрешение на устройство,
        # которое принадлежит другой группе устройств
        other_device_group = models.DeviceGroup.objects.create(name="other_test_group")
        other_device = models.Devices.objects.create(
            name="other_test_device", group=other_device_group, ip="10.10.10.10", auth_group=self.auth_group
        )

        self.user.profile.devices_groups.add(self.device_group)
        result = self.permission.has_object_permission(Mock(user=self.user), None, other_device)  # type: ignore
        self.assertFalse(result)

    def test_device_permission_with_only_acl_allow(self):
        acl = AccessGroup.objects.create(name="test_acl")
        acl.users.add(self.user)
        acl.devices.add(self.device)

        result = self.permission.has_object_permission(Mock(user=self.user), None, self.device)
        self.assertTrue(result)

    def test_device_permission_with_group_allow_but_acl_deny(self):
        acl = AccessGroup.objects.create(name="test_acl")
        acl.users.add(self.user)

        # Группа оборудования разрешена пользователю
        self.user.profile.devices_groups.add(self.device_group)
        # Но ACL запрещает доступ на конкретное оборудование.
        acl.forbidden_devices.add(self.device)

        # ACL имеет приоритет.
        result = self.permission.has_object_permission(Mock(user=self.user), None, self.device)
        self.assertFalse(result)

    def test_device_permission_with_user_group_in_acl_allow(self):
        acl = AccessGroup.objects.create(name="test_acl")

        # Создаём группу для пользователя
        user_group = Group.objects.create(name="test_user_group")
        # Добавляем в неё пользователя.
        user_group.user_set.add(self.user)

        acl.user_groups.add(user_group)  # Вешаем ACL на группу пользователя
        acl.devices.add(self.device)  # ACL разрешает доступ на оборудование.

        # Пользователь должен иметь доступ, так как его группе доступен ACL и он разрешает доступ.
        result = self.permission.has_object_permission(Mock(user=self.user), None, self.device)
        self.assertTrue(result)

    def test_device_permission_with_user_group_in_acl_deny(self):
        acl = AccessGroup.objects.create(name="test_acl")

        # Добавляем доступ пользователю на группу оборудования.
        self.user.profile.devices_groups.add(self.device_group)

        # Создаём группу пользователя.
        user_group = Group.objects.create(name="test_user_group")
        # Добавляем в неё пользователя.
        user_group.user_set.add(self.user)

        acl.user_groups.add(user_group)  # Вешаем ACL на группу пользователя
        acl.forbidden_devices.add(self.device)  # ACL запрещает доступ на конкретное оборудование.

        # Пользователь НЕ должен иметь доступ, так как его группе доступен ЗАПРЕЩЁН.
        result = self.permission.has_object_permission(Mock(user=self.user), None, self.device)
        self.assertFalse(result)
