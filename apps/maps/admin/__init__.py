"""Admin entrypoint for maps app."""

from .admin_layers import LayersAdmin
from .admin_maps import MapsAdmin

__all__ = (
    "LayersAdmin",
    "MapsAdmin",
)
