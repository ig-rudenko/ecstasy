from typing import cast

from django.contrib.auth.base_user import AbstractBaseUser
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated


class UserAuthenticatedAPIView(GenericAPIView):
    """
    A simple view that returns the currently authenticated user.
    """

    permission_classes = [IsAuthenticated]

    @property
    def current_user(self) -> AbstractBaseUser:
        return cast(AbstractBaseUser, self.request.user)
