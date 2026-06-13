import math
from collections.abc import Iterable
from datetime import datetime

from django.core.cache import cache
from django.db.models import Q, QuerySet
from django.utils import timezone

from .models import GlobalNews

ACTIVE_NEWS_CACHE_KEY = "news:active:v1"
ACTIVE_NEWS_CACHE_TIMEOUT = 24 * 60 * 60


def get_active_news() -> QuerySet[GlobalNews]:
    """Return permanent and unexpired global news ordered by creation time."""

    return GlobalNews.objects.filter(Q(expired_at__isnull=True) | Q(expired_at__gt=timezone.now()))


def get_active_news_cache_timeout(news: Iterable[GlobalNews], now: datetime | None = None) -> int:
    """Return a cache timeout bounded by the nearest news expiration."""

    current_time = now or timezone.now()
    expirations = [item.expired_at for item in news if item.expired_at is not None]
    if not expirations:
        return ACTIVE_NEWS_CACHE_TIMEOUT

    seconds_until_expiration = math.ceil((min(expirations) - current_time).total_seconds())
    return max(1, min(ACTIVE_NEWS_CACHE_TIMEOUT, seconds_until_expiration))


def invalidate_active_news_cache() -> None:
    """Remove the cached active news response."""

    cache.delete(ACTIVE_NEWS_CACHE_KEY)
