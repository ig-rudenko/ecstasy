from django.db import transaction
from rest_framework.generics import ListAPIView, ListCreateAPIView

from gpon.models import Customer, SubscriberConnection
from .permissions import SubscriberDataPermission
from .serializers.common import CustomerSerializer
from .serializers.create_subscriber_data import CreateSubscriberDataSerializer


class CustomerRetrieveAPIView(ListAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class SubscriberDataListCreateAPIView(ListCreateAPIView):
    permission_classes = [SubscriberDataPermission]
    queryset = SubscriberConnection.objects.all()
    serializer_class = CreateSubscriberDataSerializer

    @transaction.atomic
    def perform_create(self, serializer) -> None:
        super().perform_create(serializer)
