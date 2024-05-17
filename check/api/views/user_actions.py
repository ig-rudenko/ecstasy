from .base import DeviceAPIView
from ..serializers import UserDeviceActionSerializer
from ...models import UsersActions


class UserDeviceActionsAPIView(DeviceAPIView):
    serializer_class = UserDeviceActionSerializer

    def get_queryset(self):
        device = self.get_object()
        return UsersActions.objects.filter(device__name=device.name).values(
            "time", "user", "action", "user__username"
        )
