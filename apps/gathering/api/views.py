from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.check.models import Devices
from apps.check.services.filters import filter_devices_qs_by_user
from apps.gathering.models import MacAddress, Vlan, VlanPort
from ecstasy_project.types.api import PageSizePageNumberPagination, UserAuthenticatedAPIView

from ..tasks import (
    get_mac_gather_status,
    get_vlan_gather_status,
    mac_table_gather_task,
    vlan_table_gather_task,
)
from .filters import MacAddressFilter, VlanFilter, VlanPortFilter
from .serializers import (
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
        devices = filter_devices_qs_by_user(Devices.objects.all(), self.current_user)  # noqa
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
        devices = filter_devices_qs_by_user(Devices.objects.all(), self.current_user)  # noqa
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
        devices = filter_devices_qs_by_user(Devices.objects.all(), self.current_user)  # noqa
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
