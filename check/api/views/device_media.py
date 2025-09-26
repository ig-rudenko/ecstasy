from django.db.models import QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from check.models import DeviceMedia, Devices

from ..permissions import DeviceMediaPermission, DevicePermission
from ..serializers import DeviceMediaSerializer


class DeviceMediaListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, DevicePermission]
    serializer_class = DeviceMediaSerializer
    lookup_url_kwarg = "device_name_or_ip"
    lookup_field = "name"

    def get_device(self) -> Devices:
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        try:
            device = get_object_or_404(Devices, **filter_kwargs)
        except Http404:
            device = get_object_or_404(Devices, ip=self.kwargs[lookup_url_kwarg])
        self.check_object_permissions(self.request, device)
        return device

    def get_queryset(self) -> QuerySet[DeviceMedia]:
        device = self.get_device()
        return device.medias.all()

    def perform_create(self, serializer) -> None:
        device = self.get_device()
        serializer.save(device=device)


class DeviceMediaRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, DeviceMediaPermission]
    serializer_class = DeviceMediaSerializer
    queryset = DeviceMedia.objects.all()
