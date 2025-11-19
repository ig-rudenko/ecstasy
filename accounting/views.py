from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounting.serializers import UserPermissionsSerializer, UserSerializer
from ecstasy_project.types.api import UserAuthenticatedAPIView


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
            }
        )
