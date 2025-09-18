from rest_framework.permissions import BasePermission
class RolePermission(BasePermission):
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