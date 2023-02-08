"""
URL Configuration для API
Расширенное от /device/api/
"""

from django.urls import path
from . import views

# /device/api/

urlpatterns = [
    path("statistic/interfaces", views.InterfacesStatisticAPIView.as_view()),

    path("list_all", views.DevicesListAPIView.as_view()),
    path("<device_name>/interfaces", views.DeviceInterfacesAPIView.as_view()),
    path("<device_name>/info", views.DeviceInfoAPIView.as_view()),
    path("<device_name>/stats", views.DeviceStatsInfoAPIView.as_view()),
    path("comments", views.CreateInterfaceCommentAPIView.as_view()),
    path("comments/<int:pk>", views.InterfaceCommentAPIView.as_view()),
]
