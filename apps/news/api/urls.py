from django.urls import path

from .views import GlobalNewsListAPIView

app_name = "news-api"

urlpatterns = [
    path("", GlobalNewsListAPIView.as_view(), name="news-list"),
]
