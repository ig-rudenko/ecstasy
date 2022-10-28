"""
URL Configuration
Расширенное от /device/
"""

from django.urls import path
from check import views

# /device/

urlpatterns = [

    path('port', views.get_port_detail, name='show-port-info'),
    path('port/reload', views.reload_port, name='port_reload'),
    path('port/cable-diag', views.start_cable_diag, name='cable-diag'),
    path('port/set-description', views.set_description, name='set-new-description'),

    path('session', views.show_session, name='show-session'),
    path('cut-session', views.cut_user_session, name='cut-session'),

    path('<name>', views.device_info, name='device_info'),
]
