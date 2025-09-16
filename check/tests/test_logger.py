from unittest.mock import Mock, patch

from django.test import TestCase

from ..logging import log
from ..models import AuthGroup, Bras, DeviceGroup, Devices, User, UsersActions


class TestLog(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="test_log_user")
        self.devices = Devices.objects.create(
            name="test_device",
            ip="192.168.0.1",
            group=DeviceGroup.objects.create(name="group"),
            auth_group=AuthGroup.objects.create(
                name="auth group", login="login", password="password", secret="secret"
            ),
        )
        self.bras = Bras.objects.create(name="test_bras", ip="192.168.10.2")

    @patch("check.logger.django_actions_logger.info")
    def test_invalid_inputs(self, mock_logger_info: Mock):
        # Проверка, что при неверных (некорректных) входных данных, функция log не записывает в базу
        log(None, None, "123")  # type: ignore
        self.assertEqual(UsersActions.objects.count(), 0)
        mock_logger_info.assert_called_with("| NO DB | None       | None            | 123")

    @patch("check.logger.django_actions_logger.info")
    def test_log_device(self, mock_logger_info: Mock):
        # Проверка, что для объекта models.Devices создается запись в базе данных и лог-файле

        log(self.user, self.devices, "test_device_action")
        device_log = UsersActions.objects.get(device=self.devices)
        self.assertEqual(device_log.action, "test_device_action")
        mock_logger_info.assert_called_with(
            f"| {self.user.username:<10} | {self.devices.name} ({self.devices.ip}) | test_device_action"
        )

    @patch("check.logger.django_actions_logger.info")
    def test_log_bras(self, mock_logger_info: Mock):
        # Проверка, что для объекта models.Bras создается запись в базе данных и лог-файле

        log(self.user, self.bras, "test_bras_action")
        bras_log = UsersActions.objects.get(action__contains="test_bras_action")
        self.assertEqual(bras_log.action, f"{self.bras} | test_bras_action")
        mock_logger_info.assert_called_with(f"| {self.user.username:<10} | {self.bras} | test_bras_action")

    @patch("check.logger.django_actions_logger.info")
    def test_very_long_log_bras(self, mock_logger_info: Mock):
        # Проверка, что можно передавать любую длину лога. Запись в базе будет создана без ошибок

        log_str = "test_bras_action" * 50  # Слишком длинный лог
        # Максимальная длина поля в базе
        action_max_length = UsersActions._meta.get_field("action").max_length
        # Строка, которая должна быть сохранена в базе
        log_str_in_db = f"{self.bras} | {log_str}"[:action_max_length]

        log(self.user, self.bras, log_str)  # Делаем лог

        bras_log = UsersActions.objects.get(action=log_str_in_db)
        self.assertEqual(bras_log.action, log_str_in_db)
        mock_logger_info.assert_called_with(f"| {self.user.username:<10} | {self.bras} | {log_str}")
