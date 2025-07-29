from typing import Any

from django.conf import settings
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from future.backports.datetime import timedelta
from rest_framework import serializers
from rest_framework.exceptions import APIException, ValidationError
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import UntypedToken

if api_settings.BLACKLIST_AFTER_ROTATION:
    from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken


class CustomJWTAuthentication(JWTAuthentication):
    def auth_and_get_user(self, request):
        if not hasattr(request, "_force_auth_user"):
            # print("CustomJWTAuthentication user, token = self.authenticate(request)")
            try:
                data = self.authenticate(request)
            except APIException:
                return request.user
            if data is None:
                return request.user
            user, token = data
            request._force_auth_token = token
            request._force_auth_user = user
        # print("CustomJWTAuthentication", request._force_auth_user)
        return request._force_auth_user or request.user


class JWTAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # print("JWTAuthenticationMiddleware", request.user, request.user.is_authenticated)
        if request.user.is_authenticated:
            return

        auth = CustomJWTAuthentication()

        request.user = auth.auth_and_get_user(request)


class TokenVerifySerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True)

    def validate(self, attrs: dict[str, None]) -> dict[Any, Any]:
        token = UntypedToken(attrs["token"])

        if (
            api_settings.BLACKLIST_AFTER_ROTATION
            and "rest_framework_simplejwt.token_blacklist" in settings.INSTALLED_APPS
        ):
            jti = token.get(api_settings.JTI_CLAIM)
            if BlacklistedToken.objects.filter(
                token__jti=jti, blacklisted_at__lt=timezone.now() - timedelta(minutes=1)
            ).exists():
                raise ValidationError("Token is blacklisted")

        return {}
