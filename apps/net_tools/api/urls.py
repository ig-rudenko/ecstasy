from django.urls import path

from ..api import views

# /api/v1/tools/

urlpatterns = [
    path("interfaces-finder", views.InterfaceFinderAPIView.as_view()),
    path("traceroute", views.get_traceroute),
    path("traceroute-map", views.get_traceroute_map),
    path("vlan-desc", views.VlanNameAPIView.as_view()),
    path("mac-vendor/<mac>", views.GetVendorByMacAPIView.as_view()),
    path("ip-mac-info/<ip_or_mac>", views.ARPSearchAPIView.as_view()),
]
