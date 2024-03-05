from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated

from .filters import IdNameFilter
from .permissions import LayerModelPermission
from .serializers import LayerSerializer
from ..models import Layers


class LayerListView(ListAPIView):
    queryset = Layers.objects.all()
    serializer_class = LayerSerializer
    permission_classes = [IsAuthenticated, LayerModelPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IdNameFilter


class LayerUpdateView(UpdateAPIView):
    queryset = Layers.objects.all()
    serializer_class = LayerSerializer
    lookup_field = "pk"
    lookup_url_kwarg = "pk"
    permission_classes = [IsAuthenticated, LayerModelPermission]
