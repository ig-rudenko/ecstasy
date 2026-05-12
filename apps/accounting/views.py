from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ecstasy_project.types.api import UserAuthenticatedAPIView

from .serializers import UserPermissionsSerializer, UserSerializer


class MyselfAPIView(UserAuthenticatedAPIView):
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.current_user)
        return Response(serializer.data)


class MyselfPermissionsAPIView(UserAuthenticatedAPIView):
    serializer_class = UserPermissionsSerializer

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.current_user)
        return Response(serializer.data)


class OIDCAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return Response(
            {
                "enabled": settings.KEYCLOAK_ENABLE,
                "url": settings.KEYCLOAK_URL or "",
                "clientId": settings.KEYCLOAK_CLIENT_ID or "",
                "realm": settings.KEYCLOAK_REALM or "",
                "authorizationEndpoint": (
                    settings.OIDC_OP_AUTHORIZATION_ENDPOINT if settings.KEYCLOAK_ENABLE else ""
                ),
                "tokenEndpoint": settings.OIDC_OP_TOKEN_ENDPOINT if settings.KEYCLOAK_ENABLE else "",
                "userinfoEndpoint": settings.OIDC_OP_USER_ENDPOINT if settings.KEYCLOAK_ENABLE else "",
                "logoutEndpoint": (
                    f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/logout"
                    if settings.KEYCLOAK_ENABLE
                    else ""
                ),
            }
        )
