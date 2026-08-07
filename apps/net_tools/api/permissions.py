from rest_framework import permissions
from rest_framework.request import Request


class InterfaceFinderPermission(permissions.BasePermission):
    def has_permission(self, request: Request, view):
        perm = "accounting.access_desc_search"
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_superuser or request.user.has_perm(perm))
        )


class WTFSearchPermission(permissions.BasePermission):
    def has_permission(self, request: Request, view):
        perm = "accounting.access_wtf_search"
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_superuser or request.user.has_perm(perm))
        )


class TracerouteAccessPermission(permissions.BasePermission):
    def has_permission(self, request: Request, view):
        perm = "accounting.access_traceroute"
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_superuser or request.user.has_perm(perm))
        )
