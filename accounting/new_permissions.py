from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


def create_permission(sender, **kwargs):
    content_type = ContentType.objects.get_for_model(get_user_model())
    extra_permissions = [
        ("access_ecstasy_loop", "Has access to Ecstasy-Loop service"),
    ]

    for codename, name in extra_permissions:
        Permission.objects.get_or_create(codename=codename, name=name, content_type=content_type)
