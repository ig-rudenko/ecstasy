from unittest.mock import MagicMock, Mock, patch

from django.test import SimpleTestCase

from devicemanager.multifactory import DeviceMultiFactory
from devicemanager.vendors.base.types import DeviceAuthDict


class AbstractTestFactory(SimpleTestCase):
    """
    Класс представляет собой шаблон для тестирования абстрактных фабрик создания объектов устройств
    и тестирования их атрибутов и поведения.
    """

    def setUp(self) -> None:
        self.version_output = self.get_output_from_show_version_command()
        self.auth_dict: DeviceAuthDict = {
            "login": "user",
            "password": "passwd",
            "privilege_mode_password": "secret",
        }
        self.fake_session = self.get_fake_session()

    @staticmethod
    def get_device_class():
        """
        Возвращает класс, объект которого должен вернуться из фабрики
        """
        return

    @staticmethod
    def get_output_from_show_version_command() -> str:
        """
        Возвращает выходные данные от ввода на оборудовании команды «show version» в виде строки.
        """
        return ""

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
                raise NotImplementedError(
                    "Необходимо переопределить методы "
                    "`get_device_class` и `get_output_from_show_version_command`"
                )
            return True
        return False

    @patch("devicemanager.multifactory.DeviceMultiFactory.send_command")
    def test_factory_return_class(self, send_command: Mock):
        """
        Функция проверяет возвращаемый класс устройства, созданного с использованием фабричного метода.

        :param send_command: Параметр send_command является объектом Mock.
         Используется для имитации поведения метода send_command.
        """
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
        """
        Функция проверяет атрибуты устройства, созданного с помощью класса DeviceMultiFactory.

        :param send_command: Параметр send_command является объектом Mock.
         Используется для имитации поведения метода send_command.
        """
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
