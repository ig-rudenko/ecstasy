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
from check import views
from django.contrib.staticfiles.utils import settings
from django.contrib.staticfiles.urls import static
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("devices", views.show_devices, name="devices-list"),
    path("by-zabbix/<hostid>", views.by_zabbix_hostid, name="by-zabbix-hostid"),
    path("device/", include("check.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("tools/", include("net_tools.urls")),
    path("maps/", include("maps.urls")),
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
