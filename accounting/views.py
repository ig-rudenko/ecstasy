from rest_framework.response import Response

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
