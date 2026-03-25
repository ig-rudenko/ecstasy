from drf_yasg.utils import swagger_auto_schema

from ..serializers import GetVlanDescQuerySerializer, VlanTracerouteQuerySerializer
from .serializers import (
    FindByDescQuerySerializer,
    GetVendorSerializer,
    GetVlanDescSerializer,
    SearchInterfaceByDescResultSerializer,
    VlanTracerouteSerializer,
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

vlan_traceroute_schema = swagger_auto_schema(
    methods=["GET"],
    query_serializer=VlanTracerouteQuerySerializer(),
    responses={200: VlanTracerouteSerializer()},
)
