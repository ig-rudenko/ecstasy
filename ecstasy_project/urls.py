"""AbonCheck URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from check import views
from django.contrib.staticfiles.utils import settings
from django.contrib.staticfiles.urls import static
from django.views.static import serve
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenObtainPairView,
    TokenVerifyView,
)

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Ecstasy API",
        default_version="v1",
        description="Здесь вы можете посмотреть API для работы с Ecstasy",
        contact=openapi.Contact(email="irudenko@sevtelecom.ru"),
        license=openapi.License(name="Apache-2.0"),
    ),
    patterns=[
        path("device/api/", include("check.api.urls")),
        path("api/token", TokenObtainPairView.as_view(), name="token_obtain_pair"),
        path("api/token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
        path("api/token/verify", TokenVerifyView.as_view(), name="token_verify"),
    ],
    authentication_classes=[
        SessionAuthentication,
        JWTAuthentication,
    ],
    public=False,
    permission_classes=[permissions.IsAdminUser],
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("by-zabbix/<hostid>", views.by_zabbix_hostid, name="by-zabbix-hostid"),
    path("devices", views.show_devices, name="devices-list"),
    path("device/", include("check.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("tools/", include("net_tools.urls")),
    path("maps/", include("maps.urls")),
    path("gather/", include("gathering.urls")),
    path("api/token", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify", TokenVerifyView.as_view(), name="token_verify"),
    # Документация API
    path(
        "swagger-ui/",
        TemplateView.as_view(
            template_name="swagger-ui.html",
        ),
        name="swagger-ui",
    ),
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    re_path(
        r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
    ),
]

handler404 = "app_settings.errors_views.page404"
handler500 = "app_settings.errors_views.page500"

# Static
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    urlpatterns += (
        re_path(
            r"^static/(?P<path>.*)$",
            serve,
            {"document_root": settings.STATICFILES_DIRS[0]},
        ),
    )
