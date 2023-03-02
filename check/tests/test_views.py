from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from check.models import Devices, DeviceGroup
import devicemanager as dm


# class ZabbixHostIdTest(TestCase):
#     @classmethod
#     def setUpTestData(cls):
#         dev = dm.Device.from_hostid("12345")
#         Devices.objects.create(name=dev.name, ip=dev.ip)
#
#     def test_zabbix_reverse_url(self):
#         resp = self.client.get(reverse("by-zabbix-hostid", args=("12345",)))
#         self.assertEqual(resp.status_code, 302)
#
#     def test_empty_hostid(self):
#         resp = self.client.get("/by-zabbix/")
#         self.assertEqual(resp.status_code, 404)
#
#     def test_valid_redirect_url(self):
#         resp = self.client.get("/by-zabbix/12345")
#         dev = dm.Device.from_hostid("12345")
#
#         self.assertRedirects(
#             response=resp,
#             expected_url=reverse("device_info", args=(dev.name,)),
#             status_code=302,
#             target_status_code=302,
#         )
#
#     def test_invalid_redirect_url(self):
#         resp = self.client.get("/by-zabbix/12346")
#         self.assertEqual(resp.status_code, 404)


class ShowDevicesNoAccessTest(TestCase):
    """
    @login_required
    def show_devices(request):

    Для пользователя у которого нет доступа к группе
    """

    @classmethod
    def setUpTestData(cls):
        test_user = User(username="test_user")
        test_user.set_password("test_password")
        test_user.save()

        g = DeviceGroup.objects.create(name="test")

        for i in range(1, 80):
            Devices.objects.create(name=f"Device-{i}", ip=f"10.0.0.{i}", group=g)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse("home"))
        self.assertRedirects(resp, "/accounts/login/?next=/")

    def test_logged_in_uses_correct_template(self):
        self.client.login(username="test_user", password="test_password")
        resp = self.client.get(reverse("home"))

        self.assertEqual(resp.context["user"], User.objects.get(username="test_user"))
        self.assertTemplateUsed(resp, "home.html")
