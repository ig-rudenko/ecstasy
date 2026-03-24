from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.response import Response

from ...models import UsersActions
from ...services.device.user_views import DeviceUserViews
from ..serializers import DeviceViewingsSerializer, UserDeviceActionSerializer
from ..swagger.schemas import set_device_viewings_api_doc
from .base import DeviceAPIView


class UserDeviceActionsAPIView(DeviceAPIView):
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


@method_decorator(set_device_viewings_api_doc, name="post")
class ViewingDeviceAPIView(DeviceAPIView):
    serializer_class = DeviceViewingsSerializer

    def get(self, request, *args, **kwargs):
        device = self.get_object()
        viewings = DeviceUserViews(device)

        serializer = self.get_serializer(viewings.get_viewings(), many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        device = self.get_object()
        viewings = DeviceUserViews(device)
        viewings.set_viewing(self.current_user.username)
        return Response(status=status.HTTP_200_OK)
