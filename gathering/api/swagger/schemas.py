from drf_yasg.utils import swagger_auto_schema

from .responses import MacTracerouteSwaggerSerializer

# Изменяем состояние порта оборудования
mac_traceroute_api_doc = swagger_auto_schema(
    responses={200: MacTracerouteSwaggerSerializer()}
)
