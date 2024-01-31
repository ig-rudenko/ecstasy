from django.urls import path, include
from net_tools import views

# /tools/

urlpatterns = [
    path("find_descr/", views.search_description, name="find-descr"),
    path("tracerote/", views.traceroute, name="traceroute"),
    # API
    path("api/", include("net_tools.api.urls")),
    path("wtf/", views.search_wtf_is_it, name="search-wtf"),
    path("wtf/<mac>", views.search_wtf_is_it, name="search-mac-address"),
]
