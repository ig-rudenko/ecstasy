from django.urls import path, include
from . import views

# /gather/

urlpatterns = [
    path("mac-scan/run", views.run_macs_scan, name="mac-scan-run"),
    path("mac-scan/check", views.check_periodically_scan, name="mac-scan-check"),
    path("api/", include("gathering.api.urls")),
]
