from rest_framework import serializers

from apps.news.models import GlobalNews


class GlobalNewsSerializer(serializers.ModelSerializer):
    """Serialize one global news item for the frontend."""

    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    expiredAt = serializers.DateTimeField(source="expired_at", read_only=True)

    class Meta:
        model = GlobalNews
        fields = ["id", "title", "content", "severity", "createdAt", "expiredAt"]
