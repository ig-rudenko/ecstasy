from django.urls import path

from .views import MacTracerouteAPIView

# /gather/api/

urlpatterns = [
    path("traceroute/mac-address/<mac>/", MacTracerouteAPIView.as_view()),
]
