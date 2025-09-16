from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response

from ...models import UsersActions
from ..serializers import UserDeviceActionSerializer
from .base import DeviceAPIView


class UserDeviceActionsAPIView(DeviceAPIView, ListModelMixin):
    serializer_class = UserDeviceActionSerializer

    def get(self, request, *args, **kwargs):
        device = self.get_object()
        queryset = (
            UsersActions.objects.filter(device__name=device.name).values(
                "time", "user", "action", "user__username"
            )
        )[:200]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
