from django.http import Http404
from rest_framework.permissions import IsAuthenticated

from check.api.permissions import DevicePermission
from check.models import Devices
from check.services.filters import filter_devices_qs_by_user
from ecstasy_project.types.api import UserAuthenticatedAPIView


class DeviceAPIView(UserAuthenticatedAPIView):
    permission_classes = [IsAuthenticated, DevicePermission]
    lookup_url_kwarg = "device_name_or_ip"
    lookup_field = "name"

    def get_queryset(self):
        """
        ## Возвращаем queryset всех устройств из доступных для пользователя групп
        """
        return filter_devices_qs_by_user(Devices.objects.all(), self.current_user).select_related("group")

    def get_object(self) -> Devices:
        """Возвращает объект устройства по имени или IP адресу"""
        try:
            return super().get_object()
        except Http404:
            self.lookup_field = "ip"
            return super().get_object()
