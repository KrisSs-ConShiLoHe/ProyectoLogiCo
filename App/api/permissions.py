from rest_framework import permissions


def _has_role(user, roles):
    return hasattr(user, 'rol') and user.rol in roles


class IsAdminOrSupervisorForWrite(permissions.BasePermission):
    """Allow read to authenticated users; write only to ADMINISTRADOR or SUPERVISOR."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated and _has_role(request.user, ['ADMINISTRADOR', 'SUPERVISOR'])


class IsSupervisorForCreate(permissions.BasePermission):
    """Allow create only to SUPERVISOR (admins can still read)."""

    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user and request.user.is_authenticated and _has_role(request.user, ['SUPERVISOR'])
        return request.user and request.user.is_authenticated


class IsMotoristaOrSupervisorOrAdminForState(permissions.BasePermission):
    """Custom permission for changing despacho state: motorista, supervisor, admin, gerente."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        # for state-change endpoints, expect authenticated
        return request.user and request.user.is_authenticated and _has_role(request.user, ['MOTORISTA', 'SUPERVISOR', 'ADMINISTRADOR', 'GERENTE'])
