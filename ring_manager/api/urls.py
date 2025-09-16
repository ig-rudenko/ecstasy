from django.urls import path

from . import access_ring_views, views

# /api/ring-manager/

app_name = "ring-manager-api"

urlpatterns = [
    path(
        "transport-ring/<str:ring_name>",
        views.TransportRingDetailAPIView.as_view(),
        name="transport-ring-detail",
    ),
    path(
        "transport-ring/<str:ring_name>/status",
        views.TransportRingStatusAPIView.as_view(),
        name="transport-ring-status",
    ),
    path(
        "transport-ring/<str:ring_name>/solutions",
        views.CreateSubmitSolutionsAPIView.as_view(),
        name="transport-ring-solutions",
    ),
    path(
        "transport-ring/<str:ring_name>/solutions/last",
        views.GetLastSolutionsAPIView.as_view(),
        name="transport-ring-solutions-last",
    ),
    path(
        "transport-rings",
        views.ListTransportRingsAPIView.as_view(),
        name="transport-rings",
    ),
    path(
        "access-rings",
        access_ring_views.ListAccessRingsAPIView.as_view(),
        name="access-rings",
    ),
    path(
        "access-ring/<str:head_name>",
        access_ring_views.AccessRingDetailAPIView.as_view(),
        name="access-ring-detail",
    ),
]
