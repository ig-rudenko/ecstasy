from django.db import transaction
from rest_framework import status
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    GenericAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.request import Request
from rest_framework.response import Response

from gpon.models import Customer, SubscriberConnection, OLTState
from .permissions import SubscriberDataPermission, CustomerPermission
from .serializers.common import CustomerSerializer, SubscriberConnectionSerializer
from .serializers.create_subscriber_data import (
    SubscriberDataSerializer,
    UpdateSubscriberDataSerializer,
)
from .serializers.view_subscriber_data import CustomerDetailSerializer


class CustomersListAPIView(ListAPIView):
    queryset = Customer.objects.all()
    permission_classes = [CustomerPermission]
    serializer_class = CustomerSerializer


class CustomerDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    permission_classes = [CustomerPermission]
    serializer_class = CustomerDetailSerializer


class SubscriberConnectionDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [SubscriberDataPermission]
    queryset = SubscriberConnection.objects.all()
    serializer_class = UpdateSubscriberDataSerializer

    @transaction.atomic
    def perform_update(self, serializer) -> None:
        super().perform_update(serializer)


class SubscriberConnectionListCreateAPIView(ListCreateAPIView):
    permission_classes = [SubscriberDataPermission]
    queryset = SubscriberConnection.objects.all()
    serializer_class = SubscriberDataSerializer

    @transaction.atomic
    def perform_create(self, serializer) -> None:
        super().perform_create(serializer)


class SubscribersOnDevicePort(GenericAPIView):
    permission_classes = [SubscriberDataPermission]

    def get(self, request: Request, *args, **kwargs) -> Response:
        device_name = self.kwargs["device_name"]
        olt_port: str = self.request.query_params.get("port", "")
        ont_id: str = self.request.query_params.get("ont_id", "")
        if not olt_port:
            return Response(
                {"error": "Missing `port` parameter."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            olt = OLTState.objects.get(device__name=device_name, olt_port=olt_port)
        except OLTState.DoesNotExist:
            return Response({"error": "Does not exists."}, status=status.HTTP_400_BAD_REQUEST)

        subscriber_connections = [
            subscriber_connection
            for house_olt_state in olt.house_olt_states.all()
            for end3 in house_olt_state.end3_set.all()
            for tech_capability in end3.techcapability_set.all()
            for subscriber_connection in tech_capability.subscriber_connection.all().select_related(
                "customer"
            )
            if not ont_id or str(subscriber_connection.ont_id) == ont_id
        ]

        serializer = SubscriberConnectionSerializer(subscriber_connections, many=True)
        return Response(serializer.data, status=200)
