from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from check.models import Devices, DeviceGroup


class ShowDevicesNoAccessTest(TestCase):
    """
    @login_required
    def show_devices(request):

    Для пользователя у которого нет доступа к группе
    """

    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(username="show_devices_test_user", password="test_password")
        g = DeviceGroup.objects.create(name="test")

        for i in range(1, 4):
            Devices.objects.create(name=f"DeviceManager-{i}", ip=f"10.0.0.{i}", group=g)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse("home"))
        self.assertRedirects(resp, "/accounts/login/?next=/")

    def test_logged_in_uses_correct_template(self):
        self.client.login(username="show_devices_test_user", password="test_password")
        resp = self.client.get(reverse("home"))

        self.assertEqual(resp.context["user"], User.objects.get(username="show_devices_test_user"))
        self.assertTemplateUsed(resp, "home.html")
