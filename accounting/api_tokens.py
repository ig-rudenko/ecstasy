from typing import Any

from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication, get_authorization_header
from rest_framework.request import Request

from .models import UserAPIToken


class CustomTokenAuthentication(TokenAuthentication):
    def authenticate(self, request: Request) -> tuple[Any, Any] | None:
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() not in [b"token", b"bearer"]:
            return None

        if len(auth) == 1:
            msg = _("Invalid token header. No credentials provided.")
            raise exceptions.AuthenticationFailed(msg)
        if len(auth) > 2:
            msg = _("Invalid token header. Token string should not contain spaces.")
            raise exceptions.AuthenticationFailed(msg)

        try:
            token = auth[1].decode()
        except UnicodeError as exc:
            msg = _("Invalid token header. Token string should not contain invalid characters.")
            raise exceptions.AuthenticationFailed(msg) from exc

        return self.authenticate_credentials_by_request(token, request)

    @staticmethod
    def authenticate_credentials_by_request(key: str, request: Request) -> tuple[Any, Any] | None:
        try:
            token: UserAPIToken = UserAPIToken.objects.select_related("user").get(key=key)
        except UserAPIToken.DoesNotExist as exc:
            raise exceptions.AuthenticationFailed("Invalid token") from exc
        now = timezone.now()

        if token.expired is not None and token.expired < now:
            raise exceptions.AuthenticationFailed("Token has been expired")

        client_ip = request.META.get("HTTP_X_FORWARDED_FOR") or request.META.get("REMOTE_ADDR")
        if not token.validate_ip(client_ip):
            raise exceptions.AuthenticationFailed(f"Your IP ({client_ip}) is not allowed to use this token")

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed("User inactive or deleted")

        token.last_used = now
        token.save(update_fields=["last_used"])

        return token.user, token
