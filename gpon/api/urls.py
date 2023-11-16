from django.urls import path

from . import subscriber_view
from . import views

# /gpon/api/

app_name = "api"

urlpatterns = [
    path("permissions", views.ListUserPermissions.as_view(), name="user-permissions"),
    path("tech-data", views.TechDataListCreateAPIView.as_view(), name="tech-data"),
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
        "tech-data/end3",
        views.End3CreateAPIView.as_view(),
        name="tech-data-end3-create",
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
        "tech-data/<device_name>",
        views.ViewOLTStateTechDataAPIView.as_view(),
        name="view-olt-state-tech-data",
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
        "addresses/end3",
        views.End3AddressesListAPIView.as_view(),
        name="splitter-addresses",
    ),
]

# ========== SUBSCRIBER DATA =============

# /gpon/api/

urlpatterns += [
    path(
        "customers",
        subscriber_view.CustomersListAPIView.as_view(),
        name="customers-list",
    ),
    path(
        "customers/<int:pk>",
        subscriber_view.CustomerDetailAPIView.as_view(),
        name="customer-detail",
    ),
    path(
        "subscriber-data",
        subscriber_view.SubscriberConnectionListCreateAPIView.as_view(),
        name="subscribers-data-list-create",
    ),
]
