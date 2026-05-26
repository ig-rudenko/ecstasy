from collections import defaultdict

from celery.result import AsyncResult
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.check.models import AuthGroup, DeviceGroup

from ..models import DiscoveryCandidate, DiscoveryProfile, DiscoveryRun
from ..services.provisioning import accept_candidate
from ..tasks import discovery_run_task
from .permissions import DiscoveryAdminPermission
from .serializers import (
    DiscoveryCandidateAcceptSerializer,
    DiscoveryCandidateBulkDeleteSerializer,
    DiscoveryCandidateRescanSerializer,
    DiscoveryCandidateSerializer,
    DiscoveryProfileSerializer,
    DiscoveryRunCreateSerializer,
    DiscoveryRunSerializer,
)


class DiscoveryProfileListCreateAPIView(generics.ListCreateAPIView):
    """Список и создание профилей discovery."""

    queryset = DiscoveryProfile.objects.all().prefetch_related("auth_groups")
    serializer_class = DiscoveryProfileSerializer
    permission_classes = [DiscoveryAdminPermission]


class DiscoveryLookupAPIView(APIView):
    """Справочники для discovery UI без раскрытия секретов."""

    permission_classes = [DiscoveryAdminPermission]

    def get(self, request) -> Response:
        """Вернуть DeviceGroup и AuthGroup для форм discovery."""

        return Response(
            {
                "deviceGroups": list(
                    DeviceGroup.objects.order_by("name").values("id", "name", "description")
                ),
                "authGroups": list(AuthGroup.objects.order_by("name").values("id", "name", "description")),
            }
        )


class DiscoveryProfileDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Просмотр, изменение и удаление профиля discovery."""

    queryset = DiscoveryProfile.objects.all().prefetch_related("auth_groups")
    serializer_class = DiscoveryProfileSerializer
    permission_classes = [DiscoveryAdminPermission]

    def perform_destroy(self, instance: DiscoveryProfile) -> None:
        """Удалить профиль discovery и отозвать его активные запуски."""

        active_runs = instance.runs.filter(
            status__in=[DiscoveryRun.Status.PENDING, DiscoveryRun.Status.PROGRESS],
        ).exclude(task_id="")
        for run in active_runs:
            AsyncResult(run.task_id).revoke(terminate=True)
        instance.delete()


class DiscoveryRunListCreateAPIView(generics.ListAPIView):
    """Список запусков discovery и запуск новой задачи."""

    queryset = DiscoveryRun.objects.all().select_related("profile", "created_by")
    serializer_class = DiscoveryRunSerializer
    permission_classes = [DiscoveryAdminPermission]

    def post(self, request, *args, **kwargs):
        """Создать DiscoveryRun и отправить Celery-задачу."""

        serializer = DiscoveryRunCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.validated_data["profile"]
        networks = serializer.validated_data.get("networks")
        run = DiscoveryRun.objects.create(
            profile=profile,
            created_by=request.user,
            dry_run=serializer.validated_data["dry_run"],
        )
        task_result = discovery_run_task.delay(run.id, networks)
        run.refresh_from_db()
        response_data = DiscoveryRunSerializer(run).data
        response_data["task_id"] = run.task_id or str(task_result.id)
        return Response(response_data, status=status.HTTP_202_ACCEPTED)


class DiscoveryRunDetailAPIView(generics.RetrieveDestroyAPIView):
    """Детальная информация и удаление запуска discovery."""

    queryset = DiscoveryRun.objects.all().select_related("profile", "created_by")
    serializer_class = DiscoveryRunSerializer
    permission_classes = [DiscoveryAdminPermission]

    def perform_destroy(self, instance: DiscoveryRun) -> None:
        """Удалить запуск discovery и отозвать активную Celery-задачу."""

        if (
            instance.status in {DiscoveryRun.Status.PENDING, DiscoveryRun.Status.PROGRESS}
            and instance.task_id
        ):
            AsyncResult(instance.task_id).revoke(terminate=True)
        instance.delete()


class DiscoveryRunCancelAPIView(APIView):
    """Отмена запуска discovery."""

    permission_classes = [DiscoveryAdminPermission]

    def post(self, request, pk: int) -> Response:
        """Отозвать Celery-задачу discovery, если она еще выполняется."""

        run = get_object_or_404(DiscoveryRun, pk=pk)
        if run.task_id:
            AsyncResult(run.task_id).revoke(terminate=True)
        run.status = DiscoveryRun.Status.REVOKED
        run.save(update_fields=["status"])
        return Response(DiscoveryRunSerializer(run).data)


class DiscoveryCandidateListAPIView(generics.ListAPIView):
    """Список discovery candidates."""

    serializer_class = DiscoveryCandidateSerializer
    permission_classes = [DiscoveryAdminPermission]

    def get_queryset(self):
        """Вернуть отфильтрованный список кандидатов."""

        queryset = DiscoveryCandidate.objects.all().select_related("selected_auth_group", "device")
        status_filter = self.request.query_params.get("status")
        vendor = self.request.query_params.get("vendor")
        search = self.request.query_params.get("search")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if vendor:
            queryset = queryset.filter(vendor__icontains=vendor)
        if search:
            queryset = queryset.filter(name__icontains=search) | queryset.filter(ip__icontains=search)
        return queryset


class DiscoveryCandidateDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Просмотр, изменение и удаление discovery candidate."""

    queryset = DiscoveryCandidate.objects.all().select_related("selected_auth_group", "device")
    serializer_class = DiscoveryCandidateSerializer
    permission_classes = [DiscoveryAdminPermission]


class DiscoveryCandidateBulkDeleteAPIView(APIView):
    """Массовое удаление discovery candidates."""

    permission_classes = [DiscoveryAdminPermission]

    def post(self, request) -> Response:
        """Удалить выбранных кандидатов одним запросом."""

        serializer = DiscoveryCandidateBulkDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        queryset = DiscoveryCandidate.objects.filter(id__in=serializer.validated_data["ids"])
        deleted_count = queryset.count()
        queryset.delete()
        return Response({"deleted": deleted_count})


class DiscoveryCandidateRescanAPIView(APIView):
    """Повторный опрос выбранных discovery candidates."""

    permission_classes = [DiscoveryAdminPermission]

    def post(self, request) -> Response:
        """Запустить dry-run discovery только по IP выбранных кандидатов."""

        serializer = DiscoveryCandidateRescanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        candidate_ids = serializer.validated_data["ids"]
        candidates = {
            candidate.id: candidate for candidate in DiscoveryCandidate.objects.filter(id__in=candidate_ids)
        }
        skipped = []
        candidates_by_profile = defaultdict(list)

        for candidate_id in candidate_ids:
            candidate = candidates.get(candidate_id)
            if candidate is None:
                skipped.append({"id": candidate_id, "ip": "", "reason": "Кандидат не найден"})
                continue

            profile = self._get_last_profile(candidate)
            if profile is None:
                skipped.append(
                    {
                        "id": candidate.id,
                        "ip": candidate.ip,
                        "reason": "Нет истории discovery run для выбора профиля",
                    }
                )
                continue

            candidates_by_profile[profile].append(candidate)

        runs = []
        for profile, profile_candidates in candidates_by_profile.items():
            run = DiscoveryRun.objects.create(
                profile=profile,
                created_by=request.user,
                dry_run=True,
                summary={"rescanCandidateIds": [candidate.id for candidate in profile_candidates]},
            )
            task_result = discovery_run_task.delay(run.id, [candidate.ip for candidate in profile_candidates])
            run.refresh_from_db()
            run_data = DiscoveryRunSerializer(run).data
            run_data["task_id"] = run.task_id or str(task_result.id)
            runs.append(run_data)

        return Response({"runs": runs, "skipped": skipped}, status=status.HTTP_202_ACCEPTED)

    @staticmethod
    def _get_last_profile(candidate: DiscoveryCandidate) -> DiscoveryProfile | None:
        """Вернуть профиль последней discovery-попытки кандидата."""

        attempt = candidate.attempts.select_related("run__profile").order_by("-created_at").first()
        if attempt is None:
            return None
        return attempt.run.profile


class DiscoveryCandidateAcceptAPIView(APIView):
    """Принятие discovery candidate и создание Devices."""

    permission_classes = [DiscoveryAdminPermission]

    def post(self, request, pk: int) -> Response:
        """Создать устройство из кандидата."""

        candidate = get_object_or_404(DiscoveryCandidate, pk=pk)
        serializer = DiscoveryCandidateAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = accept_candidate(
            candidate,
            profile=None,
            device_group=serializer.validated_data.get("deviceGroup"),
            auth_group=serializer.validated_data.get("authGroup"),
            cmd_protocol=serializer.validated_data.get("cmdProtocol", ""),
            port_scan_protocol=serializer.validated_data.get("portScanProtocol", ""),
            snmp_community=serializer.validated_data.get("snmpCommunity", ""),
            collect_interfaces=serializer.validated_data["collectInterfaces"],
            user=request.user,
        )
        return Response({"deviceId": device.id, "deviceName": device.name}, status=status.HTTP_201_CREATED)


class DiscoveryCandidateIgnoreAPIView(APIView):
    """Игнорирование discovery candidate."""

    permission_classes = [DiscoveryAdminPermission]

    def post(self, request, pk: int) -> Response:
        """Пометить кандидата как игнорируемого."""

        candidate = get_object_or_404(DiscoveryCandidate, pk=pk)
        candidate.status = DiscoveryCandidate.Status.IGNORED
        candidate.save(update_fields=["status"])
        return Response(DiscoveryCandidateSerializer(candidate).data)
