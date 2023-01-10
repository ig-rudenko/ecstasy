"""
URL Configuration для API
Расширенное от /device/api/
"""

from django.urls import path
from . import views

# /device/api/

urlpatterns = [
    path("list_all", views.DevicesListAPIView.as_view())
]
