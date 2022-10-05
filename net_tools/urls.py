from django.urls import path, include
from net_tools import views

# /tools/

urlpatterns = [

    path('find_descr/', views.search_description, name='find-descr'),
    path('vlan-tracerote/', views.vlan_traceroute, name='vlan-traceroute'),

    # AJAX
    path('ajax/', include('net_tools.ajax.urls')),

    path('mac/', views.search_mac, name='search-mac'),
    path('mac/<mac>', views.search_mac, name='search-mac-address')
]