from unittest.mock import MagicMock, patch, Mock

import orjson
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from app_settings.models import LogsElasticStackSettings
from devicemanager.device import Interfaces, zabbix_api
from net_tools.models import DevicesInfo
from ..api.serializers import DevicesSerializer
from ..models import Devices, DeviceGroup, User, InterfacesComments
from ..services.device.interfaces_workload import DevicesInterfacesWorkloadCollector


class DevicesListAPIViewTestCase(APITestCase):
    def setUp(self) -> None:
        cache.clear()
        self.url = reverse("devices-api:devices-list")
        self.user: User = User.objects.create_user(username="test_user", password="password")
        self.group = DeviceGroup.objects.create(name="ASW")
        self.user.profile.devices_groups.add(self.group)
        self.device = Devices.objects.create(
            ip="172.30.0.58",
            name="dev1",
            group=self.group,
        )

    def test_get_devices_list_without_authentication(self):
        """Убедитесь, что GET запрос списка устройств без аутентификации возвращает 403 ответ"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_devices_list_with_authentication(self):
        """Убедитесь, что GET запрос списка устройств с аутентификацией возвращает список устройств"""
        self.client.force_authenticate(user=self.user)
        with self.assertNumQueries(1):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            serializer_data = DevicesSerializer([self.device], many=True).data
            self.assertDictEqual(response.data[0], serializer_data[0])

    def test_get_devices_list_with_authentication_and_params(self):
        """Убедитесь, что GET запрос списка устройств с аутентификацией возвращает список устройств"""
        self.client.force_authenticate(user=self.user)
        with self.assertNumQueries(1):
            response = self.client.get(self.url + "?return-fields=ip,name,group")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            serializer_data = DevicesSerializer(self.device).data
            self.assertDictEqual(
                response.data[0],
                {
                    "ip": serializer_data["ip"],
                    "name": serializer_data["name"],
                    "group": serializer_data["group"],
                },
            )

    def test_cache(self):
        """Убедитесь, что функция кэширования работает корректно"""
        self.client.force_authenticate(user=self.user)

        # Первый запрос - кеширование
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Второй запрос - данные должны браться из кэша, а не из базы данных
        with self.assertNumQueries(0):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)


class AllDevicesInterfacesWorkLoadAPIViewTests(APITestCase):
    def setUp(self) -> None:
        cache.clear()
        self.url = reverse("devices-api:all-devices-interfaces-workload")
        self.user: User = User.objects.create_user(username="test_user", password="password")
        self.group = DeviceGroup.objects.create(name="ASW")

        self.user.profile.devices_groups.add(self.group)
        self.device = Devices.objects.create(
            ip="10.10.10.10",
            name="dev1",
            group=self.group,
        )

        self.unavailable_group = DeviceGroup.objects.create(name="unavailable_group")
        self.unavailable_device = Devices.objects.create(
            ip="10.10.10.12",
            name="dev2",
            group=self.unavailable_group,
        )

        self.device_info = DevicesInfo.objects.create(
            dev=self.device,
            interfaces=orjson.dumps(
                [
                    {"Interface": "Fa1/0/1", "Status": "up", "Description": "desc1"},
                    {"Interface": "Fa1/0/2", "Status": "up", "Description": "desc2"},
                    {"Interface": "Fa1/0/3", "Status": "down", "Description": "desc3"},
                    {"Interface": "Fa1/0/4", "Status": "admin down", "Description": "desc4"},
                    {"Interface": "Fa1/0/5", "Status": "down", "Description": "desc5"},
                    {"Interface": "Fa1/0/6", "Status": "up", "Description": "CORE"},
                    {"Interface": "Fa1/0/7", "Status": "down", "Description": ""},
                ]
            ).decode(),
        )

    def test_get_all_device_interfaces_workload_without_authentication(self):
        """Убедитесь, что GET запрос списка устройств без аутентификации возвращает 403 ответ"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_all_device_interfaces_workload_without_cache(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["devices_count"], 1)
        self.assertEqual(len(response.data["devices"]), 1)

        # Check interfaces load data for device1
        device1_data = response.data["devices"][0]
        self.assertEqual(device1_data["name"], "dev1")
        self.assertEqual(device1_data["interfaces_count"]["count"], 7)
        self.assertEqual(device1_data["interfaces_count"]["abons"], 6)
        self.assertEqual(device1_data["interfaces_count"]["abons_up"], 2)
        self.assertEqual(device1_data["interfaces_count"]["abons_down"], 4)
        self.assertEqual(device1_data["interfaces_count"]["abons_up_with_desc"], 2)
        self.assertEqual(device1_data["interfaces_count"]["abons_up_no_desc"], 0)
        self.assertEqual(device1_data["interfaces_count"]["abons_down_with_desc"], 3)
        self.assertEqual(device1_data["interfaces_count"]["abons_down_no_desc"], 1)

    def test_get_all_device_interfaces_workload_with_cache(self):
        cache_value = {
            "devices_count": 123,
            "devices": [],
        }
        cache.set("all_devices_interfaces_workload_api_view", cache_value)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, cache_value)

    def test_get_all_device_interfaces_workload_with_cache_and_with_unavailable_group(
        self,
    ):
        cache_value = {
            "devices_count": 2,
            "devices": [
                {"group": self.unavailable_group.name, "device": "dev1"},
                {"group": self.group.name, "device": "dev2"},
            ],
        }
        cache.set("all_devices_interfaces_workload_api_view", cache_value)

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "devices_count": 1,
                "devices": [
                    {"group": self.group.name, "device": "dev2"},
                ],
            },
        )

    def test_get_queryset(self):
        queryset = DevicesInterfacesWorkloadCollector().get_queryset()
        self.assertEqual(queryset.count(), 1)

    def test_get_serializer_class(self):
        serializer_class = DevicesInterfacesWorkloadCollector().get_serializer_class()
        self.assertEqual(serializer_class.Meta.model, Devices)

    def test_get_interfaces_load(self):
        # Test with device that has one up and one down interface
        interfaces_load = DevicesInterfacesWorkloadCollector().get_interfaces_load(self.device_info)
        self.assertEqual(interfaces_load["count"], 7)
        self.assertEqual(interfaces_load["abons"], 6)
        self.assertEqual(interfaces_load["abons_up"], 2)
        self.assertEqual(interfaces_load["abons_down"], 4)
        self.assertEqual(interfaces_load["abons_up_with_desc"], 2)
        self.assertEqual(interfaces_load["abons_up_no_desc"], 0)
        self.assertEqual(interfaces_load["abons_down_with_desc"], 3)
        self.assertEqual(interfaces_load["abons_down_no_desc"], 1)

        # Test with device that has no interface
        device = DevicesInfo()
        interfaces_load = DevicesInterfacesWorkloadCollector().get_interfaces_load(device)
        self.assertEqual(interfaces_load["count"], 0)
        self.assertEqual(interfaces_load["abons"], 0)
        self.assertEqual(interfaces_load["abons_up"], 0)
        self.assertEqual(interfaces_load["abons_down"], 0)


class DeviceInterfacesAPIViewTestCase(APITestCase):
    def setUp(self) -> None:
        self.user: User = User.objects.create_user(username="test_user", password="password")
        self.group = DeviceGroup.objects.create(name="ASW")
        self.user.profile.devices_groups.add(self.group)
        self.device = Devices.objects.create(
            ip="127.0.0.1",
            name="dev1",
            group=self.group,
            model="model",
            vendor="vendor",
        )
        self.comment = InterfacesComments.objects.create(
            device=self.device, interface="Fa1/0/1", comment="comment", user=self.user
        )

        self.url = reverse("devices-api:device-interfaces", args=[self.device.name])
        self.client.force_authenticate(user=self.user)

    @patch("check.models.Devices.available")
    @patch("devicemanager.device.DeviceManager.from_model")
    def test_get_current_interfaces_not_snmp_with_vlans(self, mock_connect: Mock, mock_available: Mock):
        # mock_available.return_value = MagicMock(__bool__=Mock(return_value=True))
        mock_available.return_value = False

        interfaces = [
            {
                "Interface": "Fa1/0/1",
                "Status": "up",
                "Description": "desc1",
                "VLAN's": [1, 2],
            },
            {
                "Interface": "Fa1/0/2",
                "Status": "up",
                "Description": "desc2",
                "VLAN's": [3, 4],
            },
        ]

        device_manager_mock = MagicMock()
        device_manager_mock.protocol = "telnet"
        device_manager_mock.interfaces = Interfaces(interfaces)

        # Указываем новый вендор и модель, после они должны быть записаны в базе
        device_manager_mock.zabbix_info.inventory.vendor = "new vendor"
        device_manager_mock.zabbix_info.inventory.model = "new model"
        device_manager_mock.zabbix_info.inventory.serialno_a = "new serial"
        device_manager_mock.zabbix_info.inventory.os_full = "new os version"
        device_manager_mock.push_zabbix_inventory.return_value = None

        mock_connect.return_value = device_manager_mock

        response = self.client.get(f"{self.url}?current_status=1&vlans=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Получаем свежие данные
        device_info = DevicesInfo.objects.get(dev=self.device)
        print(device_info)
        device = Devices.objects.get(id=self.device.id)

        # В базе должны были обновиться поля
        self.assertEqual(device.vendor, "new vendor")
        self.assertEqual(device.model, "new model")
        self.assertEqual(device.serial_number, "new serial")
        self.assertEqual(device.os_version, "new os version")

        # Полученные данные
        del response.data["collected"]
        self.assertDictEqual(
            response.data,
            {
                "interfaces": [
                    {
                        "Interface": "Fa1/0/1",
                        "Status": "up",
                        "Description": "desc1",
                        "VLAN's": [1, 2],
                        "Comments": [
                            {
                                "text": self.comment.comment,
                                "user": self.comment.user.username if self.comment.user else "Anonymous",
                                "id": self.comment.id,
                                "createdTime": self.comment.datetime.isoformat(),
                            }
                        ],
                    },
                    {
                        "Interface": "Fa1/0/2",
                        "Status": "up",
                        "Description": "desc2",
                        "VLAN's": [3, 4],
                        "Comments": [],
                    },
                ],
                "deviceAvailable": True,
            },
        )

        self.assertEqual(mock_connect.call_count, 1)
        device_manager_mock.collect_interfaces.assert_called_once_with(
            vlans=True,
            current_status=True,
            raise_exception=True,
            make_session_global=True,
        )
        device_manager_mock.push_zabbix_inventory.assert_called_once()

        # Проверяем, что полученные интерфейсы с VLAN были записаны в базу
        self.assertListEqual(
            orjson.loads(device_info.vlans or "[]"),
            interfaces,
        )

        # А также записаны интерфейсы без VLAN
        self.assertListEqual(
            orjson.loads(device_info.interfaces or "[]"),
            [
                {
                    "Interface": line["Interface"],
                    "Status": line["Status"],
                    "Description": line["Description"],
                }
                for line in interfaces
            ],
        )

    @patch("check.models.Devices.available")
    @patch("devicemanager.device.DeviceManager.from_model")
    def test_get_current_interfaces_with_snmp_no_vlans(self, mock_connect: Mock, mock_available: Mock):
        mock_available.return_value = True
        interfaces = [
            {"Interface": "Fa1/0/1", "Status": "up", "Description": "desc1"},
            {"Interface": "Fa1/0/2", "Status": "up", "Description": "desc2"},
        ]
        self.device.port_scan_protocol = "snmp"
        self.device.save()

        device_manager_mock = MagicMock()
        device_manager_mock.interfaces = Interfaces(interfaces)
        # Указываем ПУСТЫМИ вендор и модель, после они НЕ должны быть записаны в базе
        device_manager_mock.zabbix_info.inventory.vendor = "vendor"
        device_manager_mock.zabbix_info.inventory.model = "model"
        device_manager_mock.zabbix_info.inventory.serialno_a = "serial_number"
        device_manager_mock.zabbix_info.inventory.os_full = "os_version"
        device_manager_mock.push_zabbix_inventory.return_value = None
        mock_connect.return_value = device_manager_mock

        response = self.client.get(f"{self.url}?current_status=1&vlans=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Получаем свежие данные
        device_info: DevicesInfo = DevicesInfo.objects.get(dev=self.device)
        device = Devices.objects.get(id=self.device.id)

        # В базе должны были остаться без изменения поля
        self.assertEqual(device.vendor, "vendor")
        self.assertEqual(device.model, "model")
        self.assertEqual(device.serial_number, "serial_number")
        self.assertEqual(device.os_version, "os_version")

        self.assertEqual(mock_connect.call_count, 1)

        # При SNMP протоколе опроса интерфейсов параметр `vlans=False`
        device_manager_mock.collect_interfaces.assert_called_once_with(
            vlans=False,
            current_status=True,
            raise_exception=True,
            make_session_global=True,
        )
        device_manager_mock.push_zabbix_inventory.assert_called_once()

        # Проверяем, что полученные интерфейсы с VLAN НЕ были записаны в базу
        self.assertIsNone(device_info.vlans)

        # НО записаны интерфейсы без VLAN
        self.assertListEqual(
            orjson.loads(device_info.interfaces or "[]"),
            [
                {
                    "Interface": line["Interface"],
                    "Status": line["Status"],
                    "Description": line["Description"],
                }
                for line in interfaces
            ],
        )


class DeviceInfoAPIViewTestCase(APITestCase):
    def setUp(self) -> None:
        self.user: User = User.objects.create_user(username="test_user", password="password")
        self.group = DeviceGroup.objects.create(name="ASW")
        self.user.profile.devices_groups.add(self.group)
        self.device = Devices.objects.create(
            ip="10.100.0.10",
            name="dev1",
            group=self.group,
            model="model",
            vendor="vendor",
        )
        self.url = reverse("devices-api:device-info", args=[self.device.name])

    def test_view_returns_valid_response_with_correct_data(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        expected_data = {
            "deviceName": self.device.name,
            "deviceIP": self.device.ip,
            "elasticStackLink": LogsElasticStackSettings.load().query_kibana_url(device=self.device),
            "zabbixHostID": 0,
            "zabbixURL": zabbix_api.zabbix_url,
            "zabbixInfo": {
                "description": "",
                "inventory": {},
                "monitoringAvailable": False,
                "maps": [],
            },
            "permission": self.user.profile.perm_level,
            "coords": [],
            "consoleURL": "",
            "uptime": -1,
        }
        self.assertDictEqual(response.json(), expected_data)

    def test_view_returns_valid_response_with_console_url(self):
        self.user.profile.console_access = True
        self.user.profile.console_url = "http://test_url"
        self.user.profile.save()

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        expected_data = {
            "deviceName": self.device.name,
            "deviceIP": self.device.ip,
            "elasticStackLink": LogsElasticStackSettings.load().query_kibana_url(device=self.device),
            "zabbixHostID": 0,
            "zabbixURL": zabbix_api.zabbix_url,
            "zabbixInfo": {
                "description": "",
                "inventory": {},
                "monitoringAvailable": False,
                "maps": [],
            },
            "permission": self.user.profile.perm_level,
            "coords": [],
            "consoleURL": "http://test_url&command=/usr/share/connections/tc.sh 10.100.0.10&title=10.100.0.10 (dev1) telnet",
            "uptime": -1,
        }
        self.assertDictEqual(response.json(), expected_data)

    def test_view_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_view_requires_device_permission(self):
        user = User.objects.create_user(username="user123")
        self.client.force_authenticate(user=user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)


class TestDeviceStatsInfoAPIView(APITestCase):
    def setUp(self) -> None:
        self.user: User = User.objects.create_user(username="test_user", password="password")
        self.group = DeviceGroup.objects.create(name="ASW")
        self.user.profile.devices_groups.add(self.group)
        self.device = Devices.objects.create(
            ip="10.20.0.20",
            name="dev1",
            group=self.group,
            model="model",
            vendor="vendor",
        )
        self.url = reverse("devices-api:device-stats-info", args=[self.device.name])

    @patch("check.models.Devices.available")
    @patch("check.models.Devices.connect")
    def test_device_stats_info_api_view(self, mock_connect: Mock, mock_available: Mock):
        # Делаем так, чтобы оборудование было доступно
        mock_available.return_value = True

        self.client.force_authenticate(user=self.user)
        mock_connect.return_value.get_device_info.return_value = {
            "cpu": {"util": [2]},
            "ram": {"util": 15},
            "flash": {"util": 50},
            "temp": {"value": 43.5, "status": "normal"},
        }

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "cpu": {"util": [2]},
                "ram": {"util": 15},
                "flash": {"util": 50},
                "temp": {"value": 43.5, "status": "normal"},
            },
        )

        mock_connect.assert_called_once_with()
        mock_connect.return_value.get_device_info.assert_called_once_with()

    @patch("check.models.Devices.connect")
    def test_authentication(self, mock_connect: Mock):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        mock_connect.assert_not_called()

    @patch("check.models.Devices.connect")
    def test_device_permission(self, mock_connect: Mock):
        user = User.objects.create_user(username="user123", password="test_password")
        self.client.force_authenticate(user=user)

        # DevicePermission разрешает только владельцу устройства доступ
        url = reverse("devices-api:device-stats-info", kwargs={"device_name": self.device.name})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        mock_connect.assert_not_called()
