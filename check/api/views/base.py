from django.http import Http404
from rest_framework.permissions import IsAuthenticated

from check.api.permissions import DevicePermission
from check.models import Devices
from ecstasy_project.types.api import UserAuthenticatedAPIView


class DeviceAPIView(UserAuthenticatedAPIView):
    permission_classes = [IsAuthenticated, DevicePermission]
    lookup_url_kwarg = "device_name"
    lookup_field = "name"

    def get_queryset(self):
        """
        ## Возвращаем queryset всех устройств из доступных для пользователя групп
        """
        return Devices.objects.filter(group__profile__user_id=self.current_user.id).select_related("group")

    def get_object(self) -> Devices:
        """Возвращает объект устройства по имени или IP адресу"""
        try:
            return super().get_object()
        except Http404:
            self.lookup_field = "ip"
            return super().get_object()
