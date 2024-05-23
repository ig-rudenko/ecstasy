from django.urls import path

from . import views

# /api/accounts/

urlpatterns = [
    path("myself", views.MyselfAPIView.as_view(), name="myself"),
    path("myself/permissions", views.MyselfPermissionsAPIView.as_view(), name="myself_permissions"),
]
