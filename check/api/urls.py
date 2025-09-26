"""
URL Configuration для API
Расширенное от /api/v1/devices/
"""

from django.urls import path

from .views import bras_manager, config_files, device_manager, device_media, devices_info, user_actions

app_name = "devices-api"

# /api/v1/devices/

urlpatterns = [
    path("by-zabbix/<int:host_id>", devices_info.GetDeviceByZabbixHostIDAPIView.as_view(), name="by-zabbix"),
    # ===========================================
    #                 Comments
    # ===========================================
    path("comments", device_manager.CreateInterfaceCommentAPIView.as_view()),
    path("comments/<int:pk>", device_manager.InterfaceCommentAPIView.as_view()),
    # ===========================================
    #                 BRAS Manager
    # ===========================================
    path("session", bras_manager.BrassSessionAPIView.as_view(), name="show-session"),
    path("cut-session", bras_manager.CutBrassSessionAPIView.as_view(), name="cut-session"),
    # ===========================================
    #               Devices Info
    # ===========================================
    path("", devices_info.DevicesListAPIView.as_view(), name="devices-list"),
    path(
        "workload/interfaces",
        devices_info.AllDevicesInterfacesWorkLoadAPIView.as_view(),
        name="all-devices-interfaces-workload",
    ),
    path("workload/interfaces/<device_name_or_ip>", devices_info.DeviceInterfacesWorkLoadAPIView.as_view()),
    path(
        "<device_name_or_ip>/interfaces",
        devices_info.DeviceInterfacesAPIView.as_view(),
        name="device-interfaces",
    ),
    path("<device_name_or_ip>/info", devices_info.DeviceInfoAPIView.as_view(), name="device-info"),
    path(
        "<device_name_or_ip>/vlan-info", devices_info.DeviceVlanInfoAPIView.as_view(), name="device-vlan-info"
    ),
    path(
        "<device_name_or_ip>/stats", devices_info.DeviceStatsInfoAPIView.as_view(), name="device-stats-info"
    ),
    path(
        "<device_name_or_ip>/actions",
        user_actions.UserDeviceActionsAPIView.as_view(),
        name="device-user-actions",
    ),
    # ===========================================
    #                Config files
    # ===========================================
    path("<device_name_or_ip>/collect-config", config_files.CollectConfigAPIView.as_view()),
    path("<device_name_or_ip>/configs", config_files.ListDeviceConfigFilesAPIView.as_view()),
    path(
        "<device_name_or_ip>/config/<file_name>",
        config_files.DownloadDeleteConfigAPIView.as_view(),
    ),
    # ===========================================
    #                Device Media
    # ===========================================
    path(
        "<device_name_or_ip>/media",
        device_media.DeviceMediaListCreateAPIView.as_view(),
        name="device-media-list-create",
    ),
    path(
        "<device_name_or_ip>/media/<int:pk>",
        device_media.DeviceMediaRetrieveUpdateDestroyAPIView.as_view(),
    ),
    # ===========================================
    #                Device Manager
    # ===========================================
    path("<device_name_or_ip>/interface-info", device_manager.InterfaceInfoAPIView.as_view()),
    path(
        "<device_name_or_ip>/port-status",
        device_manager.InterfaceControlAPIView.as_view(),
        name="port-control",
    ),
    path("<device_name_or_ip>/macs", device_manager.MacListAPIView.as_view(), name="mac-list"),
    path(
        "<device_name_or_ip>/change-description",
        device_manager.ChangeDescriptionAPIView.as_view(),
        name="set-description",
    ),
    path("<device_name_or_ip>/cable-diag", device_manager.CableDiagAPIView.as_view()),
    path("<device_name_or_ip>/set-poe-out", device_manager.SetPoEAPIView.as_view()),
    path("<device_name_or_ip>/change-dsl-profile", device_manager.ChangeDSLProfileAPIView.as_view()),
    path("<device_name_or_ip>/commands", device_manager.DeviceCommandsListAPIView.as_view()),
    path(
        "<device_name_or_ip>/commands/<int:command_id>/execute",
        device_manager.ExecuteDeviceCommandAPIView.as_view(),
    ),
    path(
        "<device_name_or_ip>/commands/<int:command_id>/validate",
        device_manager.ValidateDeviceCommandAPIView.as_view(),
    ),
]
