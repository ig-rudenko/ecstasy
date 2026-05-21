from django.urls import path

from . import views

app_name = "discovery-api"

urlpatterns = [
    path("lookups", views.DiscoveryLookupAPIView.as_view(), name="lookups"),
    path("profiles", views.DiscoveryProfileListCreateAPIView.as_view(), name="profiles-list"),
    path("profiles/<int:pk>", views.DiscoveryProfileDetailAPIView.as_view(), name="profiles-detail"),
    path("runs", views.DiscoveryRunListCreateAPIView.as_view(), name="runs-list"),
    path("runs/<int:pk>", views.DiscoveryRunDetailAPIView.as_view(), name="runs-detail"),
    path("runs/<int:pk>/cancel", views.DiscoveryRunCancelAPIView.as_view(), name="runs-cancel"),
    path("candidates", views.DiscoveryCandidateListAPIView.as_view(), name="candidates-list"),
    path("candidates/<int:pk>", views.DiscoveryCandidateDetailAPIView.as_view(), name="candidates-detail"),
    path("candidates/<int:pk>/accept", views.DiscoveryCandidateAcceptAPIView.as_view(), name="candidates-accept"),
    path("candidates/<int:pk>/ignore", views.DiscoveryCandidateIgnoreAPIView.as_view(), name="candidates-ignore"),
]
