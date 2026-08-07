from typing import cast

from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from apps.accounting.models import User


class UserAuthenticatedAPIView(GenericAPIView):
    """
    A simple view that returns the currently authenticated user.
    """

    permission_classes = [IsAuthenticated]

    @property
    def current_user(self) -> User:
        return cast(User, self.request.user)


class PageSizePageNumberPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 100
