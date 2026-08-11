from datetime import timedelta

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounting.models import User
from apps.check.models import AuthGroup, DeviceGroup, Devices
from apps.gathering.models import DeviceGatheringResult, GatheringTask


class GatheringResultsPermissionTests(TestCase):
    """Проверить регистрацию нового функционального права."""

    def test_permission_is_created_after_migrate(self) -> None:
        """Post-migrate hook создает право в namespace accounting."""

        content_type = ContentType.objects.get_for_model(User)

        self.assertTrue(
            Permission.objects.filter(
                codename="access_gathering_results",
                content_type=content_type,
            ).exists()
        )


class GatheringResultsAPITests(APITestCase):
    """Проверить read-only API истории периодического сбора."""

    def setUp(self) -> None:
        """Создать пользователя, доступное оборудование и историю сбора."""

        cache.clear()
        self.user = User.objects.create_user(username="operator", password="password")
        content_type = ContentType.objects.get_for_model(User)
        self.permission, _ = Permission.objects.get_or_create(
            codename="access_gathering_results",
            name="Can view periodic gathering results",
            content_type=content_type,
        )

        self.accessible_group = DeviceGroup.objects.create(name="Access")
        self.restricted_group = DeviceGroup.objects.create(name="Restricted")
        self.user.profile.devices_groups.add(self.accessible_group)
        auth_group = AuthGroup.objects.create(name="default", login="user", password="password")
        self.device = Devices.objects.create(
            group=self.accessible_group,
            auth_group=auth_group,
            ip="192.0.2.10",
            name="access-sw-1",
            vendor="Eltex",
            model="MES2324",
        )
        self.restricted_device = Devices.objects.create(
            group=self.restricted_group,
            auth_group=auth_group,
            ip="192.0.2.20",
            name="restricted-sw-1",
            vendor="Cisco",
            model="C9200",
        )

        now = timezone.now()
        self.task = GatheringTask.objects.create(
            task_id="task-visible",
            name="interfaces",
            status=GatheringTask.Status.PARTIAL,
            total_devices=2,
            started_at=now - timedelta(minutes=10),
            finished_at=now - timedelta(minutes=5),
        )
        self.result = DeviceGatheringResult.objects.create(
            task=self.task,
            device=self.device,
            status=DeviceGatheringResult.Status.FAILURE,
            error_type="TimeoutError",
            error_message="Connection timed out",
            started_at=now - timedelta(minutes=9),
            finished_at=now - timedelta(minutes=8),
        )
        DeviceGatheringResult.objects.create(
            task=self.task,
            device=self.restricted_device,
            status=DeviceGatheringResult.Status.SUCCESS,
            started_at=now - timedelta(minutes=8),
            finished_at=now - timedelta(minutes=7),
        )

        self.list_url = reverse("gathering-api:task-result-list")
        self.timeline_url = reverse("gathering-api:task-result-timeline")
        self.lookups_url = reverse("gathering-api:task-result-lookups")

    def tearDown(self) -> None:
        """Очистить кэш между тестами."""

        cache.clear()

    def test_api_requires_authentication(self) -> None:
        """Анонимный пользователь не может читать историю сбора."""

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_api_requires_gathering_results_permission(self) -> None:
        """Аутентифицированному пользователю без нового права доступ запрещен."""

        self.client.force_authenticate(self.user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_returns_only_results_for_accessible_devices(self) -> None:
        """Список не раскрывает результаты недоступного оборудования."""

        self.user.user_permissions.add(self.permission)
        self.client.force_authenticate(self.user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        row = response.data["results"][0]
        self.assertEqual(row["id"], self.result.id)
        self.assertEqual(row["device"]["name"], self.device.name)
        self.assertEqual(row["device"]["group"]["name"], self.accessible_group.name)
        self.assertEqual(row["task"]["name"], self.task.name)

    def test_list_applies_device_task_and_result_filters(self) -> None:
        """API применяет все группы фильтров к одному queryset."""

        self.user.user_permissions.add(self.permission)
        self.client.force_authenticate(self.user)
        params = {
            "device_group": self.accessible_group.id,
            "device_name": "access-sw",
            "vendor": "Eltex",
            "model": "MES2324",
            "task_status": GatheringTask.Status.PARTIAL,
            "task_name": "interfaces",
            "task_started_after": (self.task.started_at - timedelta(seconds=1)).isoformat(),
            "task_started_before": (self.task.started_at + timedelta(seconds=1)).isoformat(),
            "result_status": DeviceGatheringResult.Status.FAILURE,
            "result_started_after": (self.result.started_at - timedelta(seconds=1)).isoformat(),
            "result_started_before": (self.result.started_at + timedelta(seconds=1)).isoformat(),
            "error_type": "TimeoutError",
            "error_message": "timed out",
        }

        response = self.client.get(self.list_url, params)  # type: ignore

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        params["vendor"] = "Huawei"
        response = self.client.get(self.list_url, params)  # type: ignore
        self.assertEqual(response.data["count"], 0)

    def test_timeline_returns_filtered_range_items_without_pagination(self) -> None:
        """Timeline endpoint возвращает диапазоны и метаданные ограничения."""

        self.user.user_permissions.add(self.permission)
        self.client.force_authenticate(self.user)

        response = self.client.get(self.timeline_url, {"task_name": "interfaces"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["truncated"])
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.result.id)

    def test_lookups_are_scoped_and_error_types_are_cached(self) -> None:
        """Справочники учитывают доступ к устройствам, а error_type берется из кэша."""

        self.user.user_permissions.add(self.permission)
        self.client.force_authenticate(self.user)

        first_response = self.client.get(self.lookups_url)

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            first_response.data["device_groups"],
            [{"id": self.accessible_group.id, "name": "Access"}],
        )
        self.assertEqual(first_response.data["vendors"], ["Eltex"])
        self.assertEqual(first_response.data["models"], ["MES2324"])
        self.assertEqual(first_response.data["task_names"], ["interfaces"])
        self.assertEqual(first_response.data["error_types"], ["TimeoutError"])

        DeviceGatheringResult.objects.create(
            task=GatheringTask.objects.create(
                task_id="second-task",
                name="vlans",
                status=GatheringTask.Status.FAILURE,
                total_devices=1,
            ),
            device=self.device,
            status=DeviceGatheringResult.Status.FAILURE,
            error_type="ValueError",
            error_message="Invalid value",
        )

        cached_response = self.client.get(self.lookups_url)

        self.assertEqual(cached_response.data["error_types"], ["TimeoutError"])
        self.assertEqual(cached_response.data["task_names"], ["interfaces", "vlans"])
