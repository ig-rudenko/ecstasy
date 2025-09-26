from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from app_settings.models import AccessRingSettings
from check.api.permissions import DevicePermission
from check.models import Devices
from check.services.filters import filter_devices_qs_by_user

from ..base.helpers import collect_current_interfaces, thread_ping
from ..ring_finder import AggregationRingFinder
from .permissions import AccessRingPermission
from .serializers import AccessRingSerializer, PointRingSerializer


class ListAccessRingsAPIView(generics.ListAPIView):
    pagination_class = None
    serializer_class = AccessRingSerializer
    permission_classes = [IsAuthenticated, AccessRingPermission]

    def get_queryset(self):
        ring_settings = AccessRingSettings.load()
        if not ring_settings.agg_dev_name_regexp:
            return Devices.objects.none()

        return filter_devices_qs_by_user(
            Devices.objects.filter(name__iregex=ring_settings.agg_dev_name_regexp), self.request.user
        ).select_related("devicesinfo")

    def list(self, request, *args, **kwargs):
        ring_settings = AccessRingSettings.load()
        access_rings = []

        for agg in self.get_queryset():
            ring_finder = AggregationRingFinder(agg, ring_settings)
            ring_finder.start_find()
            access_rings.extend(ring_finder.get_rings())

        return Response(AccessRingSerializer(access_rings, many=True).data)


class AccessRingDetailAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, AccessRingPermission, DevicePermission]

    def get(self, request, head_name: str, *args, **kwargs):
        """
        Эта функция извлекает объект транспортного кольца, нормализует его, собирает все интерфейсы из его истории,
        находит связь между устройствами и возвращает сериализованный ответ данных устройств кольца.
        """

        device = get_object_or_404(Devices, name=head_name)
        self.check_object_permissions(request, device)

        ring_settings = AccessRingSettings.load()
        ring_finder = AggregationRingFinder(device, ring_settings)
        ring_finder.start_find()

        request_ports = self.request.GET.get("ports", "")

        for ring in ring_finder.get_rings():
            if ring.ports == request_ports:
                thread_ping(ring.devices)
                collect_current_interfaces(ring.devices)
                ring.find_links()
                ring.get_admin_down_info()
                points = PointRingSerializer(ring.devices, many=True).data
                break
        else:
            return Response(
                {"error": f"Не удалось найти кольцо на портах {request_ports}"},
                status=400,
            )

        return Response({"points": points})
