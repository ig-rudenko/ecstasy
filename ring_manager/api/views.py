from django.shortcuts import get_object_or_404
from rest_framework import generics, response

from .serializers import RingSerializer, PointRingSerializer

from ..ring_manager import TransportRingManager, TransportRingNormalizer
from ..models import RingDev, TransportRing


class ListTransportRingsAPIView(generics.ListAPIView):
    pagination_class = None
    serializer_class = RingSerializer

    def get_queryset(self):
        return TransportRing.objects.filter(users=self.request.user).order_by("name")


class TransportRingDetailAPIView(generics.GenericAPIView):
    def get(self, request, ring_name: str, *args, **kwargs):
        ring = get_object_or_404(TransportRing, name=ring_name)
        TransportRingNormalizer(ring=ring).normalize()
        trm = TransportRingManager(ring=ring)

        trm.collect_all_interfaces()  # Берем из истории
        trm.find_link_between_devices()

        return response.Response(PointRingSerializer(trm.ring_devs, many=True).data)
