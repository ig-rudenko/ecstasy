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
from django.urls import path, include
from check import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.home, name='home'),
    path('devices', views.show_devices, name='devices-list'),
    path('device/port/mac', views.get_port_mac, name='get_mac'),
    path('device/port/reload', views.reload_port, name='port_reload'),
    path('session', views.show_session, name='show-session'),
    path('device/cut-session', views.cut_user_session, name='cut-session'),
    path('device/<name>', views.device_info, name='device_info'),
    path('by-zabbix/<hostid>', views.by_zabbix_hostid, name='by-zabbix-hostid'),

    path('accounts/', include('django.contrib.auth.urls')),

    path('tools/', include('net_tools.urls'))
]
