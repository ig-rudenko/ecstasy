from rest_framework.response import Response
from rest_framework.views import APIView

from .swagger.schemas import mac_traceroute_api_doc
from ..mac.traceroute import MacTraceroute


class MacTracerouteAPIView(APIView):
    """
    # Находит все записи в базе данных, которые содержат необходимый MAC-адрес,
    а затем строит граф связей между этими MAC.
    """

    @mac_traceroute_api_doc
    def get(self, request, mac: str):
        traceroute = MacTraceroute()
        return Response(traceroute.get_mac_graph(mac))
