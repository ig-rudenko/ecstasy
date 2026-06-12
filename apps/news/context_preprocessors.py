from .services import get_active_news


def global_news(request):
    """Add active global news to the Django template context."""

    return {
        "global_news": get_active_news(),
    }
