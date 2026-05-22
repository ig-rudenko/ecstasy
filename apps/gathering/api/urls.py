from django.urls import path

from .views import (
    MacAddressDetailAPIView,
    MacAddressListAPIView,
    VlanDetailAPIView,
    VlanListAPIView,
    VlanPortDetailAPIView,
    VlanPortListAPIView,
)

app_name = "gathering-api"

# /api/v1/gather/

urlpatterns = [
    path("mac-addresses/", MacAddressListAPIView.as_view(), name="mac-address-list"),
    path("mac-addresses/<int:pk>/", MacAddressDetailAPIView.as_view(), name="mac-address-detail"),
    path("vlans/", VlanListAPIView.as_view(), name="vlan-list"),
    path("vlans/<int:pk>/", VlanDetailAPIView.as_view(), name="vlan-detail"),
    path("vlan-ports/", VlanPortListAPIView.as_view(), name="vlan-port-list"),
    path("vlan-ports/<int:pk>/", VlanPortDetailAPIView.as_view(), name="vlan-port-detail"),
]
