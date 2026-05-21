from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from ..serializers.common import End3Serializer, SubscriberConnectionSerializer
from ..serializers.create_subscriber_data import SubscriberDataSerializer
from ..serializers.create_tech_data import CreateTechDataSerializer
from ..serializers.statistics import OLTSubscriberSerializer
from ..serializers.view_subscriber_data import CustomerDetailSerializer
from ..serializers.view_tech_data import ViewOLTStatesTechDataSerializer
from .query_params import (
    BuildingAddressesQueryParamsSwaggerSerializer,
    DevicePortQueryParamsSwaggerSerializer,
    End3AddressesQueryParamsSwaggerSerializer,
    SearchPaginationQueryParamsSwaggerSerializer,
    SubscribersOnDevicePortQueryParamsSwaggerSerializer,
)
from .responses import (
    ErrorDetailResponseSwaggerSerializer,
    PaginatedSubscriberConnectionListResponseSwaggerSerializer,
    PaginatedTechDataListResponseSwaggerSerializer,
)

list_user_permissions_api_doc = swagger_auto_schema(
    responses={
        200: openapi.Response(
            description="List of user gpon permissions",
            schema=openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
        ),
    }
)

tech_data_list_api_doc = swagger_auto_schema(
    responses={
        200: PaginatedTechDataListResponseSwaggerSerializer(),
    }
)

tech_data_create_api_doc = swagger_auto_schema(
    request_body=CreateTechDataSerializer(),
    responses={
        201: CreateTechDataSerializer(),
        400: ErrorDetailResponseSwaggerSerializer(),
    },
)

view_olt_state_tech_data_api_doc = swagger_auto_schema(
    query_serializer=DevicePortQueryParamsSwaggerSerializer(),
    responses={
        200: ViewOLTStatesTechDataSerializer(),
        400: ErrorDetailResponseSwaggerSerializer(),
    },
)

devices_names_list_api_doc = swagger_auto_schema(
    responses={
        200: openapi.Response(
            description="List of devices names",
            schema=openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
        ),
    }
)

device_ports_list_api_doc = swagger_auto_schema(
    responses={
        200: openapi.Response(
            description="List of device ports",
            schema=openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
        ),
        400: ErrorDetailResponseSwaggerSerializer(),
    }
)

buildings_addresses_list_api_doc = swagger_auto_schema(
    query_serializer=BuildingAddressesQueryParamsSwaggerSerializer(),
)

end3_addresses_list_api_doc = swagger_auto_schema(
    query_serializer=End3AddressesQueryParamsSwaggerSerializer(),
    responses={
        200: End3Serializer(many=True),
    },
)

customers_list_api_doc = swagger_auto_schema(
    query_serializer=SearchPaginationQueryParamsSwaggerSerializer(),
)

subscriber_data_list_api_doc = swagger_auto_schema(
    responses={
        200: PaginatedSubscriberConnectionListResponseSwaggerSerializer(),
    }
)

subscriber_data_create_api_doc = swagger_auto_schema(
    request_body=SubscriberDataSerializer(),
    responses={
        201: SubscriberDataSerializer(),
        400: ErrorDetailResponseSwaggerSerializer(),
    },
)

customer_detail_api_doc = swagger_auto_schema(
    responses={
        200: CustomerDetailSerializer(),
    }
)

subscribers_on_device_port_api_doc = swagger_auto_schema(
    query_serializer=SubscribersOnDevicePortQueryParamsSwaggerSerializer(),
    responses={
        200: SubscriberConnectionSerializer(many=True),
        400: ErrorDetailResponseSwaggerSerializer(),
    },
)

olt_port_subscribers_count_api_doc = swagger_auto_schema(
    responses={
        200: OLTSubscriberSerializer(many=True),
    }
)
