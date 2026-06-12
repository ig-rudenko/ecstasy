from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import GlobalNews
from .services import invalidate_active_news_cache


@receiver(post_save, sender=GlobalNews)
@receiver(post_delete, sender=GlobalNews)
def invalidate_global_news_cache(**kwargs) -> None:
    """Invalidate active news cache after a news row changes."""

    transaction.on_commit(invalidate_active_news_cache)
