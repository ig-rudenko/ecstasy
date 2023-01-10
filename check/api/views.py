from rest_framework import generics
from rest_framework.response import Response
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from .serializers import DevicesSerializer
from .. import models


@method_decorator(login_required, name="dispatch")
class DevicesListAPIView(generics.ListAPIView):
    """
    ## Этот класс представляет собой ListAPIView, который возвращает список всех устройств в базе данных.
    """

    serializer_class = DevicesSerializer

    def get_queryset(self):
        """
        ## Возвращаем queryset всех устройств из доступных для пользователя групп
        """

        # Фильтруем запрос
        query = Q(
            group_id__in=[
                group["id"]
                for group in self.request.user.profile.devices_groups.all().values("id")
            ]
        )
        return models.Devices.objects.filter(query).select_related("group")

    def list(self, request, *args, **kwargs):
        """
        ## Возвращаем JSON список всех устройств, без пагинации
        """

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
