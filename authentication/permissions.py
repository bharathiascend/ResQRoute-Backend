from rest_framework import permissions
from .models import UserRole


class IsDriver(permissions.BasePermission):
    """Allows access only to authenticated drivers."""
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role == UserRole.DRIVER
        )


class IsCustomer(permissions.BasePermission):
    """Allows access only to authenticated customers / operations users."""
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role == UserRole.CUSTOMER
        )


class IsAdmin(permissions.BasePermission):
    """Allows access only to admin / control center users."""
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.role == UserRole.ADMIN or request.user.is_staff or request.user.is_superuser)
        )


class IsDriverOrAdmin(permissions.BasePermission):
    """Allows access to drivers or admins."""
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.role in (UserRole.DRIVER, UserRole.ADMIN) or request.user.is_staff)
        )


class IsCustomerOrAdmin(permissions.BasePermission):
    """Allows access to customers or admins."""
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.role in (UserRole.CUSTOMER, UserRole.ADMIN) or request.user.is_staff)
        )
