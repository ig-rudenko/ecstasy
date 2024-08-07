from django.core.cache import cache
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
from .serializers.common import CustomerSerializer
from .serializers.create_subscriber_data import SubscriberDataSerializer, UpdateSubscriberDataSerializer
from .serializers.view_subscriber_data import CustomerDetailSerializer
from ..services.subscriber_data import (
    all_subscriber_connections_cache_key,
    get_all_subscriber_connections,
    get_subscribers_on_device_port,
)


class CustomersListAPIView(ListAPIView):
    queryset = Customer.objects.all()
    permission_classes = [CustomerPermission]
    serializer_class = CustomerSerializer


class CustomerDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    permission_classes = [CustomerPermission]
    serializer_class = CustomerDetailSerializer

    def put(self, request: Request, *args, **kwargs) -> Response:
        cache.delete(all_subscriber_connections_cache_key)
        return super().put(request, *args, **kwargs)

    def patch(self, request: Request, *args, **kwargs) -> Response:
        cache.delete(all_subscriber_connections_cache_key)
        return super().patch(request, *args, **kwargs)

    def delete(self, request: Request, *args, **kwargs) -> Response:
        cache.delete(all_subscriber_connections_cache_key)
        return super().delete(request, *args, **kwargs)


class SubscriberConnectionDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [SubscriberDataPermission]
    queryset = SubscriberConnection.objects.all()
    serializer_class = UpdateSubscriberDataSerializer

    @transaction.atomic
    def perform_update(self, serializer) -> None:
        super().perform_update(serializer)

    def put(self, request: Request, *args, **kwargs) -> Response:
        cache.delete(all_subscriber_connections_cache_key)
        return super().put(request, *args, **kwargs)

    def patch(self, request: Request, *args, **kwargs) -> Response:
        cache.delete(all_subscriber_connections_cache_key)
        return super().patch(request, *args, **kwargs)

    def delete(self, request: Request, *args, **kwargs) -> Response:
        cache.delete(all_subscriber_connections_cache_key)
        return super().delete(request, *args, **kwargs)


class SubscriberConnectionListCreateAPIView(ListCreateAPIView):
    permission_classes = [SubscriberDataPermission]
    queryset = SubscriberConnection.objects.all()
    serializer_class = SubscriberDataSerializer

    def get(self, request: Request, *args, **kwargs) -> Response:
        customers = get_all_subscriber_connections()
        return Response(customers.data)

    @transaction.atomic
    def perform_create(self, serializer) -> None:
        cache.delete(all_subscriber_connections_cache_key)
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
            data = get_subscribers_on_device_port(device_name, olt_port, ont_id)
        except OLTState.DoesNotExist:
            return Response({"error": "Does not exists."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data)
