from django.urls import path

from . import views

# /gpon/api/

app_name = "gpon-api"

urlpatterns = [
    path("tech-data", views.TechDataListCreateAPIView.as_view(), name="tech-data"),
    path("building/addresses", views.BuildingsAddressesListAPIView.as_view(), name="building-addresses"),
    path("splitter/addresses", views.SplitterAddressesListAPIView.as_view(), name="splitter-addresses"),
]
