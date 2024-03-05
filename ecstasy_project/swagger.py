from django.conf import settings
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenObtainPairView,
    TokenVerifyView,
)

from gathering.api.views import MacTraceroute

access_token_lifetime_seconds: float = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].seconds / 60  # type: ignore

# Это представление для пользовательского интерфейса Swagger.
schema_view = get_schema_view(
    # Это описание API.
    openapi.Info(
        title="Ecstasy API",
        default_version="v1",
        description=f"""
## Здесь вы можете посмотреть API для работы с Ecstasy

Для работы с каждым endpoint `требуется токен` (JWT). Получить можно по URL `/api/token`.

Время жизни access токена - `{access_token_lifetime_seconds} минут`
Время жизни refresh токена - `{settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]}`
        """,
        contact=openapi.Contact(
            name=settings.CONTACT_NAME or "user",
            email=settings.CONTACT_EMAIL or "example@mail.com",
        ),
        license=openapi.License(
            name="License: Apache-2.0",
            url="https://github.com/ig-rudenko/ecstasy/blob/master/LICENSE",
        ),
    ),
    # Это список всех конечных точек, которые будут отображаться в Swagger.
    patterns=[
        path("device/api/", include("check.api.urls")),
        path("tools/api/", include("net_tools.api.urls")),
        path("api/token", TokenObtainPairView.as_view(), name="token_obtain_pair"),
        path("api/token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
        path("api/token/verify", TokenVerifyView.as_view(), name="token_verify"),
        path("gather/api/traceroute/mac-address/<mac>/", MacTraceroute.as_view()),
        path("maps/api/", include("maps.api.urls")),
    ],
    authentication_classes=[
        SessionAuthentication,
        JWTAuthentication,
    ],
    # Это означает, что пользовательский интерфейс Swagger недоступен для общего доступа.
    public=False,
    # Это означает, что пользовательский интерфейс Swagger не является общедоступным.
    permission_classes=[permissions.IsAuthenticated],
)
