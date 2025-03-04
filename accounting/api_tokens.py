from django.utils import timezone
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication

from .models import UserAPIToken


class CustomTokenAuthentication(TokenAuthentication):
    def authenticate_credentials(self, key):
        try:
            token = UserAPIToken.objects.select_related("user").get(key=key)
        except UserAPIToken.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid token")
        now = timezone.now()

        if token.expired is not None and token.expired < now:
            raise exceptions.AuthenticationFailed("Token has been expired")

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed("User inactive or deleted")

        token.last_used = now
        token.save(update_fields=["last_used"])

        return token.user, token
