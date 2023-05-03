from django.urls import path
from . import views

# /ring-manager/api/

urlpatterns = [
    path("transport-ring/<str:ring_name>", views.TransportRingDetailAPIView.as_view()),
    path("transport-rings", views.ListTransportRingsAPIView.as_view())
]
