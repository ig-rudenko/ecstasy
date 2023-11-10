from django import template
from django.contrib.auth.models import AbstractUser

register = template.Library()


@register.filter
def has_wft_search_permission(user: AbstractUser) -> bool:
    return user.has_perm("auth.access_wtf_search")


@register.filter
def has_desc_search_permission(user: AbstractUser) -> bool:
    return user.has_perm("auth.access_desc_search")


@register.filter
def has_traceroute_permission(user: AbstractUser) -> bool:
    return user.has_perm("auth.access_traceroute")
