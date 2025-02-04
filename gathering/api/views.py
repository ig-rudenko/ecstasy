from django.core.cache import cache
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from gathering.services.mac.traceroute import MacTraceroute
from .serializers import (
    MacGatherStatusSerializer,
    MacGatherScanTaskSerializer,
    VlanGatherScanTaskSerializer,
    VlanGatherStatusSerializer,
)
from .swagger.schemas import mac_traceroute_api_doc
from ..tasks import (
    check_scanning_status,
    check_scanning_status_vlan,
    mac_table_gather_task,
    vlan_table_gather_task,
)


class MacTracerouteAPIView(GenericAPIView):
    """
    # Находит все записи в базе данных, которые содержат необходимый MAC-адрес,
    а затем строит граф связей между этими MAC.
    """

    @mac_traceroute_api_doc
    def get(self, request, mac: str):
        traceroute = MacTraceroute()
        return Response(traceroute.get_mac_graph(mac))


class MacGatherStatusAPIView(GenericAPIView):
    serializer_class = MacGatherStatusSerializer

    def get(self, request):
        """Проверяет, выполняется ли сканирование MAC-адресов и возвращает результаты."""
        return Response(check_scanning_status())


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
        return Response(check_scanning_status_vlan())


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
