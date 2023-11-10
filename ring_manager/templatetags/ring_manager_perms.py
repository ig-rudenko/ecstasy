from django import template
from django.contrib.auth.models import AbstractUser

register = template.Library()


@register.filter
def has_access_ring_permission(user: AbstractUser) -> bool:
    return user.has_perm("auth.access_rings")


@register.filter
def has_transport_ring_permission(user: AbstractUser) -> bool:
    return user.has_perm("auth.access_transport_rings")


@register.filter
def has_any_ring_permission(user: AbstractUser) -> bool:
    return user.has_perm("auth.access_rings") or user.has_perm(
        "auth.access_transport_rings"
    )
