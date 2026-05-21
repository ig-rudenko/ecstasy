from ipaddress import IPv4Address

from django.db.models import Q, QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from ...models import DeviceMedia, Devices
from ..permissions import DeviceMediaPermission, DevicePermission
from ..serializers import DeviceMediaSerializer


class DeviceMediaListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, DevicePermission]
    serializer_class = DeviceMediaSerializer
    lookup_url_kwarg = "device_name_or_ip"
    lookup_field = "name"

    def get_device(self) -> Devices:
        try:
            IPv4Address(self.kwargs.get(self.lookup_url_kwarg, ""))
        except ValueError:
            self.lookup_field = "name"
        else:
            self.lookup_field = "ip"

        filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_url_kwarg]}
        device = get_object_or_404(Devices, **filter_kwargs)
        self.check_object_permissions(self.request, device)
        return device

    def get_queryset(self) -> QuerySet[DeviceMedia]:
        device = self.get_device()
        queryset = device.medias.all().order_by("-mod_time", "-id")
        search_query = str(self.request.query_params.get("search", "")).strip()
        if search_query:
            queryset = queryset.filter(
                Q(file__icontains=search_query) | Q(description__icontains=search_query)
            )
        return queryset

    def perform_create(self, serializer) -> None:
        device = self.get_device()
        serializer.save(device=device)


class DeviceMediaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, DeviceMediaPermission]
    serializer_class = DeviceMediaSerializer
    queryset = DeviceMedia.objects.all()
