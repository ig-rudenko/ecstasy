from django.urls import path, include

from gpon.views import (
    gpon_home,
    gpon_tech_data,
    gpon_create_tech_data,
    gpon_view_olt_tech_data,
    gpon_view_building_tech_data,
    gpon_view_tech_capability_data,
)

# /gpon/

app_name = "gpon"

urlpatterns = [
    path("", gpon_home, name="main"),
    path("api/", include("gpon.api.urls")),
    path("tech-data/", gpon_tech_data, name="tech-data"),
    path("tech-data/create", gpon_create_tech_data, name="create-tech-data"),
    path("tech-data/<device_name>", gpon_view_olt_tech_data, name="view-olt-tech-data"),
    path("tech-capability/<int:pk>", gpon_view_tech_capability_data, name="view-tech-capability-data"),
    path(
        "tech-data/building/<int:building_id>",
        gpon_view_building_tech_data,
        name="view-building-tech-data",
    ),
]
