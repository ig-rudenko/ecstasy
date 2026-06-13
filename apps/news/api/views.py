from django.core.cache import cache
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from apps.news.services import (
    ACTIVE_NEWS_CACHE_KEY,
    get_active_news,
    get_active_news_cache_timeout,
)

from .serializers import GlobalNewsSerializer


class GlobalNewsListAPIView(ListAPIView):
    """Return active global news for authenticated users."""

    serializer_class = GlobalNewsSerializer
    pagination_class = None

    def get_queryset(self):
        """Return permanent and unexpired news."""

        return get_active_news()

    def list(self, request, *args, **kwargs) -> Response:
        """Return cached serialized news or rebuild the cache from the database."""

        cached_news = cache.get(ACTIVE_NEWS_CACHE_KEY)
        if cached_news is not None:
            return Response(cached_news)

        news = list(self.get_queryset())
        serialized_news = [dict(item) for item in self.get_serializer(news, many=True).data]
        cache.set(
            ACTIVE_NEWS_CACHE_KEY,
            serialized_news,
            timeout=get_active_news_cache_timeout(news),
        )
        return Response(serialized_news)
