from django.db import transaction
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateAPIView

from gpon.models import Customer, SubscriberConnection
from .permissions import SubscriberDataPermission, CustomerPermission
from .serializers.common import CustomerSerializer
from .serializers.create_subscriber_data import SubscriberDataSerializer
from .serializers.view_subscriber_data import CustomerDetailSerializer


class CustomersListAPIView(ListAPIView):
    queryset = Customer.objects
    permission_classes = [CustomerPermission]
    serializer_class = CustomerSerializer


class CustomerDetailAPIView(RetrieveUpdateAPIView):
    queryset = Customer.objects
    permission_classes = [CustomerPermission]
    serializer_class = CustomerDetailSerializer


class SubscriberConnectionListCreateAPIView(ListCreateAPIView):
    permission_classes = [SubscriberDataPermission]
    queryset = SubscriberConnection.objects
    serializer_class = SubscriberDataSerializer

    @transaction.atomic
    def perform_create(self, serializer) -> None:
        super().perform_create(serializer)
