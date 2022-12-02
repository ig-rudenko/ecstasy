from django.urls import path
from maps import views

# maps/

urlpatterns = [
    # Домашняя страница для карт
    path("", views.map_home, name="map-home"),
    # Обновление точек на интерактивной карте
    path(
        "<int:map_id>/api/update",
        views.update_interactive_map,
        name="interactive-map-update",
    ),
    # Возвращаем слои на интерактивной карте
    path(
        "<int:map_id>/api/layers",
        views.send_layers,
        name="interactive-map-layers",
    ),
    # Возврат всех точек для интерактивной карты
    path(
        "<int:map_id>/api/render",
        views.render_interactive_map,
        name="interactive-map-render",
    ),
    # Возвращаем шаблон интерактивной карты
    path(
        "<int:map_id>",
        views.show_interactive_map,
        name="interactive-map-show",
    ),
]
