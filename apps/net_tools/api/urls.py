from django.urls import path

from ..api import views

# /api/v1/tools/

urlpatterns = [
    path("interfaces-finder", views.InterfaceFinderAPIView.as_view()),
    path("traceroute", views.TracerouteAPIView.as_view()),
    path("traceroute-map", views.TracerouteMapAPIView.as_view()),
    path("vlan-desc", views.VlanNameAPIView.as_view()),
    path("mac-vendor/<mac>", views.GetVendorByMacAPIView.as_view()),
    path("ip-mac-info/<ip_or_mac>", views.ARPSearchAPIView.as_view()),
]
