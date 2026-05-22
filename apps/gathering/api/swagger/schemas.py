from drf_yasg.utils import no_body, swagger_auto_schema

from ..serializers import (
    MacGatherScanTaskSerializer,
    MacGatherStatusSerializer,
    VlanGatherScanTaskSerializer,
    VlanGatherStatusSerializer,
)

mac_scan_status_api_doc = swagger_auto_schema(responses={200: MacGatherStatusSerializer()})
mac_scan_run_api_doc = swagger_auto_schema(
    responses={200: MacGatherScanTaskSerializer()}, request_body=no_body
)

vlan_scan_status_api_doc = swagger_auto_schema(responses={200: VlanGatherStatusSerializer()})
vlan_scan_run_api_doc = swagger_auto_schema(
    responses={200: VlanGatherScanTaskSerializer()}, request_body=no_body
)
