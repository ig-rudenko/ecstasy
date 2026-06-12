from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.news.models import GlobalNews
from apps.news.services import ACTIVE_NEWS_CACHE_TIMEOUT, get_active_news_cache_timeout


class GlobalNewsAPITests(APITestCase):
    """Tests for the global news API."""

    def setUp(self) -> None:
        """Create an authenticated user."""

        self.user = get_user_model().objects.create_user(username="operator", password="password")
        self.url = reverse("news-api:news-list")
        cache.clear()

    def tearDown(self) -> None:
        """Clear cached news between tests."""

        cache.clear()
        super().tearDown()

    def test_news_list_requires_authentication(self):
        """Anonymous users cannot read global news."""

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_news_list_returns_only_active_news_newest_first(self):
        """The API returns permanent and unexpired news, excluding expired rows."""

        now = timezone.now()
        permanent = GlobalNews.objects.create(
            title="Новая возможность",
            content="Теперь доступен новый раздел.",
            severity=GlobalNews.SevSeverityChoices.SUCCESS,
        )
        scheduled = GlobalNews.objects.create(
            title="Технические работы",
            content="Работы начнутся сегодня в 23:00.",
            severity=GlobalNews.SevSeverityChoices.WARNING,
            expired_at=now + timedelta(hours=2),
        )
        GlobalNews.objects.create(
            title="Устаревшее сообщение",
            content="Это сообщение больше не должно отображаться.",
            severity=GlobalNews.SevSeverityChoices.INFO,
            expired_at=now - timedelta(minutes=1),
        )
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [scheduled.id, permanent.id])
        self.assertEqual(
            response.data[0],
            {
                "id": scheduled.id,
                "title": "Технические работы",
                "content": "Работы начнутся сегодня в 23:00.",
                "severity": "warning",
                "createdAt": response.data[0]["createdAt"],
                "expiredAt": response.data[0]["expiredAt"],
            },
        )
        self.assertIsNotNone(response.data[0]["expiredAt"])
        self.assertIsNone(response.data[1]["expiredAt"])

    def test_news_list_caches_empty_response(self):
        """Repeated empty responses do not query the database."""

        self.client.force_authenticate(self.user)

        first_response = self.client.get(self.url)
        with self.assertNumQueries(0):
            second_response = self.client.get(self.url)

        self.assertEqual(first_response.data, [])
        self.assertEqual(second_response.data, [])

    def test_news_list_caches_serialized_news(self):
        """Repeated populated responses use serialized cache data."""

        GlobalNews.objects.create(
            title="Технические работы",
            content="Кратковременный перерыв связи.",
            severity=GlobalNews.SevSeverityChoices.WARNING,
        )
        self.client.force_authenticate(self.user)

        first_response = self.client.get(self.url)
        with self.assertNumQueries(0):
            second_response = self.client.get(self.url)

        self.assertEqual(second_response.data, first_response.data)

    def test_news_cache_is_invalidated_after_save_and_delete(self):
        """Saving or deleting news makes the next response rebuild the cache."""

        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(self.url).data, [])

        with self.captureOnCommitCallbacks(execute=True):
            news = GlobalNews.objects.create(
                title="Новая функция",
                content="Описание новой функции.",
                severity=GlobalNews.SevSeverityChoices.SUCCESS,
            )
        created_response = self.client.get(self.url)
        self.assertEqual([item["id"] for item in created_response.data], [news.id])

        news.title = "Обновлённая функция"
        with self.captureOnCommitCallbacks(execute=True):
            news.save(update_fields=["title"])
        updated_response = self.client.get(self.url)
        self.assertEqual(updated_response.data[0]["title"], "Обновлённая функция")

        with self.captureOnCommitCallbacks(execute=True):
            news.delete()
        self.assertEqual(self.client.get(self.url).data, [])

    def test_cache_timeout_is_limited_by_nearest_expiration(self):
        """Cached news expires no later than the nearest active news row."""

        now = timezone.now()
        permanent = GlobalNews(expired_at=None)
        expiring = GlobalNews(expired_at=now + timedelta(seconds=90))

        self.assertEqual(get_active_news_cache_timeout([], now), ACTIVE_NEWS_CACHE_TIMEOUT)
        self.assertEqual(get_active_news_cache_timeout([permanent, expiring], now), 90)
