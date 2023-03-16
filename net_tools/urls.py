from django.urls import path, include
from net_tools import views

# /tools/

urlpatterns = [
    path("find_descr/", views.search_description, name="find-descr"),
    path("tracerote/", views.traceroute, name="traceroute"),
    # AJAX
    path("ajax/", include("net_tools.ajax.urls")),
    path("wtf/", views.search_wtf_is_it, name="search-wtf"),
    path("wtf/<mac>", views.search_wtf_is_it, name="search-mac-address"),
]
