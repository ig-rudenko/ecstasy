
from django.urls import path
from .views import MacTraceroute

# /gather/api/

urlpatterns = [
    path("traceroute/mac-address/<mac>/", MacTraceroute.as_view()),
]
