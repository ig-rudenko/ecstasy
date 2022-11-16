from django.urls import path
from net_tools.ajax import views

# /tools/ajax/

urlpatterns = [
    # path('', views.search_description, name='ajax-find-description'),
    path("find", views.find_as_str, name="ajax-find"),
    path("vlantraceroute", views.get_vlan, name="ajax-vlan-traceroute"),
    path("vlan_desc", views.get_vlan_desc, name="ajax-get-vlan-desc"),
    path("mac_vendor/<mac>", views.get_vendor, name="ajax-get-vendor"),
    path("ip-mac-info/<ip_or_mac>", views.ip_mac_info, name="ajax-ip-mac-info"),
]
