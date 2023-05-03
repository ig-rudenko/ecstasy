from django.urls import path, include

# /ring-manager/
from django.views.generic import TemplateView

urlpatterns = [
    path("api/", include("ring_manager.api.urls")),
    path("", TemplateView.as_view(template_name="ring-manager/index.html"), name="ring-manager")
]
