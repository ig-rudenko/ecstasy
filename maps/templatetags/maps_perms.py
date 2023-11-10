from django import template
from django.contrib.auth.models import AbstractUser

register = template.Library()


@register.filter
def has_map_view_permission(user: AbstractUser) -> bool:
    return user.has_perm("auth.can_view_maps")
