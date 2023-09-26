from django.urls import path, include

from gpon.views import gpon_home

# /gpon/

app_name = "gpon"

urlpatterns = [
    path("", gpon_home, name="main"),
    path("api/", include("gpon.api.urls")),
]
