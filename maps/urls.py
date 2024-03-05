from django.urls import path, include

from maps import views
from maps.api import views as api_views

# maps/

urlpatterns = [
    # Домашняя страница для карт
    path("", views.map_home, name="map-home"),
    path("api/", include("maps.api.urls")),
    path(  # Обновление точек на интерактивной карте
        "<int:map_id>/api/update",
        api_views.UpdateInteractiveMapAPIView.as_view(),
        name="interactive-map-update",
    ),
    path(  # Возвращаем слои на интерактивной карте
        "<int:map_id>/api/layers",
        api_views.MapLayersListAPIView.as_view(),
        name="interactive-map-layers",
    ),
    path(  # Возврат всех точек для интерактивной карты
        "<int:map_id>/api/render",
        api_views.InteractiveMapAPIView.as_view(),
        name="interactive-map-render",
    ),
    path(  # Возвращаем шаблон интерактивной карты
        "<int:map_id>",
        views.show_interactive_map,
        name="interactive-map-show",
    ),
]
