"""
URL Configuration
Расширенное от /device/
"""

from django.urls import path, include
from check import views

# /device/

urlpatterns = [
    path("<name>", views.device_info, name="device_info"),
    path("api/", include("check.api.urls")),
]
