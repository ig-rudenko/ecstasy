from django.urls import path

from .views import (
    MacGatherScanRunAPIView,
    MacGatherStatusAPIView,
    MacTracerouteAPIView,
    VlanDetailAPIView,
    VlanGatherScanRunAPIView,
    VlanGatherStatusAPIView,
    VlanListAPIView,
    VlanPortDetailAPIView,
    VlanPortListAPIView,
)

app_name = "gathering-api"

# /api/v1/gather/

urlpatterns = [
    path("traceroute/mac-address/<mac>/", MacTracerouteAPIView.as_view()),
    path("mac-address/scan/status", MacGatherStatusAPIView.as_view()),
    path("mac-address/scan/run", MacGatherScanRunAPIView.as_view()),
    path("vlan/scan/status", VlanGatherStatusAPIView.as_view(), name="vlan-scan-status"),
    path("vlan/scan/run", VlanGatherScanRunAPIView.as_view(), name="vlan-scan-run"),
    path("vlans/", VlanListAPIView.as_view(), name="vlan-list"),
    path("vlans/<int:pk>/", VlanDetailAPIView.as_view(), name="vlan-detail"),
    path("vlan-ports/", VlanPortListAPIView.as_view(), name="vlan-port-list"),
    path("vlan-ports/<int:pk>/", VlanPortDetailAPIView.as_view(), name="vlan-port-detail"),
]
