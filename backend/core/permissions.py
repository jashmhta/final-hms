from rest_framework.permissions import BasePermission


class RolePermission(BasePermission):
    """Require a user role in view.allowed_roles. SUPER_ADMIN/superuser always allowed."""

    def has_permission(self, request, view):
        roles = getattr(view, "allowed_roles", None)
        if roles is None:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if (
            getattr(user, "is_superuser", False)
            or getattr(user, "role", None) == "SUPER_ADMIN"
        ):
            return True
        return getattr(user, "role", None) in roles


class ModuleEnabledPermission(BasePermission):
    """Ensure the module is enabled for the user's hospital subscription.
    Set view.required_module to one of: enable_opd, enable_ipd, enable_diagnostics, enable_pharmacy, enable_accounting.
    SUPER_ADMIN bypasses.
    """

    def has_permission(self, request, view):
        module_flag = getattr(view, "required_module", None)
        if not module_flag:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if (
            getattr(user, "is_superuser", False)
            or getattr(user, "role", None) == "SUPER_ADMIN"
        ):
            return True
        hospital = getattr(user, "hospital", None)
        if not hospital:
            return False
        subscription = getattr(hospital, "subscription", None)
        if not subscription:
            return False
        return subscription.is_enabled(module_flag)
