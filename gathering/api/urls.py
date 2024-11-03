from django.urls import path

from .views import MacTracerouteAPIView

# /api/gather/

urlpatterns = [
    path("traceroute/mac-address/<mac>/", MacTracerouteAPIView.as_view()),
]
