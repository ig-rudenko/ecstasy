from django.urls import path

from . import views

# /gpon/api/

app_name = "api"

urlpatterns = [
    path("tech-data", views.TechDataListCreateAPIView.as_view(), name="tech-data"),
    path(
        "tech-data/<device_name>",
        views.ViewOLTStateTechDataAPIView.as_view(),
        name="view-olt-state-tech-data",
    ),
    path(
        "tech-data/building/<int:pk>",
        views.ViewBuildingTechDataAPIView.as_view(),
        name="view-building-tech-data",
    ),
    path(
        "tech-data/olt-state/<int:pk>",
        views.RetrieveUpdateOLTStateAPIView.as_view(),
        name="tech-data-olt-state",
    ),
    path(
        "tech-data/house-olt-state/<int:pk>",
        views.RetrieveUpdateHouseOLTState.as_view(),
        name="tech-data-house-olt-state",
    ),
    path(
        "tech-data/end3/<int:pk>",
        views.End3TechCapabilityAPIView.as_view(),
        name="tech-data-end3-capability",
    ),
    path(
        "tech-data/tech-capability/<int:pk>",
        views.TechCapabilityAPIView.as_view(),
        name="tech-data-tech-capability",
    ),
    path(
        "devices-names",
        views.DevicesNamesListAPIView.as_view(),
        name="devices-names",
    ),
    path(
        "ports-names/<str:device_name>",
        views.DevicePortsList.as_view(),
        name="ports-names",
    ),
    path(
        "addresses/buildings",
        views.BuildingsAddressesListAPIView.as_view(),
        name="building-addresses",
    ),
    path(
        "addresses/splitters",
        views.SplitterAddressesListAPIView.as_view(),
        name="splitter-addresses",
    ),
]
