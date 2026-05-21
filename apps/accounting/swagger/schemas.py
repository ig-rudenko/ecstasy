from drf_yasg.utils import swagger_auto_schema

from apps.accounting.serializers import UserSerializer
from apps.accounting.swagger.responses import OIDCSwaggerSchema, UserPermissionsSwaggerSerializer

myself_user_api_doc = swagger_auto_schema(
    responses={
        200: UserSerializer,
    }
)

myself_permissions_api_doc = swagger_auto_schema(
    responses={
        200: UserPermissionsSwaggerSerializer,
    }
)

oidc_api_doc = swagger_auto_schema(
    responses={
        200: OIDCSwaggerSchema,
    }
)
