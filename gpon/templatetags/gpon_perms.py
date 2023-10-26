from django import template
from django.contrib.auth.models import AbstractUser

register = template.Library()


@register.filter
def has_any_gpon_permissions(user: AbstractUser) -> bool:
    permissions = user.get_all_permissions()
    return any(p for p in permissions if p.startswith("gpon"))
