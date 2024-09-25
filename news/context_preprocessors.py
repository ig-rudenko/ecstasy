from django.db.models import Q
from django.utils import timezone

from .models import GlobalNews


def global_news(request):
    return {
        "global_news": GlobalNews.objects.filter(
            Q(expired_at__isnull=True) | Q(expired_at__gt=timezone.now())
        ),
    }
