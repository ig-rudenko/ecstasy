from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import (
    GenericAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.request import Request
from rest_framework.response import Response

from ..models import Customer, OLTState, SubscriberConnection
from ..services.subscriber_data import get_subscribers_on_device_port
from .filters import SubscriberConnectionFilter
from .permissions import CustomerPermission, SubscriberDataPermission
from .serializers.common import CustomerSerializer, SubscriberConnectionSerializer
from .serializers.create_subscriber_data import SubscriberDataSerializer, UpdateSubscriberDataSerializer
from .serializers.view_subscriber_data import CustomerDetailSerializer
from .swagger import (
    customer_detail_api_doc,
    customers_list_api_doc,
    subscriber_data_create_api_doc,
    subscriber_data_list_api_doc,
    subscribers_on_device_port_api_doc,
)


@method_decorator(name="get", decorator=customers_list_api_doc)
class CustomersListAPIView(ListAPIView):
    queryset = Customer.objects.all().order_by("id")
    permission_classes = [CustomerPermission]
    serializer_class = CustomerSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = str(self.request.query_params.get("search", "")).strip()
        if search_query:
            queryset = queryset.filter(
                Q(surname__icontains=search_query)
                | Q(first_name__icontains=search_query)
                | Q(last_name__icontains=search_query)
                | Q(company_name__icontains=search_query)
                | Q(contract__icontains=search_query)
                | Q(phone__icontains=search_query)
            )
        return queryset


@method_decorator(name="get", decorator=customer_detail_api_doc)
class CustomerDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [CustomerPermission]
    serializer_class = CustomerDetailSerializer

    def get_queryset(self):
        if self.request.method == "GET":
            return Customer.objects.all().prefetch_related(
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
        return Customer.objects.all()


class SubscriberConnectionDetailAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = [SubscriberDataPermission]
    queryset = SubscriberConnection.objects.all().select_related("address").prefetch_related("services")
    serializer_class = UpdateSubscriberDataSerializer

    @transaction.atomic
    def perform_update(self, serializer) -> None:
        super().perform_update(serializer)


class SubscriberConnectionListCreateAPIView(ListCreateAPIView):
    permission_classes = [SubscriberDataPermission]
    queryset = SubscriberConnection.objects.all().order_by("id")
    filter_backends = [DjangoFilterBackend]
    filterset_class = SubscriberConnectionFilter

    def get_queryset(self):
        if self.request.method == "GET":
            return (
                SubscriberConnection.objects.all()
                .select_related("address", "customer", "tech_capability")
                .prefetch_related("services")
                .order_by("id")
            )
        return SubscriberConnection.objects.all().order_by("id")

    def get_serializer_class(self):
        if self.request.method == "GET":
            return SubscriberConnectionSerializer
        return SubscriberDataSerializer

    @subscriber_data_list_api_doc
    def get(self, request: Request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)

    @subscriber_data_create_api_doc
    @transaction.atomic
    def post(self, request: Request, *args, **kwargs) -> Response:
        return super().post(request, *args, **kwargs)

    @transaction.atomic
    def perform_create(self, serializer) -> None:
        super().perform_create(serializer)


class SubscribersOnDevicePort(GenericAPIView):
    permission_classes = [SubscriberDataPermission]
    queryset = SubscriberConnection.objects.all()

    @subscribers_on_device_port_api_doc
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
        except OLTState.DoesNotExist as exc:
            raise NotFound("OLT state does not exist.") from exc

        return Response(data)
