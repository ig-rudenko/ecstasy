from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


def create_permission(sender, **kwargs) -> None:
    """Создать custom permission для доступа к auto discovery."""

    content_type = ContentType.objects.get_for_model(get_user_model())
    Permission.objects.get_or_create(
        codename="access_discovery",
        name="Can use auto discovery",
        content_type=content_type,
    )
