from typing import ClassVar  # noqa: F401
from unittest.mock import MagicMock, patch, Mock

import orjson
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from devicemanager.vendors.base.device import BaseDevice
from devicemanager.vendors.base.types import SetDescriptionResult
from net_tools.models import DevicesInfo, VlanName
from ..models import Devices, DeviceGroup, User, UsersActions, AuthGroup


class PortControlAPIViewTestCase(APITestCase):
    user = None  # type: ClassVar[User]
    group = None  # type: ClassVar[DeviceGroup]
    device = None  # type: ClassVar[Devices]
    url = None  # type: ClassVar[str]
    auth_group = None  # type: ClassVar[AuthGroup]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(username="test_user", password="password")
        cls.group = DeviceGroup.objects.create(name="ASW")
        cls.user.profile.devices_groups.add(cls.group)
        cls.auth_group = AuthGroup.objects.create(
            name="auth_group",
            login="auth_group",
            password="auth_group",
        )
        cls.device = Devices.objects.create(
            ip="10.255.255.255",
            name="dev1",
            group=cls.group,
        )
        DevicesInfo.objects.create(
            dev=cls.device,
            interfaces=orjson.dumps(
                [
                    {
                        "Interface": "Fa1/0/1",
                        "Status": "up",
                        "Description": "desc1",
                        "VLAN's": [1, 2],
                    },
                    {
                        "Interface": "Gi0/1",
                        "Status": "up",
                        "Description": "CORE-1",
                        "VLAN's": [3, 4],
                    },
                ]
            ).decode(),
        )
        cls.url = reverse("devices-api:port-control", args=(cls.device.name,))

    def test_no_auth(self):
        resp = self.client.post(
            self.url,
            data={"port": "Fa1/0/1", "status": "down", "save": True},
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_no_profile_access(self):
        self.client.force_login(user=self.user)
        resp = self.client.post(
            self.url,
            data={"port": "Fa1/0/1", "status": "down", "save": True},
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_port_down_dev_unavailable(self):
        self.user.profile.permissions = self.user.profile.UP_DOWN
        self.user.profile.save()
        self.client.force_login(user=self.user)

        resp = self.client.post(
            self.url,
            data={"port": "Fa1/0/1", "status": "down", "save": True},
        )
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertDictEqual(resp.data, {"error": "Оборудование недоступно!"})

    def test_port_down_invalid_request_data(self):
        self.user.profile.permissions = self.user.profile.UP_DOWN
        self.user.profile.save()
        self.client.force_login(user=self.user)

        # Неверный статус.
        resp = self.client.post(
            self.url,
            data={"port": "Fa1/0/1", "status": "asdasd", "save": True},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", resp.data)
        self.assertEqual(len(resp.data), 1)

        # Не был передан `save`.
        resp = self.client.post(
            self.url,
            data={"port": "Fa1/0/1", "status": "down"},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("save", resp.data)
        self.assertEqual(len(resp.data), 1)

        # Нет данных.
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("save", resp.data)
        self.assertIn("status", resp.data)
        self.assertIn("port", resp.data)
        self.assertEqual(len(resp.data), 3)

    @patch("check.models.Devices.connect")
    def test_port_down_invalid_port(self, dev_connect_mock: Mock):
        self.user.profile.permissions = self.user.profile.UP_DOWN
        self.user.profile.save()
        self.client.force_login(user=self.user)

        # Меняем IP, чтобы работал ping.
        self.device.ip = "127.0.0.1"
        self.device.save()

        device_mock = MagicMock()
        device_mock.set_port.return_value = "Неверный порт"
        dev_connect_mock.return_value = device_mock

        resp = self.client.post(
            self.url,
            data={"port": "eth1", "status": "down", "save": True},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", resp.data)

    def test_port_down_not_enough_permission(self):
        # Права только на перезагрузку.
        self.user.profile.permissions = self.user.profile.REBOOT
        self.user.profile.save()
        self.client.force_login(user=self.user)

        # Попытка выключить порт.
        resp = self.client.post(
            self.url,
            data={"port": "Fa1/0/1", "status": "down", "save": True},
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            resp.data["detail"],
            "У вас недостаточно прав, для изменения состояния порта!",
        )

        # Имеется запись в логах.
        self.assertEqual(
            UsersActions.objects.filter(
                device=self.device,
                user=self.user,
                action__contains="was refused",
            ).count(),
            1,
            msg="Нет записи в логах о неудачной попытке смены состояния порта",
        )

    def test_port_down_no_access_to_change_core_port_by_desc(self):
        self.user.profile.permissions = self.user.profile.UP_DOWN
        self.user.profile.port_guard_pattern = r"core-\d"
        self.user.profile.save()
        self.client.force_login(user=self.user)

        # Данный порт имеет описание `CORE`, Теперь его состояние нельзя менять.
        resp = self.client.post(
            self.url,
            data={"port": "Gi0/1", "status": "down", "save": True},
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp.data["detail"], "Запрещено изменять состояние данного порта!")

    @patch("check.models.Devices.connect")
    def test_port_down_superuser_access_to_change_core_port_by_desc(self, device_connection: Mock):
        self.user.profile.permissions = self.user.profile.UP_DOWN
        self.user.profile.save()
        self.client.force_login(user=self.user)
        self.user.is_superuser = True
        self.user.save()

        # Меняем IP, чтобы работал ping.
        self.device.ip = "127.0.0.1"
        self.device.save()

        device_connection.return_value.set_port.return_value = "Порт выключен"
        # Данный порт имеет описание `CORE`, изменять его состояние может только суперпользователь.
        data = {"port": "Gi0/1", "status": "down", "save": True}
        resp = self.client.post(self.url, data=data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertDictEqual(resp.data, data)

        # Имеется запись в логах.
        self.assertEqual(
            UsersActions.objects.filter(
                device=self.device,
                user=self.user,
                action__contains="down port",
            ).count(),
            1,
            msg="Нет записи в логах смене состояния порта",
        )

    @patch("check.models.Devices.connect")
    def test_port_down_valid(self, dev_connect_mock: Mock):
        self.user.profile.permissions = self.user.profile.UP_DOWN
        self.user.profile.save()
        self.client.force_login(user=self.user)

        # Меняем IP, чтобы работал ping.
        self.device.ip = "127.0.0.1"
        self.device.save()

        device_mock = MagicMock()
        device_mock.set_port.return_value = "Порт выключен"
        dev_connect_mock.return_value = device_mock

        data = {"port": "Fa1/0/1", "status": "down", "save": True}
        resp = self.client.post(self.url, data=data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertDictEqual(resp.data, data)

        # Имеется запись в логах.
        self.assertEqual(
            UsersActions.objects.filter(
                device=self.device,
                user=self.user,
                action__contains="down port",
            ).count(),
            1,
            msg="Нет записи в логах смене состояния порта",
        )


class ChangeDescriptionAPIViewTestCase(APITestCase):
    user = None  # type: ClassVar[User]
    group = None  # type: ClassVar[DeviceGroup]
    device = None  # type: ClassVar[Devices]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(username="test_user", password="password")
        cls.group = DeviceGroup.objects.create(name="ASW")
        cls.user.profile.devices_groups.add(cls.group)
        cls.device = Devices.objects.create(ip="172.31.176.21", name="dev1", group=cls.group)

    def setUp(self) -> None:
        self.client.force_login(user=self.user)

    def test_set_description_forbidden(self):
        resp = self.client.post(
            reverse("devices-api:set-description", args=(self.device.name,)),
            data={"port": "eth1", "description": "new_desc"},
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    @patch("check.models.Devices.connect")
    def test_clear_description(self, device_connect: Mock):
        # Меняем уровень доступа пользователя, чтобы он мог изменять описания портов.
        self.user.profile.permissions = self.user.profile.BRAS
        self.user.profile.save()

        # Подготовка данных.
        set_description_result = SetDescriptionResult(
            status="cleared", description="", saved="Saved OK", port="eth1"
        )
        device_connect.return_value.set_description.return_value = set_description_result
        device_connect.return_value.get_interfaces.return_value = [("eth1", "up", "desc1")]

        # Отправка запроса.
        request_data = {"port": "eth1"}
        resp = self.client.post(
            reverse("devices-api:set-description", args=(self.device.name,)),
            data=request_data,
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Кол-во вызванных методов.
        # Первый на поиск интерфейсов, чтобы проверить описание
        # Второй на изменение описания
        self.assertEqual(device_connect.call_count, 2)
        # Правильность вызова `set_description`.
        device_connect.return_value.set_description.assert_called_once_with(
            port=request_data["port"],
            desc="",  # Пустое описание.
        )

        self.assertDictEqual(
            resp.data,
            {
                "description": set_description_result.description,
                "port": set_description_result.port,
                "saved": set_description_result.saved,
            },
            msg="В ответе API неверные данные",
        )

        # Имеется запись в логах.
        self.assertEqual(
            UsersActions.objects.filter(
                device=self.device,
                user=self.user,
                action=str(set_description_result),
            ).count(),
            1,
            msg="Нет записи лога об очищении описания на порту",
        )

    @patch("check.models.Devices.connect")
    def test_set_description(self, device_connect: Mock):
        # Меняем уровень доступа пользователя, чтобы он мог изменять описания портов.
        self.user.profile.permissions = self.user.profile.BRAS
        self.user.profile.save()

        # Подготовка данных.
        description = "Новое описание"
        formatted_description = BaseDevice.clear_description(description)
        set_description_result = SetDescriptionResult(
            status="cleared",
            description=formatted_description,
            saved="Saved OK",
            port="eth1",
        )
        device_connect.return_value.set_description.return_value = set_description_result
        device_connect.return_value.get_interfaces.return_value = [("eth1", "up", "desc1")]
        data = {"port": "eth1", "description": description}

        # Отправка запроса.
        resp = self.client.post(
            reverse("devices-api:set-description", args=(self.device.name,)),
            data=data,
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Кол-во вызванных методов.
        # Первый на поиск интерфейсов, чтобы проверить описание
        # Второй на изменение описания
        self.assertEqual(device_connect.call_count, 2)
        # Правильность вызова `set_description`.
        device_connect.return_value.set_description.assert_called_once_with(
            port=data["port"],
            desc=data["description"],
        )

        self.assertDictEqual(
            resp.data,
            {
                "description": formatted_description,
                "port": set_description_result.port,
                "saved": set_description_result.saved,
            },
            msg="В ответе API неверные данные",
        )

        # Имеется запись в логах.
        self.assertEqual(
            UsersActions.objects.filter(
                device=self.device,
                user=self.user,
                action=str(set_description_result),
            ).count(),
            1,
            msg="Нет записи лога об изменении описания на порту",
        )

    @patch("check.models.Devices.connect")
    def test_set_description_too_long(self, device_connect: Mock):
        # Меняем уровень доступа пользователя, чтобы он мог изменять описания портов.
        self.user.profile.permissions = self.user.profile.BRAS
        self.user.profile.save()

        # Подготовка данных.
        description = "Новое описание" * 100
        set_description_result = SetDescriptionResult(
            status="fail",
            max_length=64,
            port="eth1",
        )
        device_connect.return_value.set_description.return_value = set_description_result
        device_connect.return_value.get_interfaces.return_value = [("eth1", "up", "desc1")]
        data = {"port": "eth1", "description": description}

        # Отправка запроса.
        resp = self.client.post(
            reverse("devices-api:set-description", args=(self.device.name,)),
            data=data,
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(device_connect.call_count, 2)
        device_connect.return_value.set_description.assert_called_once_with(
            port=data["port"],
            desc=data["description"],
        )

        self.assertDictEqual(
            resp.data,
            {
                "detail": "Слишком длинное описание! "
                          f"Укажите не более {set_description_result.max_length} символов."
            },
            msg="В ответе API неверные данные",
        )

        # НЕ Имеется запись в логах.
        self.assertEqual(
            UsersActions.objects.count(),
            0,
            msg="Лишняя запись лога об слишком длинном запросе изменения описания на порту",
        )


class MacListAPIViewTestCase(APITestCase):
    user = None  # type: ClassVar[User]
    group = None  # type: ClassVar[DeviceGroup]
    device = None  # type: ClassVar[Devices]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(username="test_user", password="password")
        cls.group = DeviceGroup.objects.create(name="ASW")
        cls.user.profile.devices_groups.add(cls.group)
        cls.device = Devices.objects.create(
            ip="172.31.176.21",
            name="dev1",
            group=cls.group,
        )

    @patch("check.models.Devices.connect")
    def test_mac_list(self, device_connect: Mock):
        self.client.force_login(user=self.user)

        vlan_name = "some_vlan_name"
        device_connect.return_value.get_mac.return_value = [
            ("1051", "00-04-96-51-AD-3D"),
            ("1051", "00-04-96-52-A5-FB"),
            ("1051", "00-04-96-52-A5-5B"),
        ]
        # Добавляем название VLAN
        VlanName.objects.create(vid=1051, name=vlan_name)

        with self.assertNumQueries(5):
            # django_session Cached Now
            # 1. auth_user
            # 2. devices
            # 3. user_profile
            # 4. devices_group
            # 5. vlan_name (Только один раз, проверка кэша)
            resp = self.client.get(reverse("devices-api:mac-list", args=(self.device.name,)) + "?port=eth1")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            resp.data,
            {
                "count": 3,
                "result": [
                    {
                        "vlanID": "1051",
                        "mac": "00-04-96-51-AD-3D",
                        "vlanName": vlan_name,
                    },
                    {
                        "vlanID": "1051",
                        "mac": "00-04-96-52-A5-FB",
                        "vlanName": vlan_name,
                    },
                    {
                        "vlanID": "1051",
                        "mac": "00-04-96-52-A5-5B",
                        "vlanName": vlan_name,
                    },
                ],
            },
        )

        self.assertEqual(device_connect.call_count, 1)
        device_connect.return_value.get_mac.assert_called_once_with("eth1")
