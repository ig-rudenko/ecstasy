from django.urls import path, include

from gpon.views import gpon_home, gpon_tech_data, gpon_create_tech_data

# /gpon/

app_name = "gpon"

urlpatterns = [
    path("", gpon_home, name="main"),
    path("api/", include("gpon.api.urls")),
    path("tech-data/", gpon_tech_data, name="tech-data"),
    path("tech-data/create", gpon_create_tech_data, name="create-tech-data"),
]
