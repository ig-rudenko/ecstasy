from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response

from .base import DeviceAPIView
from ..serializers import UserDeviceActionSerializer
from ...models import UsersActions


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
