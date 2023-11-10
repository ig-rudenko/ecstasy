from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


def create_permission(sender, **kwargs):
    content_type = ContentType.objects.get_for_model(get_user_model())
    extra_permissions = [
        ("access_wtf_search", "Can use wtf search"),
        ("access_desc_search", "Can use desc search"),
        ("access_traceroute", "Can use traceroute"),
        ("access_run_interfaces_gather", "Can run interfaces gather"),
        ("access_run_mac_gather", "Can run mac gather"),
    ]

    for codename, name in extra_permissions:
        print(
            Permission.objects.get_or_create(
                codename=codename, name=name, content_type=content_type
            )
        )
