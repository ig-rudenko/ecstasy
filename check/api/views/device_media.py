from django.contrib.auth.views import LoginView
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from check.models import DeviceMedia, Devices
from ..permissions import DevicePermission, DeviceMediaPermission
from ..serializers import DeviceMediaSerializer


class DeviceMediaListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, DevicePermission]
    serializer_class = DeviceMediaSerializer
    lookup_url_kwarg = "device_name"
    lookup_field = "name"

    def get_device(self) -> Devices:
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        device = get_object_or_404(Devices, **filter_kwargs)
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
