from django.urls import path

from .crud_views import LayerListView, LayerUpdateView

# /maps/api/

urlpatterns = [
    path("layers/", LayerListView.as_view()),
    path("layers/<int:pk>/", LayerUpdateView.as_view()),
]
