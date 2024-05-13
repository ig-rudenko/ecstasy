from typing import cast

from django.contrib.auth.models import User
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated


class UserAuthenticatedAPIView(GenericAPIView):
    """
    A simple view that returns the currently authenticated user.
    """

    permission_classes = [IsAuthenticated]

    @property
    def current_user(self) -> User:
        return cast(User, self.request.user)
