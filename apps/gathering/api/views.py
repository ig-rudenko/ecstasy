import re

from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.check.models import Devices
from apps.check.services.filters import filter_devices_qs_by_user
from apps.gathering.models import Vlan, VlanPort
from ecstasy_project.types.api import UserAuthenticatedAPIView

from ..services.mac.traceroute import MacTraceroute
from ..tasks import (
    get_mac_gather_status,
    get_vlan_gather_status,
    mac_table_gather_task,
    vlan_table_gather_task,
)
from .filters import VlanFilter, VlanPortFilter
from .serializers import (
    MacGatherScanTaskSerializer,
    MacGatherStatusSerializer,
    VlanGatherScanTaskSerializer,
    VlanGatherStatusSerializer,
    VlanPortSerializer,
    VlanSerializer,
)
from .swagger.schemas import mac_traceroute_api_doc


class MacTracerouteAPIView(GenericAPIView):
    """
    # Находит все записи в базе данных, которые содержат необходимый MAC-адрес,
    а затем строит граф связей между этими MAC.
    """

    @mac_traceroute_api_doc
    def get(self, request, mac: str):
        try:
            vlan = int(request.GET.get("vlan", 0))
        except ValueError:
            vlan = 0
        mac_clean = "".join(re.findall(r"[0-9a-fA-F]+", mac)).lower()
        if len(mac_clean) != 12:
            return Response({"error": "Invalid MAC address"}, status=400)

        traceroute = MacTraceroute()
        return Response(traceroute.get_mac_graph(mac=mac_clean, vlan=vlan))


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


class MacGatherStatusAPIView(GenericAPIView):
    serializer_class = MacGatherStatusSerializer

    def get(self, request):
        """Проверяет, выполняется ли сканирование MAC-адресов и возвращает результаты."""
        return Response(get_mac_gather_status())


class MacGatherScanRunAPIView(GenericAPIView):
    serializer_class = MacGatherScanTaskSerializer

    def post(self, request):
        """Запускает сканирование MAC-адресов."""
        task_id = cache.get("mac_table_gather_task_id")
        if not task_id:
            task_id = mac_table_gather_task.delay()
            cache.set("mac_table_gather_task_id", task_id, timeout=None)
            return Response({"task_id": task_id}, status=201)

        return Response({"task_id": task_id}, status=200)


class VlanGatherStatusAPIView(GenericAPIView):
    serializer_class = VlanGatherStatusSerializer

    def get(self, request):
        """Проверяет, выполняется ли сканирование VLAN-ов и возвращает результаты."""
        return Response(get_vlan_gather_status())


class VlanGatherScanRunAPIView(GenericAPIView):
    serializer_class = VlanGatherScanTaskSerializer

    def post(self, request):
        """Запускает сканирование VLAN-ов."""
        task_id = cache.get("vlan_table_gather_task_id")
        if not task_id:
            task_id = vlan_table_gather_task.delay()
            cache.set("vlan_table_gather_task_id", task_id, timeout=None)
            return Response({"task_id": task_id}, status=201)

        return Response({"task_id": task_id}, status=200)
