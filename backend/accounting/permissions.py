from rest_framework import permissions
from users.models import UserRole
class AccountingModulePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        user_role = request.user.role
        action = view.action or "list"
        view_name = getattr(view, "basename", "") or view.__class__.__name__.lower()
        if user_role == UserRole.SUPER_ADMIN:
            return True
        if user_role == UserRole.HOSPITAL_ADMIN:
            return True
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
                "department_restricted": True,
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
        user_perms = role_permissions.get(user_role)
        if not user_perms:
            return False
        if view_name not in user_perms.get("allowed_views", []):
            return False
        if action not in user_perms.get("allowed_actions", []):
            return False
        if action in user_perms.get("restricted_actions", []):
            return False
        return True
    def has_object_permission(self, request, view, obj):
        user_role = request.user.role
        if user_role in [UserRole.SUPER_ADMIN, UserRole.HOSPITAL_ADMIN]:
            return obj.hospital == request.user.hospital
        role_permissions = {
            UserRole.DOCTOR: True,
            UserRole.NURSE: True,
            UserRole.PHARMACIST: True,
            UserRole.LAB_TECH: True,
        }
        if user_role in role_permissions:
            if obj.hospital != request.user.hospital:
                return False
            if hasattr(obj, "cost_center"):
                user_department = getattr(request.user, "department", None)
                return obj.cost_center.code == user_department
            return True
        return obj.hospital == request.user.hospital
class FinancialReportPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        user_role = request.user.role
        if user_role in [UserRole.SUPER_ADMIN, UserRole.HOSPITAL_ADMIN]:
            return True
        if user_role == UserRole.DOCTOR:
            return request.method == "GET"
        if user_role == UserRole.BILLING_CLERK:
            return request.method == "GET"
        return False
class ExpenseApprovalPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        user_role = request.user.role
        if user_role in [UserRole.SUPER_ADMIN, UserRole.HOSPITAL_ADMIN]:
            return True
        if user_role == UserRole.DOCTOR and view.action == "approve":
            return True
        return False
class PayrollProcessingPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        user_role = request.user.role
        if user_role in [UserRole.SUPER_ADMIN, UserRole.HOSPITAL_ADMIN]:
            return True
        if (
            hasattr(request.user, "has_hr_permissions")
            and request.user.has_hr_permissions
        ):
            return True
        if view.action in ["list", "retrieve"]:
            return True
        return False
class BookLockingPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        user_role = request.user.role
        if user_role in [UserRole.SUPER_ADMIN, UserRole.HOSPITAL_ADMIN]:
            return True
        if request.method == "GET":
            return True
        return False
class TaxCompliancePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        user_role = request.user.role
        if user_role in [UserRole.SUPER_ADMIN, UserRole.HOSPITAL_ADMIN]:
            return True
        if (
            hasattr(request.user, "has_tax_permissions")
            and request.user.has_tax_permissions
        ):
            return True
        return False
class BankReconciliationPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        user_role = request.user.role
        if user_role in [UserRole.SUPER_ADMIN, UserRole.HOSPITAL_ADMIN]:
            return True
        if (
            hasattr(request.user, "has_finance_permissions")
            and request.user.has_finance_permissions
        ):
            return True
        if request.method == "GET":
            return user_role in [UserRole.BILLING_CLERK]
        return False
class AuditLogPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        user_role = request.user.role
        if user_role in [UserRole.SUPER_ADMIN, UserRole.HOSPITAL_ADMIN]:
            return True
        if request.method == "GET" and hasattr(request.user, "has_audit_access"):
            return request.user.has_audit_access
        return False
class AdvancedReportingPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in [
            UserRole.SUPER_ADMIN,
            UserRole.HOSPITAL_ADMIN,
        ]
class ComplianceManagementPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in [
            UserRole.SUPER_ADMIN,
            UserRole.HOSPITAL_ADMIN,
        ]
class AssetManagementPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        user_role = request.user.role
        if user_role in [UserRole.SUPER_ADMIN, UserRole.HOSPITAL_ADMIN]:
            return True
        if user_role == UserRole.DOCTOR and request.method == "GET":
            return True
        return False