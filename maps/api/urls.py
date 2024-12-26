from django.urls import path

from .crud_views import LayerListView, LayerUpdateView
from .views import (
    UpdateInteractiveMapAPIView,
    MapLayersListAPIView,
    InteractiveMapAPIView,
    MapListAPIView,
    MapRetrieveAPIView,
)

# /api/v1/maps/

app_name = "maps-api"

urlpatterns = [
    path("", MapListAPIView.as_view()),
    path("<int:pk>", MapRetrieveAPIView.as_view()),
    path("layers/", LayerListView.as_view()),
    path("layers/<int:pk>/", LayerUpdateView.as_view()),
    # Обновление точек на интерактивной карте
    path("<int:map_id>/update", UpdateInteractiveMapAPIView.as_view(), name="interactive-map-update"),
    # Возвращаем слои на интерактивной карте
    path("<int:map_id>/layers", MapLayersListAPIView.as_view(), name="interactive-map-layers"),
    # Возврат всех точек для интерактивной карты
    path("<int:map_id>/render", InteractiveMapAPIView.as_view(), name="interactive-map-render"),
]
