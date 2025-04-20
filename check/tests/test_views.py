from django.contrib.auth.models import User
from django.test import TestCase

from check.models import Devices, DeviceGroup, AuthGroup


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
        auth_group = AuthGroup.objects.create(name="test", login="test", password="test")

        for i in range(1, 4):
            Devices.objects.create(
                name=f"DeviceManager-{i}", ip=f"10.0.0.{i}", group=g, auth_group=auth_group
            )
