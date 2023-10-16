from django.urls import path, include

from . import views

# /gpon/

app_name = "gpon"

urlpatterns = [
    path("", views.gpon_home, name="main"),
    path("api/", include("gpon.api.urls")),
    path("tech-data/", views.gpon_tech_data, name="tech-data"),
    path("tech-data/create", views.gpon_create_tech_data, name="create-tech-data"),
    path("tech-data/<device_name>", views.gpon_view_olt_tech_data, name="view-olt-tech-data"),
    path(
        "tech-data/end3/<int:pk>", views.gpon_view_end3_tech_data, name="view-tech-capability-data"
    ),
    path(
        "tech-data/building/<int:building_id>",
        views.gpon_view_building_tech_data,
        name="view-building-tech-data",
    ),
]

# Subscriber Data

urlpatterns += [
    path(
        "subscriber-data/create", views.gpon_create_subscriber_data, name="create-subscriber-data"
    ),
]
