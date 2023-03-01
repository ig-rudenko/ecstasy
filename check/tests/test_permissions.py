from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from check import views
from check import models


class ReadPermissionsDecoratorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        u = User(username="test_user")
        u.set_password("password")
        u.save()

    def setUp(self) -> None:
        self.user = User.objects.get(username="test_user")
        self.request = RequestFactory()
        self.request.user = self.user

    def test_read_perms(self):
        @views.permission(models.Profile.READ)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")

    def test_reboot_with_read_perms(self):
        @views.permission(models.Profile.REBOOT)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)

    def test_up_down_with_read_perms(self):
        @views.permission(models.Profile.UP_DOWN)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)

    def test_bras_with_read_perms(self):
        @views.permission(models.Profile.BRAS)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)


class RebootPermissionsDecoratorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        u = User(username="test_user")
        u.set_password("password")
        u.save()
        u.profile.permissions = models.Profile.REBOOT
        u.profile.save()

    def setUp(self) -> None:
        self.user = User.objects.get(username="test_user")
        self.request = RequestFactory()
        self.request.user = self.user

    def test_read_perms(self):
        @views.permission(models.Profile.READ)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")

    def test_reboot_with_read_perms(self):
        @views.permission(models.Profile.REBOOT)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")

    def test_up_down_with_read_perms(self):
        @views.permission(models.Profile.UP_DOWN)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)

    def test_bras_with_read_perms(self):
        @views.permission(models.Profile.BRAS)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)


class UpDownPermissionsDecoratorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        u = User(username="test_user")
        u.set_password("password")
        u.save()
        u.profile.permissions = models.Profile.UP_DOWN
        u.profile.save()

    def setUp(self) -> None:
        self.user = User.objects.get(username="test_user")
        self.request = RequestFactory()
        self.request.user = self.user

    def test_read_perms(self):
        @views.permission(models.Profile.READ)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")

    def test_reboot_with_read_perms(self):
        @views.permission(models.Profile.REBOOT)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")

    def test_up_down_with_read_perms(self):
        @views.permission(models.Profile.UP_DOWN)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")

    def test_bras_with_read_perms(self):
        @views.permission(models.Profile.BRAS)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request).status_code, 403)


class BrasPermissionsDecoratorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        u = User(username="test_user")
        u.set_password("password")
        u.save()
        u.profile.permissions = models.Profile.BRAS
        u.profile.save()

    def setUp(self) -> None:
        self.user = User.objects.get(username="test_user")
        self.request = RequestFactory()
        self.request.user = self.user

    def test_read_perms(self):
        @views.permission(models.Profile.READ)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")

    def test_reboot_with_read_perms(self):
        @views.permission(models.Profile.REBOOT)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")

    def test_up_down_with_read_perms(self):
        @views.permission(models.Profile.UP_DOWN)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")

    def test_bras_with_read_perms(self):
        @views.permission(models.Profile.BRAS)
        def test_(request):
            return "func"

        self.assertEqual(test_(self.request), "func")
