from django.db.models import F, Count
from rest_framework.generics import ListAPIView

from gpon.models import SubscriberConnection
from .serializers.statistics import OLTSubscriberSerializer


class OLTPortSubscribersCountAPIView(ListAPIView):
    serializer_class = OLTSubscriberSerializer

    def get_queryset(self):
        device_name = self.kwargs["device_name"]
        return (
            SubscriberConnection.objects.filter(
                tech_capability__end3__house_olt_states__statement__device__name__icontains=device_name
            )
            .annotate(olt_port=F("tech_capability__end3__house_olt_states__statement__olt_port"))
            .values("olt_port")
            .annotate(count=Count("id"))
            .order_by("olt_port")
        )
