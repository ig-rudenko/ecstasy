from datetime import timedelta
from typing import Any

from django.conf import settings
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import gettext_lazy as _
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from rest_framework import serializers
from rest_framework.exceptions import APIException, ValidationError
from rest_framework_simplejwt.authentication import AuthUser, JWTAuthentication
from rest_framework_simplejwt.backends import TokenBackend
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import Token, UntypedToken
from rest_framework_simplejwt.utils import get_md5_hash_password

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

    def get_user_params(self, validated_token: Token) -> tuple[str, str]:
        # Ищем пользователя в собственном токене.
        if api_settings.USER_ID_CLAIM in validated_token:
            return api_settings.USER_ID_FIELD, validated_token[api_settings.USER_ID_CLAIM]

        # Ищем пользователя в токене Keycloak.
        if settings.KEYCLOAK_USER_ID_CLAIM in validated_token and settings.KEYCLOAK_ENABLE:
            return settings.KEYCLOAK_USER_ID_FIELD, validated_token[settings.KEYCLOAK_USER_ID_CLAIM]

        raise InvalidToken(_("Token contained no recognizable user identification"))  # type: ignore

    def get_user(self, validated_token: Token) -> AuthUser:  # type: ignore
        """
        Attempts to find and return a user using the given validated token.
        """
        key, value = self.get_user_params(validated_token)

        try:
            user = self.user_model.objects.get(**{key: value})
        except self.user_model.DoesNotExist as e:
            raise AuthenticationFailed(_("User not found"), code="user_not_found") from e  # type: ignore

        if api_settings.CHECK_USER_IS_ACTIVE and not user.is_active:
            raise AuthenticationFailed(_("User is inactive"), code="user_inactive")  # type: ignore

        if api_settings.CHECK_REVOKE_TOKEN and validated_token.get(
            api_settings.REVOKE_TOKEN_CLAIM
        ) != get_md5_hash_password(user.password):
            raise AuthenticationFailed(
                _("The user's password has been changed."), code="password_changed"  # type: ignore
            )

        return user  # type: ignore


class KeycloakToken(Token):
    """Обработка токенов от Keycloak"""

    token_type = "keycloak"
    lifetime = timedelta(seconds=60)
    _token_backend = TokenBackend(
        algorithm="RS256",
        signing_key=None,
        verifying_key="",
        audience=settings.KEYCLOAK_AUDIENCE,
        issuer=settings.KEYCLOAK_ISSUER,
        jwk_url=settings.KEYCLOAK_JWKS_URL,
        leeway=settings.KEYCLOAK_JWT_LEEWAY,
        json_encoder=None,
    )

    def verify_token_type(self) -> None:
        pass


class JWTAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # print("JWTAuthenticationMiddleware", request.user, request.user.is_authenticated)
        if request.user.is_authenticated:
            request._force_auth_user = request.user
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


class KeycloakBackend(OIDCAuthenticationBackend):

    def get_username(self, claims):
        return claims.get(settings.KEYCLOAK_USER_ID_CLAIM) or super().get_username(claims)

    def create_user(self, claims):
        user = super().create_user(claims)
        return self.update_user(user, claims)

    def update_user(self, user, claims):
        user.email = claims.get("email")
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")
        user.save()
        return user


def context_preprocessor_keycloak_enable(request):
    return {"keycloak_enabled": settings.KEYCLOAK_ENABLE}
