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

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from maps.protected_serve import MapMediaServeLimitation

from .protected_serve import LoginRequiredLimitation, protected_serve
from .swagger import schema_view

urlpatterns = [
    path("admin/", admin.site.urls),
    # API Endpoints
    path("api/v1/devices/", include("check.api.urls")),
    path("api/v1/tools/", include("net_tools.api.urls")),
    path("api/v1/maps/", include("maps.api.urls")),
    path("api/v1/gather/", include("gathering.api.urls")),
    path("api/v1/gpon/", include("gpon.api.urls")),
    path("api/v1/ring-manager/", include("ring_manager.api.urls")),
    path("api/v1/accounts/", include("accounting.urls")),
    # JWT
    path("api/token", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify", TokenVerifyView.as_view(), name="token_verify"),
    # Документация API
    path("api/swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("api/swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger-ui"),
    path("api/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]

protected_serve.add_limitation(LoginRequiredLimitation())
protected_serve.add_limitation(MapMediaServeLimitation())
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
        protected_serve.serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
)

if settings.KEYCLOAK_ENABLE:
    urlpatterns.insert(
        0,
        path("oidc/", include("mozilla_django_oidc.urls")),
    )

if settings.ENV == "dev":
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()
    # urlpatterns += [
    #     re_path(
    #         r"^(?P<path>(?:assets|img|video).*)$",
    #         serve,
    #         {"document_root": settings.STATICFILES_DIRS[1]},
    #     ),
    #     re_path(".*", TemplateView.as_view(template_name="index.html"), name="index"),
    # ]
