from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.app_settings.models import AccessRingSettings
from apps.check.api.permissions import DevicePermission
from apps.check.models import Devices
from apps.check.services.filters import filter_devices_qs_by_user

from ..ring_finder import AggregationRingFinder, get_ring_by_device
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
        device_name = self.request.GET.get("device_name", "")

        for agg in self.get_queryset():
            ring_finder = AggregationRingFinder(agg, ring_settings)
            ring_finder.start_find()

            if device_name:  # Если нужно отфильтровать по названию оборудования в кольце
                for ring in ring_finder.get_rings():  # Проходимся по кольцам
                    for point in ring.devices:  # Проходимся по оборудованию в кольце
                        if device_name in point.device.name:  # Если название оборудование совпадает
                            access_rings.append(ring)  # Добавляем кольцо в финальный список
                            break  # Выходим, данное кольцо добавлено
            else:
                # Если нет фильтра, то добавляем всё кольцо
                access_rings.extend(ring_finder.get_rings())

        return Response(AccessRingSerializer(access_rings, many=True).data)


class AccessRingDetailAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, AccessRingPermission, DevicePermission]

    def get(self, request, head_name: str, *args, **kwargs):
        """
        Эта функция извлекает объект транспортного кольца, нормализует его, собирает все интерфейсы из его истории,
        находит связь между устройствами и возвращает сериализованный ответ данных устройств кольца.
        """
        true_values = {"1", "true", "yes"}

        request_ports = self.request.GET.get("ports", "")
        current_status = self.request.GET.get("current_status", "1").lower() in true_values
        collect_vlans = self.request.GET.get("collect_vlans", "1").lower() in true_values

        device = get_object_or_404(Devices, name=head_name)
        self.check_object_permissions(request, device)

        ring = get_ring_by_device(
            device,
            request_ports=request_ports,
            current_status=current_status,
            collect_vlans=collect_vlans,
        )
        if ring is None:
            return Response(
                {"error": f"Не удалось найти кольцо на портах {request_ports}"},
                status=400,
            )

        return Response({"points": PointRingSerializer(ring.devices, many=True).data})
