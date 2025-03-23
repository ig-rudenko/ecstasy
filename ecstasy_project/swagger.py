from django.conf import settings
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication

from accounting.api_tokens import CustomTokenAuthentication
from ecstasy_project.authentication import CustomJWTAuthentication

access_token_lifetime_seconds: float = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].seconds / 60  # type: ignore


class CustomSchemaGenerator(OpenAPISchemaGenerator):
    def get_operation(self, view, path, prefix, method, components, request):
        # Преобразуем path и prefix в строки для избежания ошибки
        path = str(path)
        prefix = str(prefix)

        operation = super().get_operation(view, path, prefix, method, components, request)

        # Добавляем теги на основе маршрута
        if path.startswith("/api/v1/gpon/"):
            operation["tags"] = ["GPON"]
        elif path.startswith("/api/v1/maps/"):
            operation["tags"] = ["Maps"]
        elif path.startswith("/api/v1/devices/"):
            operation["tags"] = ["Devices"]
        elif path.startswith("/api/v1/ring-manager/"):
            operation["tags"] = ["Ring Manager"]
        elif path.startswith("/api/v1/token"):
            operation["tags"] = ["Token"]
        elif path.startswith("/api/v1/tools/"):
            operation["tags"] = ["Tools"]
        elif path.startswith("/api/v1/accounts/"):
            operation["tags"] = ["Accounts"]
        elif path.startswith("/api/v1/gather/"):
            operation["tags"] = ["Gather"]

        return operation


# Это представление для пользовательского интерфейса Swagger.
schema_view = get_schema_view(
    # Это описание API.
    openapi.Info(
        title="Ecstasy API",
        default_version="v1",
        description=f"""
## Здесь вы можете посмотреть API для работы с Ecstasy

API токен можно создать в панели администратора
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
        path("api/v1/accounts/", include("accounting.urls")),
        path("api/v1/devices/", include("check.api.urls")),
        path("api/v1/tools/", include("net_tools.api.urls")),
        path("api/v1/maps/", include("maps.api.urls")),
        path("api/v1/gather/", include("gathering.api.urls")),
        path("api/v1/gpon/", include("gpon.api.urls")),
        path("api/v1/ring-manager/", include("ring_manager.api.urls")),
    ],
    generator_class=CustomSchemaGenerator,
    authentication_classes=[
        SessionAuthentication,
        CustomTokenAuthentication,
        CustomJWTAuthentication,
    ],
    # Это означает, что пользовательский интерфейс Swagger недоступен для общего доступа.
    public=False,
    # Это означает, что пользовательский интерфейс Swagger не является общедоступным.
    permission_classes=[permissions.IsAuthenticated],
)
