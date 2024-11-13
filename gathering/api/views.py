from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.views import APIView

from gathering.services.mac.traceroute import MacTraceroute
from .serializers import MacGatherStatusSerializer, MacGatherScanTaskSerializer
from .swagger.schemas import mac_traceroute_api_doc
from ..tasks import check_scanning_status, mac_table_gather_task


class MacTracerouteAPIView(APIView):
    """
    # Находит все записи в базе данных, которые содержат необходимый MAC-адрес,
    а затем строит граф связей между этими MAC.
    """

    @mac_traceroute_api_doc
    def get(self, request, mac: str):
        traceroute = MacTraceroute()
        return Response(traceroute.get_mac_graph(mac))


class MacGatherStatusAPIView(APIView):
    serializer_class = MacGatherStatusSerializer

    def get(self, request):
        """Проверяет, выполняется ли сканирование MAC-адресов и возвращает результаты."""
        return Response(check_scanning_status())


class MacGatherScanRunAPIView(APIView):
    serializer_class = MacGatherScanTaskSerializer

    def post(self, request):
        """Запускает сканирование MAC-адресов."""
        task_id = cache.get("mac_table_gather_task_id")
        if not task_id:
            task_id = mac_table_gather_task.delay()
            cache.set("mac_table_gather_task_id", task_id, timeout=None)
            return Response({"task_id": task_id}, status=201)

        return Response({"task_id": task_id}, status=200)
