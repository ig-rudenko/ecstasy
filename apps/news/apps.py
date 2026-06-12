from django.apps import AppConfig


class NewsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.news"

    def ready(self) -> None:
        """Register global news cache invalidation signals."""

        from . import signals  # noqa: F401
