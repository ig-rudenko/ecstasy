from django.urls import path, include

from . import views

# /ring-manager/

urlpatterns = [
    path("api/", include("ring_manager.api.urls")),
    path("", views.main_rings_view, name="ring-manager"),
    path("transport-rings/", views.transport_rings_view, name="transport-rings"),
    path("access-rings/", views.access_rings_view, name="access-rings"),
]
