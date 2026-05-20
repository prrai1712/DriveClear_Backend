from rest_framework.permissions import BasePermission

from common.constants.enums import UserRole


class IsAuthenticatedUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class HasRole(BasePermission):
    allowed_roles: tuple[str, ...] = ()

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in self.allowed_roles


class IsAdmin(HasRole):
    allowed_roles = (UserRole.ADMIN,)


class IsOperations(HasRole):
    allowed_roles = (UserRole.ADMIN, UserRole.OPERATIONS)


class IsSupport(HasRole):
    allowed_roles = (UserRole.ADMIN, UserRole.SUPPORT, UserRole.OPERATIONS)
