from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response

from check.api.permissions import DevicePermission
from check.models import Devices
from .serializers import AccessRingSerializer, PointRingSerializer
from ..base.helpers import thread_ping, collect_current_interfaces
from ..ring_finder import AggregationRingFinder


class ListAccessRingsAPIView(generics.ListAPIView):
    pagination_class = None
    serializer_class = AccessRingSerializer

    def get_queryset(self):
        user_available_groups = self.request.user.profile.devices_groups.all().values_list(
            "id", flat=True
        )
        return Devices.objects.filter(
            group__name="SSW", group_id__in=user_available_groups
        ).select_related("devicesinfo")

    def list(self, request, *args, **kwargs):

        access_rings = []

        for agg in self.get_queryset():
            ring_finder = AggregationRingFinder(agg)
            ring_finder.start_find()
            access_rings.extend(ring_finder.get_rings())

        return Response(AccessRingSerializer(access_rings, many=True).data)


class AccessRingDetailAPIView(generics.GenericAPIView):
    permission_classes = [DevicePermission]

    def get(self, request, head_name: str, *args, **kwargs):
        """
        Эта функция извлекает объект транспортного кольца, нормализует его, собирает все интерфейсы из его истории,
        находит связь между устройствами и возвращает сериализованный ответ данных устройств кольца.
        """

        device = get_object_or_404(Devices, name=head_name)
        self.check_object_permissions(request, device)

        ring_finder = AggregationRingFinder(device)
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
                {"error": f"Не удалось найти кольцо на портах {request_ports}"}, status=400
            )

        return Response({"points": points})
