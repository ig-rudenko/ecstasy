from ipaddress import IPv4Address

from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated

from ecstasy_project.types.api import UserAuthenticatedAPIView

from ...api.permissions import DevicePermission
from ...models import Devices
from ...services.filters import filter_devices_qs_by_user


class DeviceAPIView(UserAuthenticatedAPIView):
    permission_classes = [IsAuthenticated, DevicePermission]
    serializer_class = serializers.Serializer
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
            IPv4Address(self.kwargs.get(self.lookup_url_kwarg, ""))
        except ValueError:
            self.lookup_field = "name"
        else:
            self.lookup_field = "ip"
        return super().get_object()
