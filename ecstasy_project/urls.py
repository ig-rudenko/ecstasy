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

from check import views
from django.conf import settings
from django.contrib.staticfiles.urls import static
from django.views.static import serve
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenObtainPairView,
    TokenVerifyView,
)

from .swagger import schema_view


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
    path("ring-manager/", include("ring_manager.urls")),
    path("api/token", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify", TokenVerifyView.as_view(), name="token_verify"),
]

# Документация API
urlpatterns += [
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
    re_path(r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]

handler404 = "app_settings.errors_views.page404"
handler500 = "app_settings.errors_views.page500"

# Static
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += (
        re_path(
            r"^static/(?P<path>.*)$",
            serve,
            {"document_root": settings.STATICFILES_DIRS[0]},
        ),
    )
    urlpatterns += (
        re_path(
            r"^media/(?P<path>.*)$",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        ),
    )
