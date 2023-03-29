"""
URL Configuration для API
Расширенное от /device/api/
"""

from django.urls import path
from .views import devices_info, device_manager, bras_manager, config_files

# /device/api/

urlpatterns = [
    # ===========================================
    #               Devices Info
    # ===========================================
    path(
        "workload/interfaces",
        devices_info.AllDevicesInterfacesWorkLoadAPIView.as_view(),
    ),
    path(
        "workload/interfaces/<device_name>",
        devices_info.DeviceInterfacesWorkLoadAPIView.as_view(),
    ),
    path("list_all", devices_info.DevicesListAPIView.as_view()),
    path("<device_name>/interfaces", devices_info.DeviceInterfacesAPIView.as_view()),
    path("<device_name>/interface-info", device_manager.InterfaceInfoAPIView.as_view()),
    path("<device_name>/info", devices_info.DeviceInfoAPIView.as_view()),
    path("<device_name>/stats", devices_info.DeviceStatsInfoAPIView.as_view()),
    # ===========================================
    #                Config files
    # ===========================================
    path("<device_name>/collect-config", config_files.CollectConfigAPIView.as_view()),
    path("<device_name>/configs", config_files.ListDeviceConfigFilesAPIView.as_view()),
    path(
        "<device_name>/config/<file_name>",
        config_files.DownloadDeleteConfigAPIView.as_view(),
    ),
    # ===========================================
    #                Device Manager
    # ===========================================
    path("<device_name>/macs", device_manager.MacListAPIView.as_view()),
    path(
        "<device_name>/change-description", device_manager.ChangeDescription.as_view()
    ),
    path("<device_name>/cable-diag", device_manager.CableDiagAPIView.as_view()),
    path("<device_name>/set-poe-out", device_manager.SetPoEAPIView.as_view()),
    path(
        "<device_name>/change-dsl-profile",
        device_manager.ChangeDSLProfileAPIView.as_view(),
    ),
    path("comments", device_manager.CreateInterfaceCommentAPIView.as_view()),
    path("comments/<int:pk>", device_manager.InterfaceCommentAPIView.as_view()),
    # ===========================================
    #                 BRAS Manager
    # ===========================================
    path("session", bras_manager.BrassSessionAPIView.as_view(), name="show-session"),
    path(
        "cut-session", bras_manager.CutBrassSessionAPIView.as_view(), name="cut-session"
    ),
]
