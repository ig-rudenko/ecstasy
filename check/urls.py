"""
URL Configuration
Расширенное от /device/
"""

from django.urls import path, include
from check import views

# /device/

urlpatterns = [
    path("port/reload", views.reload_port, name="port_reload"),
    path("<name>", views.device_info, name="device_info"),
]

# API
urlpatterns += [
    path("api/", include("check.api.urls")),
]
