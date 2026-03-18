"""
Reusable permission classes shared across all apps.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminUser(BasePermission):
    """Allow access only to staff/admin users."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission — allow access if the requesting user
    owns the object or is staff.
    Assumes the model instance has a `user` attribute.
    """

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        return obj.user == request.user


class IsOwnerOrAdminOrReadOnly(BasePermission):
    """
    Read-only for anyone authenticated.
    Write access only for the owner or admin.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.user and request.user.is_staff:
            return True
        return obj.user == request.user
