"""
accounts/permissions.py — RBAC permission classes
"""
from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Only ADMIN role can access."""
    message = 'Access restricted to Administrators only.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ADMIN')


class IsAdminOrIO(BasePermission):
    """ADMIN or Investigating Officer can access."""
    message = 'Access restricted to Administrators and Investigating Officers.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in ('ADMIN', 'IO')
        )


class IsAnyRole(BasePermission):
    """Any authenticated user (ADMIN, IO, COURT) can access."""
    message = 'Authentication required.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
