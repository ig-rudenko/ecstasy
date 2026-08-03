"""Admin entrypoint for maps app."""

from .admin_layers import LayersAdmin
from .admin_maps import MapsAdmin
from .admin_tile_layers import TileLayerAdmin

__all__ = (
    "LayersAdmin",
    "MapsAdmin",
    "TileLayerAdmin",
)
