from django.urls import path, include
from django.views.generic import TemplateView

# /ring-manager/

urlpatterns = [
    path("api/", include("ring_manager.api.urls")),
    path("", TemplateView.as_view(template_name="ring-manager/index.html"), name="ring-manager"),
    path(
        "transport-rings/",
        TemplateView.as_view(template_name="ring-manager/transport_rings.html"),
        name="transport-rings",
    ),
    path(
        "access-rings/",
        TemplateView.as_view(template_name="ring-manager/access_rings.html"),
        name="access-rings",
    ),
]
