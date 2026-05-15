from drf_yasg.utils import swagger_auto_schema

from apps.maps.api.swagger.responses import MapLayerRenderSerializer, MapUpdateLayersSerializer

map_layers_render_api_doc = swagger_auto_schema(
    responses={
        200: MapLayerRenderSerializer(),
    },
)

map_update_layers_api_doc = swagger_auto_schema(
    responses={
        200: MapUpdateLayersSerializer(),
    }
)
