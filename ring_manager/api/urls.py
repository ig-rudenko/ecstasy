from django.urls import path
from . import views
from . import access_ring_views

# /ring-manager/api/

urlpatterns = [
    path("transport-ring/<str:ring_name>", views.TransportRingDetailAPIView.as_view()),
    path("transport-ring/<str:ring_name>/status", views.TransportRingStatusAPIView.as_view()),
    path("transport-ring/<str:ring_name>/solutions", views.CreateSubmitSolutionsAPIView.as_view()),
    path("transport-ring/<str:ring_name>/solutions/last", views.GetLastSolutionsAPIView.as_view()),
    path("transport-rings", views.ListTransportRingsAPIView.as_view()),
    path("access-rings", access_ring_views.ListAccessRingsAPIView.as_view()),
    path("access-ring/<str:head_name>", access_ring_views.AccessRingDetailAPIView.as_view()),
]
