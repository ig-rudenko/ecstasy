from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.check.models import AuthGroup, DeviceGroup, Devices, User
from apps.discovery.models import DiscoveryAttempt, DiscoveryCandidate, DiscoveryProfile, DiscoveryRun


class DiscoveryAPITests(APITestCase):
    """Тесты discovery REST API."""

    def setUp(self) -> None:
        """Создать суперпользователя и справочники."""

        self.user = User.objects.create_superuser(username="admin", password="password")
        self.group = DeviceGroup.objects.create(name="Access")
        self.auth_group = AuthGroup.objects.create(name="default", login="u", password="p")
        self.client.force_authenticate(self.user)

    def test_create_profile_does_not_return_snmp_communities(self):
        """API принимает SNMP community, но не раскрывает значения в ответе."""

        response = self.client.post(
            reverse("discovery-api:profiles-list"),
            {
                "name": "access-net",
                "networks": ["192.0.2.0/24"],
                "deviceGroup": self.group.id,
                "authGroups": [self.auth_group.id],
                "snmpCommunities": ["secret-community"],
                "tryProtocols": ["ssh"],
                "portScanProtocol": "snmp",
                "cmdProtocol": "ssh",
                "maxWorkers": 4,
                "timeoutSeconds": 1,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("snmpCommunities", response.data)
        self.assertEqual(response.data["snmpCommunitiesCount"], 1)

    def test_create_profile_rejects_network_larger_than_24(self):
        """API отклоняет discovery profile с CIDR шире /24."""

        response = self.client.post(
            reverse("discovery-api:profiles-list"),
            {
                "name": "too-big",
                "networks": ["10.0.0.0/23"],
                "deviceGroup": self.group.id,
                "authGroups": [self.auth_group.id],
                "tryProtocols": ["ssh"],
                "portScanProtocol": "snmp",
                "cmdProtocol": "ssh",
                "maxWorkers": 4,
                "timeoutSeconds": 1,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_accept_candidate_endpoint_creates_inactive_device(self):
        """Accept endpoint создает inactive устройство."""

        candidate = DiscoveryCandidate.objects.create(
            ip="192.0.2.30",
            name="sw-30",
            status=DiscoveryCandidate.Status.READY,
            selected_auth_group=self.auth_group,
        )

        response = self.client.post(
            reverse("discovery-api:candidates-accept", args=[candidate.id]),
            {
                "deviceGroup": self.group.id,
                "authGroup": self.auth_group.id,
                "cmdProtocol": "ssh",
                "portScanProtocol": "snmp",
                "collectInterfaces": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        candidate.refresh_from_db()
        self.assertEqual(candidate.status, DiscoveryCandidate.Status.CREATED)
        self.assertFalse(candidate.device.active)

    def test_accept_candidate_uses_selected_auth_group_and_detected_protocols_by_default(self):
        """Accept endpoint использует auth/protocol кандидата, если override не передан."""

        candidate = DiscoveryCandidate.objects.create(
            ip="192.0.2.31",
            name="sw-31",
            status=DiscoveryCandidate.Status.READY,
            selected_auth_group=self.auth_group,
            detected_protocols={"snmp": False, "ssh": False, "telnet": True},
            raw_fingerprint={"cliProtocol": "telnet"},
        )

        response = self.client.post(
            reverse("discovery-api:candidates-accept", args=[candidate.id]),
            {
                "deviceGroup": self.group.id,
                "collectInterfaces": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        candidate.refresh_from_db()
        device = Devices.objects.get(id=candidate.device_id)
        self.assertEqual(device.auth_group_id, self.auth_group.id)
        self.assertEqual(device.cmd_protocol, "telnet")
        self.assertEqual(device.port_scan_protocol, "telnet")

    def test_staff_without_discovery_permission_is_forbidden(self):
        """Staff без `auth.access_discovery` не может использовать discovery API."""

        user = User.objects.create_user(username="operator", password="password", is_staff=True)
        self.client.force_authenticate(user)

        response = self.client.get(reverse("discovery-api:profiles-list"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_with_discovery_permission_can_access_api(self):
        """Пользователь с `auth.access_discovery` может использовать discovery API."""

        user = User.objects.create_user(username="discovery-user", password="password")
        user.user_permissions.add(Permission.objects.get(codename="access_discovery"))
        self.client.force_authenticate(user)

        response = self.client.get(reverse("discovery-api:profiles-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("apps.discovery.api.views.discovery_run_task")
    def test_create_run_rejects_overlapping_discovery(self, mock_discovery_task):
        """Новый discovery run не запускается, пока предыдущий активен."""

        profile = self._create_profile()
        DiscoveryRun.objects.create(
            profile=profile,
            status=DiscoveryRun.Status.PROGRESS,
        )

        response = self.client.post(
            reverse("discovery-api:runs-list"),
            {
                "profileId": profile.id,
                "dryRun": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(DiscoveryRun.objects.count(), 1)
        mock_discovery_task.delay.assert_not_called()

    @patch("apps.discovery.api.views.AsyncResult")
    def test_delete_run_removes_run_and_attempts(self, mock_async_result):
        """DELETE run удаляет запуск, попытки и отзывает активную Celery-задачу."""

        run = DiscoveryRun.objects.create(
            profile=self._create_profile(),
            status=DiscoveryRun.Status.PROGRESS,
            task_id="discovery-task-id",
        )
        DiscoveryAttempt.objects.create(
            run=run,
            ip="192.0.2.40",
            method=DiscoveryAttempt.Method.PING,
            status=DiscoveryAttempt.Status.SUCCESS,
        )

        response = self.client.delete(reverse("discovery-api:runs-detail", args=[run.id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(DiscoveryRun.objects.filter(id=run.id).exists())
        self.assertFalse(DiscoveryAttempt.objects.filter(run_id=run.id).exists())
        mock_async_result.assert_called_once_with("discovery-task-id")
        mock_async_result.return_value.revoke.assert_called_once_with(terminate=True)

    @patch("apps.discovery.api.views.AsyncResult")
    def test_delete_profile_endpoint_removes_profile(self, mock_async_result):
        """DELETE profile удаляет discovery profile и отзывает активные запуски."""

        profile = self._create_profile()
        DiscoveryRun.objects.create(
            profile=profile,
            status=DiscoveryRun.Status.PROGRESS,
            task_id="profile-task-id",
        )

        response = self.client.delete(reverse("discovery-api:profiles-detail", args=[profile.id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(DiscoveryProfile.objects.filter(id=profile.id).exists())
        mock_async_result.assert_called_once_with("profile-task-id")
        mock_async_result.return_value.revoke.assert_called_once_with(terminate=True)

    def test_delete_candidate_endpoint_removes_candidate(self):
        """DELETE candidate удаляет discovery candidate."""

        candidate = DiscoveryCandidate.objects.create(
            ip="192.0.2.41",
            name="sw-41",
            status=DiscoveryCandidate.Status.NEW,
        )

        response = self.client.delete(reverse("discovery-api:candidates-detail", args=[candidate.id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(DiscoveryCandidate.objects.filter(id=candidate.id).exists())

    def test_candidate_list_returns_auth_check_status(self):
        """Candidate list возвращает статус проверки AuthGroup для фронтенда."""

        DiscoveryCandidate.objects.create(
            ip="192.0.2.45",
            status=DiscoveryCandidate.Status.READY,
            raw_fingerprint={"authCheck": {"status": "FAILED"}},
            last_error="логин неверный",
        )

        response = self.client.get(reverse("discovery-api:candidates-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        candidate = response.data["results"][0]
        self.assertEqual(candidate["authCheckStatus"], "FAILED")
        self.assertEqual(candidate["authCheckError"], "логин неверный")

    def test_bulk_delete_candidates_endpoint_removes_requested_candidates(self):
        """Bulk delete удаляет выбранных кандидатов одним запросом."""

        first = DiscoveryCandidate.objects.create(ip="192.0.2.42", status=DiscoveryCandidate.Status.NEW)
        second = DiscoveryCandidate.objects.create(ip="192.0.2.43", status=DiscoveryCandidate.Status.READY)
        kept = DiscoveryCandidate.objects.create(ip="192.0.2.44", status=DiscoveryCandidate.Status.NEW)

        response = self.client.post(
            reverse("discovery-api:candidates-bulk-delete"),
            {"ids": [first.id, second.id]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"deleted": 2})
        self.assertFalse(DiscoveryCandidate.objects.filter(id__in=[first.id, second.id]).exists())
        self.assertTrue(DiscoveryCandidate.objects.filter(id=kept.id).exists())

    @patch("apps.discovery.api.views.chain")
    @patch("apps.discovery.api.views.discovery_run_task")
    def test_rescan_candidates_endpoint_starts_dry_run_for_candidate_ips(
        self,
        mock_discovery_task,
        mock_chain,
    ):
        """Rescan endpoint запускает dry-run только по IP выбранных кандидатов."""

        scan_task = mock_discovery_task.si.return_value
        scan_task.freeze.return_value.id = "rescan-task-id"
        profile = self._create_profile()
        run = DiscoveryRun.objects.create(profile=profile, status=DiscoveryRun.Status.SUCCESS)
        candidate = DiscoveryCandidate.objects.create(ip="192.0.2.46", status=DiscoveryCandidate.Status.READY)
        DiscoveryAttempt.objects.create(
            run=run,
            candidate=candidate,
            ip=candidate.ip,
            method=DiscoveryAttempt.Method.PING,
            status=DiscoveryAttempt.Status.SUCCESS,
        )

        response = self.client.post(
            reverse("discovery-api:candidates-rescan"),
            {"ids": [candidate.id]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        rescan_run = DiscoveryRun.objects.get(id=response.data["runs"][0]["id"])
        self.assertTrue(rescan_run.dry_run)
        self.assertEqual(rescan_run.task_id, "rescan-task-id")
        self.assertEqual(response.data["skipped"], [])
        mock_discovery_task.si.assert_called_once_with(rescan_run.id, [candidate.ip])
        mock_chain.assert_called_once_with(scan_task)
        mock_chain.return_value.apply_async.assert_called_once_with()

    @patch("apps.discovery.api.views.discovery_run_task")
    def test_rescan_candidates_endpoint_skips_candidate_without_profile_history(self, mock_discovery_task):
        """Rescan endpoint не угадывает профиль, если у кандидата нет истории discovery."""

        candidate = DiscoveryCandidate.objects.create(ip="192.0.2.47", status=DiscoveryCandidate.Status.READY)

        response = self.client.post(
            reverse("discovery-api:candidates-rescan"),
            {"ids": [candidate.id]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["runs"], [])
        self.assertEqual(response.data["skipped"][0]["id"], candidate.id)
        mock_discovery_task.delay.assert_not_called()

    def _create_profile(self) -> DiscoveryProfile:
        """Создать минимальный discovery profile для API-тестов."""

        profile = DiscoveryProfile.objects.create(
            name="access-net",
            networks=["192.0.2.0/24"],
            device_group=self.group,
            try_protocols=["ssh"],
            port_scan_protocol="snmp",
            cmd_protocol="ssh",
            max_workers=4,
            timeout_seconds=1,
        )
        profile.auth_groups.add(self.auth_group)
        return profile
