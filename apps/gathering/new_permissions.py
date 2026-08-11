from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


def create_permission(sender, **kwargs) -> None:
    """Создать право на чтение результатов периодического сбора."""

    content_type = ContentType.objects.get_for_model(get_user_model())
    Permission.objects.get_or_create(
        codename="access_gathering_results",
        name="Can view periodic gathering results",
        content_type=content_type,
    )
