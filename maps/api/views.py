from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from maps.models import Maps

from ..services.maps import get_map_layers_geo_data, get_zabbix_problems_on_map
from .permissions import MapPermission
from .serializers import MapDetailSerializer, MapLayerSerializer, MapSerializer


class MapPageNumberPagination(PageNumberPagination):
    page_size = 100


class MapListAPIView(generics.ListAPIView):
    queryset = Maps.objects.all()
    serializer_class = MapSerializer
    pagination_class = MapPageNumberPagination


class MapRetrieveAPIView(generics.RetrieveAPIView):
    queryset = Maps.objects.all()
    serializer_class = MapDetailSerializer


class MapLayersListAPIView(generics.RetrieveAPIView):
    queryset = Maps.objects.all()
    lookup_url_kwarg = "map_id"
    lookup_field = "id"
    permission_classes = [IsAuthenticated, MapPermission]
    serializer_class = MapLayerSerializer


class InteractiveMapAPIView(generics.RetrieveAPIView):
    queryset = Maps.objects.all()
    lookup_url_kwarg = "map_id"
    lookup_field = "id"
    permission_classes = [IsAuthenticated, MapPermission]

    def retrieve(self, request, *args, **kwargs) -> Response:
        """
        Эта функция извлекает данные из слоев объекта карты и возвращает их в формате списка.
        """
        map_obj = self.get_object()
        data = get_map_layers_geo_data(map_obj)
        return Response(data)


class UpdateInteractiveMapAPIView(generics.RetrieveAPIView):
    queryset = Maps.objects.all()
    lookup_url_kwarg = "map_id"
    lookup_field = "id"
    permission_classes = [IsAuthenticated, MapPermission]

    def retrieve(self, request, *args, **kwargs) -> Response:
        """
        # Проверяем какие из узлов сети недоступны на интерактивной карте с заданным идентификатором

        Возвращаем JSON ответ с проблемными узлами сети и подтверждение проблем (если они есть в Zabbix):

            {
                "problems": [
                    {"id": "host_id", "acknowledges": [["datetime", "text"], ... ]},
                    {"id": "host_id", "acknowledges": [["datetime", "text"], ... ]},
                    ...
                ]

            }
        """
        map_obj: Maps = self.get_object()
        problems = get_zabbix_problems_on_map(map_obj)
        return Response({"problems": problems})
