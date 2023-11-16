from django.db import transaction
from rest_framework import status
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    GenericAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.response import Response

from gpon.models import Customer, SubscriberConnection, OLTState
from .permissions import SubscriberDataPermission, CustomerPermission
from .serializers.common import CustomerSerializer
from .serializers.create_subscriber_data import SubscriberDataSerializer
from .serializers.view_subscriber_data import CustomerDetailSerializer


class CustomersListAPIView(ListAPIView):
    queryset = Customer.objects
    permission_classes = [CustomerPermission]
    serializer_class = CustomerSerializer


class CustomerDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects
    permission_classes = [CustomerPermission]
    serializer_class = CustomerDetailSerializer


class SubscriberConnectionDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [SubscriberDataPermission]
    queryset = SubscriberConnection.objects
    serializer_class = SubscriberDataSerializer


class SubscriberConnectionListCreateAPIView(ListCreateAPIView):
    permission_classes = [SubscriberDataPermission]
    queryset = SubscriberConnection.objects
    serializer_class = SubscriberDataSerializer

    @transaction.atomic
    def perform_create(self, serializer) -> None:
        super().perform_create(serializer)
