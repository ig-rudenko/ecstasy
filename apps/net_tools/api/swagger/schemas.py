from drf_yasg.utils import swagger_auto_schema

from ..serializers import GetVlanDescQuerySerializer, TracerouteMapQuerySerializer, TracerouteQuerySerializer
from .serializers import (
    FindByDescQuerySerializer,
    GetVendorSerializer,
    GetVlanDescSerializer,
    SearchInterfaceByDescResultSerializer,
    TracerouteMapSerializer,
    TracerouteSerializer,
)

get_vendor_schema = swagger_auto_schema(
    methods=["GET"],
    responses={200: GetVendorSerializer()},
)


find_by_description_schema = swagger_auto_schema(
    methods=["GET"],
    query_serializer=FindByDescQuerySerializer(),
    responses={200: SearchInterfaceByDescResultSerializer()},
)

get_vlan_desc_schema = swagger_auto_schema(
    methods=["GET"],
    query_serializer=GetVlanDescQuerySerializer(),
    responses={200: GetVlanDescSerializer()},
)

traceroute_schema = swagger_auto_schema(
    methods=["GET"],
    query_serializer=TracerouteQuerySerializer(),
    responses={
        200: TracerouteSerializer(),
    },
)

traceroute_map_schema = swagger_auto_schema(
    methods=["GET"],
    query_serializer=TracerouteMapQuerySerializer(),
    responses={200: TracerouteMapSerializer()},
)
