from django.urls import path
from . import views

urlpatterns = [
    # path("mac-address/<device_name>/", views.MacAddressView.as_view()),
    path("traceroute/mac-address/<mac>/", views.MacTraceroute.as_view()),
    path("mac-scan/run", views.run_macs_scan, name="mac-scan-run"),
    path("mac-scan/check", views.check_periodically_scan, name="mac-scan-check"),
]
