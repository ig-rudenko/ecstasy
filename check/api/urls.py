"""
URL Configuration для API
Расширенное от /device/api/
"""

from django.urls import path
from . import views

# /device/api/

urlpatterns = [
    path("list_all", views.DevicesListView.as_view()),
    path("<device_name>/interfaces", views.DeviceInterfacesView.as_view()),
    path("<device_name>/info", views.DeviceInfoView.as_view()),
    path("<device_name>/stats", views.DeviceStatsInfoView.as_view()),
    path("<device_name>/add-comment", views.CreateInterfaceCommentView.as_view()),
    path("comment/<int:pk>/update", views.UpdateInterfaceCommentView.as_view()),
    path("comment/<int:pk>/delete", views.DeleteInterfaceCommentView.as_view()),
]
