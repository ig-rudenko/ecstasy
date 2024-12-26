from django.urls import path

from .views import MacTracerouteAPIView, MacGatherStatusAPIView, MacGatherScanRunAPIView

# /api/v1/gather/

urlpatterns = [
    path("traceroute/mac-address/<mac>/", MacTracerouteAPIView.as_view()),
    path("mac-address/scan/status", MacGatherStatusAPIView.as_view()),
    path("mac-address/scan/run", MacGatherScanRunAPIView.as_view()),
]
