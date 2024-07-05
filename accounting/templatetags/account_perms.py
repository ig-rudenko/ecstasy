from django import template
from django.contrib.auth.models import AbstractUser

register = template.Library()


@register.filter
def has_access_ecstasy_loop_permission(user: AbstractUser) -> bool:
    return user.has_perm("auth.access_ecstasy_loop")
