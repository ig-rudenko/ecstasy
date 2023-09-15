from unittest.mock import MagicMock, Mock, patch

from django.test import SimpleTestCase

from devicemanager.multifactory import DeviceMultiFactory


class AbstractTestFactory(SimpleTestCase):
    def setUp(self) -> None:
        self.version_output = self.get_output_from_show_version_command()
        self.auth_dict = {
            "login": "user",
            "password": "passwd",
            "privilege_mode_password": "secret",
        }
        self.fake_session = self.get_fake_session()

    @staticmethod
    def get_device_class():
        pass

    @staticmethod
    def get_output_from_show_version_command() -> str:
        pass

    @staticmethod
    def get_fake_session():
        fake_session = MagicMock()
        fake_session.sendline.return_value = ""
        fake_session.before.decode.return_value = ""
        fake_session.expect.return_value = 0
        return fake_session

    def _is_need_skip(self) -> bool:
        if not self.get_device_class() or not self.get_output_from_show_version_command():
            if self.__class__ != AbstractTestFactory:
                raise NotImplemented(
                    "Необходимо переопределить методы "
                    "`get_device_class` и `get_output_from_show_version_command`"
                )
            return True
        return False

    @patch("devicemanager.multifactory.DeviceMultiFactory.send_command")
    def test_factory_return_class(self, send_command: Mock):
        if self._is_need_skip():
            return

        send_command.return_value = self.version_output

        device = DeviceMultiFactory.get_device(
            session=self.fake_session,
            ip="10.10.10.10",
            snmp_community="",
            auth=self.auth_dict,
        )
        self.assertEqual(device.__class__, self.get_device_class())

    @patch("devicemanager.multifactory.DeviceMultiFactory.send_command")
    def test_factory_device_attributes(self, send_command: Mock):
        if self._is_need_skip():
            return

        send_command.return_value = self.version_output
        ip = "10.10.10.10"
        snmp_community = "oifihasdhf"

        device = DeviceMultiFactory.get_device(
            session=self.fake_session,
            ip=ip,
            snmp_community=snmp_community,
            auth=self.auth_dict,
        )
        self.assertEqual(device.auth, self.auth_dict)
        self.assertEqual(device.ip, ip)
        self.assertEqual(device.snmp_community, snmp_community)
