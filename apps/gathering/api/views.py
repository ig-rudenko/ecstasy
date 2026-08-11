from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.check.models import Devices
from apps.check.services.filters import filter_devices_qs_by_user
from apps.gathering.models import DeviceGatheringResult, MacAddress, Vlan, VlanPort
from ecstasy_project.types.api import PageSizePageNumberPagination, UserAuthenticatedAPIView

from ..tasks import (
    get_mac_gather_status,
    get_vlan_gather_status,
    mac_table_gather_task,
    vlan_table_gather_task,
)
from .filters import DeviceGatheringResultFilter, MacAddressFilter, VlanFilter, VlanPortFilter
from .permissions import GatheringResultsPermission
from .serializers import (
    DeviceGatheringResultSerializer,
    MacAddressSerializer,
    VlanPortSerializer,
    VlanSerializer,
)
from .swagger.schemas import (
    mac_scan_run_api_doc,
    mac_scan_status_api_doc,
    vlan_scan_run_api_doc,
    vlan_scan_status_api_doc,
)


class MacAddressQuerysetMixin:
    def get_queryset(self):
        """Filter MAC address rows by user device access and optional query params."""
        devices = filter_devices_qs_by_user(Devices.objects.all(), self.current_user)
        queryset = MacAddress.objects.filter(device__in=devices).select_related("device")
        return queryset.distinct().order_by("device__name", "address", "vlan", "port")


class MacAddressListAPIView(MacAddressQuerysetMixin, UserAuthenticatedAPIView, ListAPIView):
    """Return collected MAC address rows for devices available to the user."""

    serializer_class = MacAddressSerializer
    pagination_class = PageSizePageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = MacAddressFilter


class MacAddressDetailAPIView(MacAddressQuerysetMixin, UserAuthenticatedAPIView, RetrieveAPIView):
    """Return one collected MAC address row."""

    serializer_class = MacAddressSerializer


class VlanQuerysetMixin:
    def get_queryset(self):
        """Filter VLANs by user device access and optional query params."""
        devices = filter_devices_qs_by_user(Devices.objects.all(), self.current_user)
        queryset = Vlan.objects.filter(device__in=devices).select_related("device").prefetch_related("ports")
        return queryset.distinct().order_by("device__name", "vlan")


class VlanListAPIView(VlanQuerysetMixin, UserAuthenticatedAPIView, ListAPIView):
    """Return collected VLAN rows for devices available to the user."""

    serializer_class = VlanSerializer
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = VlanFilter


class VlanDetailAPIView(VlanQuerysetMixin, UserAuthenticatedAPIView, RetrieveAPIView):
    """Return one collected VLAN row."""

    serializer_class = VlanSerializer


class VlanPortQuerysetMixin:
    def get_queryset(self):
        """Filter VLAN ports by user device access and optional query params."""
        devices = filter_devices_qs_by_user(Devices.objects.all(), self.current_user)
        queryset = VlanPort.objects.filter(vlan__device__in=devices).select_related("vlan", "vlan__device")
        return queryset.distinct().order_by("vlan__device__name", "vlan__vlan", "port")


class VlanPortListAPIView(VlanPortQuerysetMixin, UserAuthenticatedAPIView, ListAPIView):
    """Return collected VLAN port rows for devices available to the user."""

    serializer_class = VlanPortSerializer
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = VlanPortFilter


class VlanPortDetailAPIView(VlanPortQuerysetMixin, UserAuthenticatedAPIView, RetrieveAPIView):
    """Return one collected VLAN port row."""

    serializer_class = VlanPortSerializer


class DeviceGatheringResultQuerysetMixin:
    """Ограничить историю результатами доступного пользователю оборудования."""

    def get_queryset(self):
        """Вернуть оптимизированный queryset с device-level ограничением доступа."""

        devices = Devices.objects.all()
        if not self.current_user.is_superuser:
            devices = filter_devices_qs_by_user(devices, self.current_user)
        return (
            DeviceGatheringResult.objects.filter(device__in=devices)
            .select_related("task", "device", "device__group")
            .order_by("-started_at", "-id")
        )


class DeviceGatheringResultListAPIView(
    DeviceGatheringResultQuerysetMixin,
    UserAuthenticatedAPIView,
    ListAPIView,
):
    """Вернуть пагинированный список результатов периодического сбора."""

    serializer_class = DeviceGatheringResultSerializer
    pagination_class = PageSizePageNumberPagination
    permission_classes = [GatheringResultsPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_class = DeviceGatheringResultFilter


class DeviceGatheringTimelineAPIView(DeviceGatheringResultQuerysetMixin, UserAuthenticatedAPIView, APIView):
    """Вернуть диапазоны результатов для временной шкалы."""

    permission_classes = [GatheringResultsPermission]
    max_results = 5000

    def get(self, request) -> Response:
        """Применить общие фильтры и вернуть ограниченный набор диапазонов."""

        filterset = DeviceGatheringResultFilter(request.query_params, queryset=self.get_queryset())
        if not filterset.is_valid():
            raise ValidationError(filterset.errors)

        results = list(filterset.qs[: self.max_results + 1])
        truncated = len(results) > self.max_results
        serializer = DeviceGatheringResultSerializer(results[: self.max_results], many=True)
        return Response({"results": serializer.data, "truncated": truncated})


class DeviceGatheringLookupsAPIView(DeviceGatheringResultQuerysetMixin, UserAuthenticatedAPIView, APIView):
    """Вернуть справочники значений для фильтров истории сбора."""

    permission_classes = [GatheringResultsPermission]
    error_types_cache_timeout = 300

    def get(self, request) -> Response:
        """Сформировать доступные справочники и кэшировать уникальные типы ошибок."""

        queryset = self.get_queryset()
        devices = Devices.objects.filter(gathering_results__in=queryset).select_related("group").distinct()
        error_types_cache_key = f"gathering-result-error-types:{self.current_user.pk}"
        error_types = cache.get(error_types_cache_key)
        if error_types is None:
            error_types = list(
                queryset.exclude(error_type="")
                .order_by("error_type")
                .values_list("error_type", flat=True)
                .distinct()
            )
            cache.set(error_types_cache_key, error_types, timeout=self.error_types_cache_timeout)

        device_groups = list(devices.order_by("group__name").values("group_id", "group__name").distinct())
        return Response(
            {
                "device_groups": [
                    {"id": group["group_id"], "name": group["group__name"]} for group in device_groups
                ],
                "vendors": list(
                    devices.exclude(vendor__isnull=True)
                    .exclude(vendor="")
                    .order_by("vendor")
                    .values_list("vendor", flat=True)
                    .distinct()
                ),
                "models": list(
                    devices.exclude(model__isnull=True)
                    .exclude(model="")
                    .order_by("model")
                    .values_list("model", flat=True)
                    .distinct()
                ),
                "task_names": list(
                    queryset.order_by("task__name").values_list("task__name", flat=True).distinct()
                ),
                "error_types": error_types,
            }
        )


class MacGatherStatusAPIView(APIView):

    @mac_scan_status_api_doc
    def get(self, request):
        """Проверяет, выполняется ли сканирование MAC-адресов и возвращает результаты."""
        return Response(get_mac_gather_status())


class MacGatherScanRunAPIView(APIView):

    @mac_scan_run_api_doc
    def post(self, request):
        """Запускает сканирование MAC-адресов."""
        task_id = cache.get("mac_table_gather_task_id")
        if not task_id:
            task_id = mac_table_gather_task.delay()
            cache.set("mac_table_gather_task_id", task_id, timeout=None)
            return Response({"task_id": task_id}, status=201)

        return Response({"task_id": task_id}, status=200)


class VlanGatherStatusAPIView(APIView):

    @vlan_scan_status_api_doc
    def get(self, request):
        """Проверяет, выполняется ли сканирование VLAN-ов и возвращает результаты."""
        return Response(get_vlan_gather_status())


class VlanGatherScanRunAPIView(APIView):

    @vlan_scan_run_api_doc
    def post(self, request):
        """Запускает сканирование VLAN-ов."""
        task_id = cache.get("vlan_table_gather_task_id")
        if not task_id:
            task_id = vlan_table_gather_task.delay()
            cache.set("vlan_table_gather_task_id", task_id, timeout=None)
            return Response({"task_id": task_id}, status=201)

        return Response({"task_id": task_id}, status=200)
