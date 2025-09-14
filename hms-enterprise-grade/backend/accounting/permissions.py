"""
Custom permissions for accounting module with role-based access control.
"""

from rest_framework import permissions
from users.models import UserRole


class AccountingModulePermission(permissions.BasePermission):
    """
    Base permission class for accounting module.
    Defines role-based access for different accounting features.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        user_role = request.user.role
        action = view.action or "list"
        view_name = getattr(view, "basename", "") or view.__class__.__name__.lower()

        # Super Admin has full access to everything
        if user_role == UserRole.SUPER_ADMIN:
            return True

        # Hospital Admin has full access to their hospital's accounting
        if user_role == UserRole.HOSPITAL_ADMIN:
            return True

        # Define permissions for each role
        role_permissions = {
            UserRole.BILLING_CLERK: {
                "allowed_views": [
                    "currency",
                    "customer",
                    "invoice",
                    "payment",
                    "insurance-claim",
                ],
                "allowed_actions": ["list", "retrieve", "create", "update"],
                "restricted_actions": ["delete"],
            },
            UserRole.DOCTOR: {
                "allowed_views": [
                    "dashboard",
                    "reports",
                    "cost-center",
                    "invoice",
                    "expense",
                ],
                "allowed_actions": ["list", "retrieve"],
                "department_restricted": True,  # Can only view their department data
            },
            UserRole.NURSE: {
                "allowed_views": ["dashboard"],
                "allowed_actions": ["list", "retrieve"],
                "department_restricted": True,
            },
            UserRole.PHARMACIST: {
                "allowed_views": ["dashboard", "invoice", "expense", "vendor"],
                "allowed_actions": ["list", "retrieve", "create"],
                "department_restricted": True,
            },
            UserRole.RECEPTIONIST: {
                "allowed_views": ["invoice", "payment", "customer"],
                "allowed_actions": ["list", "retrieve", "create"],
            },
            UserRole.LAB_TECH: {
                "allowed_views": ["dashboard", "expense"],
                "allowed_actions": ["list", "retrieve"],
                "department_restricted": True,
            },
        }

        # Get permissions for user role
        user_perms = role_permissions.get(user_role)
        if not user_perms:
            return False

        # Check if view is allowed
        if view_name not in user_perms.get("allowed_views", []):
            return False

        # Check if action is allowed
        if action not in user_perms.get("allowed_actions", []):
            return False

        # Check restricted actions
        if action in user_perms.get("restricted_actions", []):
            return False

        return True

    def has_object_permission(self, request, view, obj):
        """Object-level permissions"""
        user_role = request.user.role

        # Super Admin and Hospital Admin have access to all objects in their hospital
        if user_role in [UserRole.SUPER_ADMIN, UserRole.HOSPITAL_ADMIN]:
            return obj.hospital == request.user.hospital

        # Department restricted roles can only access their department data
        role_permissions = {
            UserRole.DOCTOR: True,
            UserRole.NURSE: True,
            UserRole.PHARMACIST: True,
            UserRole.LAB_TECH: True,
        }

        if user_role in role_permissions:
            # Check if object belongs to user's hospital
            if obj.hospital != request.user.hospital:
                return False

            # Check department access if applicable
            if hasattr(obj, "cost_center"):
                # User should only access their department's data
                user_department = getattr(request.user, "department", None)
                return obj.cost_center.code == user_department

            return True

        # Other roles have basic hospital-level access
        return obj.hospital == request.user.hospital


class FinancialReportPermission(permissions.BasePermission):
    """Permission for financial reports"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        user_role = request.user.role

        # All management roles can view reports
        if user_role in [UserRole.SUPER_ADMIN, UserRole.HOSPITAL_ADMIN]:
            return True

        # Doctors can view department-specific reports
        if user_role == UserRole.DOCTOR:
            return request.method == "GET"

        # Billing clerks can view billing reports
        if user_role == UserRole.BILLING_CLERK:
            return request.method == "GET"

        return False


class ExpenseApprovalPermission(permissions.BasePermission):
    """Permission for expense approval"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Only Hospital Admin can approve expenses above certain limits
        user_role = request.user.role

        if user_role in [UserRole.SUPER_ADMIN, UserRole.HOSPITAL_ADMIN]:
            return True

        # Department heads can approve expenses for their department up to a limit
        if user_role == UserRole.DOCTOR and view.action == "approve":
            # Add logic for approval limits based on user hierarchy
            return True

        return False


class PayrollProcessingPermission(permissions.BasePermission):
    """Permission for payroll processing"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        user_role = request.user.role

        # Only Hospital Admin and designated HR staff can process payroll
        if user_role in [UserRole.SUPER_ADMIN, UserRole.HOSPITAL_ADMIN]:
            return True

        # Check if user has HR permissions (would need to be added to user model)
        if (
            hasattr(request.user, "has_hr_permissions")
            and request.user.has_hr_permissions
        ):
            return True

        # Others can only view their own payroll
        if view.action in ["list", "retrieve"]:
            return True

        return False


class BookLockingPermission(permissions.BasePermission):
    """Permission for book locking operations"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        user_role = request.user.role

        # Only Hospital Admin can lock/unlock books
        if user_role in [UserRole.SUPER_ADMIN, UserRole.HOSPITAL_ADMIN]:
            return True

        # Others can only view lock status
        if request.method == "GET":
            return True

        return False


class TaxCompliancePermission(permissions.BasePermission):
    """Permission for tax compliance features"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        user_role = request.user.role

        # Hospital Admin and designated tax officers can manage tax compliance
        if user_role in [UserRole.SUPER_ADMIN, UserRole.HOSPITAL_ADMIN]:
            return True

        # Check if user has tax compliance permissions
        if (
            hasattr(request.user, "has_tax_permissions")
            and request.user.has_tax_permissions
        ):
            return True

        return False


class BankReconciliationPermission(permissions.BasePermission):
    """Permission for bank reconciliation"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        user_role = request.user.role

        # Hospital Admin and designated finance staff can perform reconciliation
        if user_role in [UserRole.SUPER_ADMIN, UserRole.HOSPITAL_ADMIN]:
            return True

        # Check if user has finance permissions
        if (
            hasattr(request.user, "has_finance_permissions")
            and request.user.has_finance_permissions
        ):
            return True

        # Others can only view reconciliation status
        if request.method == "GET":
            return user_role in [UserRole.BILLING_CLERK]

        return False


class AuditLogPermission(permissions.BasePermission):
    """Permission for audit log access"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        user_role = request.user.role

        # Only Hospital Admin and above can access audit logs
        if user_role in [UserRole.SUPER_ADMIN, UserRole.HOSPITAL_ADMIN]:
            return True

        # Audit logs are read-only for authorized users
        if request.method == "GET" and hasattr(request.user, "has_audit_access"):
            return request.user.has_audit_access

        return False


# Permission classes for specific operations


class AdvancedReportingPermission(permissions.BasePermission):
    """Permission for advanced reporting features"""

    def has_permission(self, request, view):
        # Advanced reports require management level access
        return request.user.role in [UserRole.SUPER_ADMIN, UserRole.HOSPITAL_ADMIN]


class ComplianceManagementPermission(permissions.BasePermission):
    """Permission for compliance management"""

    def has_permission(self, request, view):
        # Compliance management requires admin level access
        return request.user.role in [UserRole.SUPER_ADMIN, UserRole.HOSPITAL_ADMIN]


class AssetManagementPermission(permissions.BasePermission):
    """Permission for asset management"""

    def has_permission(self, request, view):
        user_role = request.user.role

        # Admin and designated asset managers can manage assets
        if user_role in [UserRole.SUPER_ADMIN, UserRole.HOSPITAL_ADMIN]:
            return True

        # Department heads can view their department assets
        if user_role == UserRole.DOCTOR and request.method == "GET":
            return True

        return False
