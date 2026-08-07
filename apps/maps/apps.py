from django.apps import AppConfig
from django.db.models.signals import post_migrate

DEFAULT_TILE_LAYERS = (
    {
        "name": "Google geo",
        "url": "https://www.google.com/maps/vt?lyrs=s@189&gl=cn&x={x}&y={y}&z={z}",
        "crs": "EPSG:3857",
    },
    {
        "name": "ArcGIS Online",
        "url": "http://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "crs": "EPSG:3857",
    },
)


def create_default_tile_layers(sender, **kwargs):
    """Создать подложки карт по умолчанию после применения миграций."""

    from .models import TileLayer

    for tile_layer in DEFAULT_TILE_LAYERS:
        TileLayer.objects.update_or_create(
            url=tile_layer["url"],
            create_defaults={
                "crs": tile_layer["crs"],
                "name": tile_layer["name"],
            },
        )


class MapsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.maps"

    def ready(self):
        from .new_permissions import create_permission

        post_migrate.connect(create_permission, sender=self)
        post_migrate.connect(
            create_default_tile_layers,
            sender=self,
            dispatch_uid="maps.create_default_tile_layers",
        )
