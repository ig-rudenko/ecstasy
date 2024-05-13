from rest_framework.generics import ListAPIView

from ..serializers import UserDeviceActionSerializer
from ...models import UsersActions


class UserDeviceActionsAPIView(ListAPIView):
    serializer_class = UserDeviceActionSerializer

    def get_queryset(self):
        device_name = self.kwargs["device_name"]
        return UsersActions.objects.filter(device__name=device_name).values(
            "time", "user", "action", "user__username"
        )
