from django.urls import path
from net_tools.api import views

# /api/tools/

urlpatterns = [
    path("find-by-desc", views.find_by_description),
    path("vlan-traceroute", views.get_vlan_traceroute),
    path("vlan-desc", views.get_vlan_desc),
    path("mac-vendor/<mac>", views.get_vendor),
    path("ip-mac-info/<ip_or_mac>", views.ip_mac_info),
    path("vlans-scan/run", views.run_periodically_scan),
    path("vlans-scan/check", views.check_periodically_scan),
]
