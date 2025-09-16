from django.core.cache import cache
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (
    GenericAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.request import Request
from rest_framework.response import Response

from gpon.models import Customer, OLTState, SubscriberConnection

from ..services.subscriber_data import (
    all_subscriber_connections_cache_key,
    get_all_subscriber_connections,
    get_subscribers_on_device_port,
)
from .permissions import CustomerPermission, SubscriberDataPermission
from .serializers.common import CustomerSerializer
from .serializers.create_subscriber_data import SubscriberDataSerializer, UpdateSubscriberDataSerializer
from .serializers.view_subscriber_data import CustomerDetailSerializer


class CustomersListAPIView(ListAPIView):
    queryset = Customer.objects.all()
    permission_classes = [CustomerPermission]
    serializer_class = CustomerSerializer


class CustomerDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [CustomerPermission]
    serializer_class = CustomerDetailSerializer

    def get_queryset(self):
        if self.request.method == "GET":
            queryset = Customer.objects.all().prefetch_related(
                "connections",
                "connections__address",
                "connections__services",
                "connections__tech_capability",
                "connections__tech_capability__end3",
                "connections__tech_capability__end3__address",
                "connections__tech_capability__end3__house_olt_states",
                "connections__tech_capability__end3__house_olt_states__house__address",
                "connections__tech_capability__end3__house_olt_states__statement__device",
            )
            return queryset
        return Customer.objects.all()

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
    queryset = SubscriberConnection.objects.all().select_related("address").prefetch_related("services")
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
        customers_data = get_all_subscriber_connections()
        return Response(customers_data)

    @transaction.atomic
    def perform_create(self, serializer) -> None:
        cache.delete(all_subscriber_connections_cache_key)
        super().perform_create(serializer)


class SubscribersOnDevicePort(GenericAPIView):
    permission_classes = [SubscriberDataPermission]
    queryset = SubscriberConnection.objects.all()

    def get(self, request: Request, *args, **kwargs) -> Response:
        device_name = self.kwargs["device_name"]
        olt_port: str = self.request.query_params.get("port", "")
        try:
            ont_id: int = int(self.request.query_params.get("ont_id", 0))
        except ValueError as exc:
            raise ValidationError("`ont_id` parameter must be an integer") from exc
        if not olt_port:
            raise ValidationError("Missing `port` parameter.")

        try:
            data = get_subscribers_on_device_port(device_name, olt_port, ont_id)
        except OLTState.DoesNotExist:
            return Response({"error": "Does not exists."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data)
