from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from hospitals.models import HospitalPlan
from .models import (
    Department,
    User,
    UserCredential,
    UserLoginHistory,
    UserPermissionGroup,
    UserSession,
)
class DepartmentSerializer(serializers.ModelSerializer):
    head_name = serializers.SerializerMethodField()
    user_count = serializers.SerializerMethodField()
    subdepartments_count = serializers.SerializerMethodField()
    class Meta:
        model = Department
        fields = [
            "id",
            "name",
            "code",
            "description",
            "head",
            "head_name",
            "parent",
            "is_active",
            "budget",
            "location",
            "phone",
            "email",
            "user_count",
            "subdepartments_count",
            "created_at",
            "updated_at",
        ]
    def get_head_name(self, obj):
        return obj.head.get_full_name() if obj.head else None
    def get_user_count(self, obj):
        return obj.users.filter(status="ACTIVE").count()
    def get_subdepartments_count(self, obj):
        return obj.subdepartments.filter(is_active=True).count()
class UserCredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCredential
        fields = [
            "id",
            "credential_type",
            "credential_name",
            "issuing_organization",
            "credential_number",
            "issue_date",
            "expiry_date",
            "is_active",
            "verification_status",
            "document",
            "notes",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"credential_number": {"write_only": True}}
class UserSessionSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()
    class Meta:
        model = UserSession
        fields = [
            "id",
            "session_key",
            "ip_address",
            "user_agent",
            "location",
            "is_active",
            "login_time",
            "logout_time",
            "last_activity",
            "duration",
        ]
        read_only_fields = ["session_key"]
    def get_duration(self, obj):
        if obj.logout_time:
            return (obj.logout_time - obj.login_time).total_seconds()
        return (obj.last_activity - obj.login_time).total_seconds()
class UserLoginHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLoginHistory
        fields = [
            "id",
            "username_attempted",
            "ip_address",
            "user_agent",
            "success",
            "failure_reason",
            "timestamp",
            "location",
        ]
class UserListSerializer(serializers.ModelSerializer):
    department_name = serializers.SerializerMethodField()
    supervisor_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    credentials_count = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "employee_id",
            "full_name",
            "first_name",
            "last_name",
            "email",
            "role",
            "status",
            "department",
            "department_name",
            "supervisor_name",
            "hire_date",
            "employment_type",
            "last_login",
            "credentials_count",
            "is_active",
            "date_joined",
        ]
    def get_department_name(self, obj):
        return obj.department.name if obj.department else None
    def get_supervisor_name(self, obj):
        return obj.supervisor.get_full_name() if obj.supervisor else None
    def get_full_name(self, obj):
        return obj.get_full_name()
    def get_credentials_count(self, obj):
        return obj.credentials.filter(is_active=True).count()
class UserSerializer(serializers.ModelSerializer):
    department_name = serializers.SerializerMethodField()
    supervisor_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    credentials = UserCredentialSerializer(many=True, read_only=True)
    recent_sessions = UserSessionSerializer(
        many=True, read_only=True, source="sessions"
    )
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "employee_id",
            "full_name",
            "first_name",
            "middle_name",
            "last_name",
            "suffix",
            "email",
            "role",
            "status",
            "department",
            "department_name",
            "supervisor",
            "supervisor_name",
            "date_of_birth",
            "gender",
            "work_phone",
            "employment_type",
            "hire_date",
            "termination_date",
            "license_expiry",
            "specialization",
            "board_certification",
            "years_experience",
            "mfa_enabled",
            "background_check_date",
            "drug_test_date",
            "hipaa_training_date",
            "orientation_completed",
            "last_activity",
            "avatar",
            "bio",
            "preferences",
            "credentials",
            "recent_sessions",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
        ]
    def get_department_name(self, obj):
        return obj.department.name if obj.department else None
    def get_supervisor_name(self, obj):
        return obj.supervisor.get_full_name() if obj.supervisor else None
    def get_full_name(self, obj):
        return obj.get_full_name()
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if "recent_sessions" in data:
            data["recent_sessions"] = data["recent_sessions"][:10]
        return data
class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "password_confirm",
            "employee_id",
            "first_name",
            "middle_name",
            "last_name",
            "suffix",
            "email",
            "role",
            "hospital",
            "department",
            "supervisor",
            "date_of_birth",
            "gender",
            "personal_phone",
            "work_phone",
            "personal_email",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "zip_code",
            "country",
            "employment_type",
            "hire_date",
            "salary",
            "hourly_rate",
            "license_number",
            "license_expiry",
            "specialization",
            "board_certification",
            "years_experience",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
            "personal_phone": {"write_only": True},
            "personal_email": {"write_only": True},
            "address_line1": {"write_only": True},
            "address_line2": {"write_only": True},
            "salary": {"write_only": True},
            "hourly_rate": {"write_only": True},
            "license_number": {"write_only": True},
        }
    def validate(self, data):
        if data.get("password") != data.get("password_confirm"):
            raise serializers.ValidationError("Passwords do not match")
        return data
    def create(self, validated_data):
        validated_data.pop("password_confirm", None)
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "employee_id",
            "first_name",
            "middle_name",
            "last_name",
            "suffix",
            "email",
            "role",
            "status",
            "department",
            "supervisor",
            "date_of_birth",
            "gender",
            "personal_phone",
            "work_phone",
            "personal_email",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "zip_code",
            "country",
            "employment_type",
            "hire_date",
            "termination_date",
            "salary",
            "hourly_rate",
            "license_number",
            "license_expiry",
            "specialization",
            "board_certification",
            "years_experience",
            "background_check_date",
            "drug_test_date",
            "hipaa_training_date",
            "orientation_completed",
            "avatar",
            "bio",
            "preferences",
        ]
        extra_kwargs = {
            "personal_phone": {"write_only": True},
            "personal_email": {"write_only": True},
            "address_line1": {"write_only": True},
            "address_line2": {"write_only": True},
            "salary": {"write_only": True},
            "hourly_rate": {"write_only": True},
            "license_number": {"write_only": True},
        }
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    def validate(self, data):
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError("New passwords do not match")
        return data
    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value
class UserPermissionGroupSerializer(serializers.ModelSerializer):
    permissions_count = serializers.SerializerMethodField()
    users_count = serializers.SerializerMethodField()
    class Meta:
        model = UserPermissionGroup
        fields = [
            "id",
            "name",
            "description",
            "permissions",
            "users",
            "permissions_count",
            "users_count",
            "is_active",
            "created_at",
            "updated_at",
        ]
    def get_permissions_count(self, obj):
        return obj.permissions.count()
    def get_users_count(self, obj):
        return obj.users.count()
class UserStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    inactive_users = serializers.IntegerField()
    pending_verification = serializers.IntegerField()
    suspended_users = serializers.IntegerField()
    by_role = serializers.DictField()
    by_department = serializers.DictField()
    recent_logins = serializers.IntegerField()
    failed_logins_today = serializers.IntegerField()
    credentials_expiring_soon = serializers.IntegerField()
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = getattr(user, "role", None)
        token["hospital"] = getattr(user, "hospital_id", None)
        token["employee_id"] = getattr(user, "employee_id", None)
        token["department"] = getattr(user, "department_id", None)
        token["full_name"] = user.get_full_name()
        token["status"] = getattr(user, "status", None)
        token["can_prescribe"] = user.can_prescribe()
        flags = [
            "enable_opd",
            "enable_ipd",
            "enable_diagnostics",
            "enable_pharmacy",
            "enable_accounting",
        ]
        hp = None
        try:
            if getattr(user, "hospital_id", None):
                hospital = getattr(user, "hospital", None)
                hp = getattr(hospital, "subscription", None)
                if hp is None:
                    hp = (
                        HospitalPlan.objects.select_related("plan")
                        .filter(hospital_id=user.hospital_id)
                        .first()
                    )
        except Exception:
            hp = None
        for f in flags:
            try:
                token[f] = bool(hp.is_enabled(f)) if hp else True
            except Exception:
                token[f] = True
        return token