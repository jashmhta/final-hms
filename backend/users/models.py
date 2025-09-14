from datetime import timedelta

from django.contrib.auth.models import AbstractUser, Permission
from django.db import models
from django.utils import timezone
from encrypted_model_fields.fields import (
    EncryptedCharField,
    EncryptedEmailField,
)

from django.contrib.auth.models import AbstractUser, Permission
from django.db import models
from django.utils import timezone
from encrypted_model_fields.fields import (
    EncryptedCharField,
    EncryptedEmailField,
)
>>>>>>> transform-refactor


class UserRole(models.TextChoices):
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
    HOSPITAL_ADMIN = "HOSPITAL_ADMIN", "Hospital Admin"
    CHIEF_MEDICAL_OFFICER = "CHIEF_MEDICAL_OFFICER", "Chief Medical Officer"
    DEPARTMENT_HEAD = "DEPARTMENT_HEAD", "Department Head"
    ATTENDING_PHYSICIAN = "ATTENDING_PHYSICIAN", "Attending Physician"
    RESIDENT = "RESIDENT", "Resident"
    INTERN = "INTERN", "Intern"
    NURSE_MANAGER = "NURSE_MANAGER", "Nurse Manager"
    CHARGE_NURSE = "CHARGE_NURSE", "Charge Nurse"
    REGISTERED_NURSE = "REGISTERED_NURSE", "Registered Nurse"
    LICENSED_NURSE = "LICENSED_NURSE", "Licensed Practical Nurse"
    PHARMACIST = "PHARMACIST", "Pharmacist"
    PHARMACY_TECH = "PHARMACY_TECH", "Pharmacy Technician"
    LAB_DIRECTOR = "LAB_DIRECTOR", "Lab Director"
    LAB_SUPERVISOR = "LAB_SUPERVISOR", "Lab Supervisor"
    LAB_TECH = "LAB_TECH", "Lab Technician"
    RADIOLOGY_TECH = "RADIOLOGY_TECH", "Radiology Technician"
    RESPIRATORY_THERAPIST = "RESPIRATORY_THERAPIST", "Respiratory Therapist"
    PHYSICAL_THERAPIST = "PHYSICAL_THERAPIST", "Physical Therapist"
    SOCIAL_WORKER = "SOCIAL_WORKER", "Social Worker"
    CASE_MANAGER = "CASE_MANAGER", "Case Manager"
    BILLING_MANAGER = "BILLING_MANAGER", "Billing Manager"
    BILLING_CLERK = "BILLING_CLERK", "Billing Clerk"
    FINANCE_MANAGER = "FINANCE_MANAGER", "Finance Manager"
    RECEPTIONIST = "RECEPTIONIST", "Receptionist"
    SCHEDULER = "SCHEDULER", "Scheduler"
    MEDICAL_RECORDS = "MEDICAL_RECORDS", "Medical Records"
    IT_ADMIN = "IT_ADMIN", "IT Administrator"
    SECURITY = "SECURITY", "Security"
    MAINTENANCE = "MAINTENANCE", "Maintenance"
    VOLUNTEER = "VOLUNTEER", "Volunteer"


class UserStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"
    SUSPENDED = "SUSPENDED", "Suspended"
    TERMINATED = "TERMINATED", "Terminated"
    ON_LEAVE = "ON_LEAVE", "On Leave"
    PENDING_VERIFICATION = "PENDING_VERIFICATION", "Pending Verification"


class EmploymentType(models.TextChoices):
    FULL_TIME = "FULL_TIME", "Full Time"
    PART_TIME = "PART_TIME", "Part Time"
    CONTRACT = "CONTRACT", "Contract"
    TEMPORARY = "TEMPORARY", "Temporary"
    CONSULTANT = "CONSULTANT", "Consultant"
    VOLUNTEER = "VOLUNTEER", "Volunteer"


class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    hospital = models.ForeignKey(
        "hospitals.Hospital",
        on_delete=models.CASCADE,
        related_name="departments",
    )
    head = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="headed_departments",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subdepartments",
    )
    is_active = models.BooleanField(default=True)
    budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["hospital", "code"]]
        ordering = ["name"]

    def __str__(self):
        return f"{self.hospital.name} - {self.name}"


class User(AbstractUser):
    # Basic Information
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    role = models.CharField(
        max_length=32, choices=UserRole.choices, default=UserRole.RECEPTIONIST
    )
    status = models.CharField(
        max_length=20,
        choices=UserStatus.choices,
        default=UserStatus.PENDING_VERIFICATION,
    )

    # Organization
    hospital = models.ForeignKey(
        "hospitals.Hospital",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    supervisor = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supervised_users",
    )

    # Personal Information
    middle_name = models.CharField(max_length=30, blank=True)
    suffix = models.CharField(max_length=10, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[("M", "Male"), ("F", "Female"), ("O", "Other")],
        blank=True,
    )
    personal_phone = EncryptedCharField(max_length=20, blank=True)
    work_phone = models.CharField(max_length=20, blank=True)
    personal_email = EncryptedEmailField(blank=True)

    # Address Information
    address_line1 = EncryptedCharField(max_length=255, blank=True)
    address_line2 = EncryptedCharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=50, default="US")

    # Employment Information
    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
    )
    hire_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    salary = EncryptedCharField(max_length=50, blank=True)
    hourly_rate = EncryptedCharField(max_length=20, blank=True)

    # Professional Information
    license_number = EncryptedCharField(max_length=50, blank=True)
    license_expiry = models.DateField(null=True, blank=True)
    specialization = models.CharField(max_length=100, blank=True)
    board_certification = models.CharField(max_length=200, blank=True)
    years_experience = models.PositiveIntegerField(null=True, blank=True)

    # Security & Access
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = EncryptedCharField(max_length=200, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)
    must_change_password = models.BooleanField(default=True)

    # Compliance & Training
    background_check_date = models.DateField(null=True, blank=True)
    drug_test_date = models.DateField(null=True, blank=True)
    hipaa_training_date = models.DateField(null=True, blank=True)
    orientation_completed = models.BooleanField(default=False)

    # System Information
    created_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_users",
    )
    last_activity = models.DateTimeField(null=True, blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    bio = models.TextField(blank=True)
    preferences = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["hospital", "department", "status"]),
            models.Index(fields=["role", "status"]),
            models.Index(fields=["employee_id"]),
            models.Index(fields=["last_activity"]),
        ]
        permissions = [
            ("can_manage_users", "Can manage users"),
            ("can_view_all_patients", "Can view all patients"),
            ("can_manage_departments", "Can manage departments"),
            ("can_access_reports", "Can access reports"),
            ("can_manage_billing", "Can manage billing"),
            ("can_prescribe_medication", "Can prescribe medication"),
            ("can_order_labs", "Can order lab tests"),
            ("can_discharge_patients", "Can discharge patients"),
            ("can_access_admin_panel", "Can access admin panel"),
        ]

    def __str__(self) -> str:
        return f"{self.get_full_name()} ({self.employee_id or self.username})"

    def get_full_name(self):
        parts = [
            self.first_name,
            self.middle_name,
            self.last_name,
            self.suffix,
        ]
        return " ".join(part for part in parts if part)

    def is_account_locked(self):
        return self.account_locked_until and self.account_locked_until > timezone.now()

    def lock_account(self, duration_minutes=30):
        self.account_locked_until = timezone.now() + timedelta(minutes=duration_minutes)
        self.save(update_fields=["account_locked_until"])

    def unlock_account(self):
        self.account_locked_until = None
        self.failed_login_attempts = 0
        self.save(update_fields=["account_locked_until", "failed_login_attempts"])

    def can_prescribe(self):
        prescribing_roles = [
            UserRole.CHIEF_MEDICAL_OFFICER,
            UserRole.ATTENDING_PHYSICIAN,
            UserRole.RESIDENT,
            UserRole.INTERN,
        ]
        return self.role in prescribing_roles or self.has_perm(
            "users.can_prescribe_medication"
        )


class UserPermissionGroup(models.Model):
    """Custom permission groups for role-based access control"""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    hospital = models.ForeignKey(
        "hospitals.Hospital",
        on_delete=models.CASCADE,
        related_name="permission_groups",
    )
    permissions = models.ManyToManyField(Permission, blank=True)
    users = models.ManyToManyField(
        User, blank=True, related_name="custom_permission_groups"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["hospital", "name"]]
        ordering = ["name"]

    def __str__(self):
        return f"{self.hospital.name} - {self.name}"


class UserSession(models.Model):
    """Track user sessions for security monitoring"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    location = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-login_time"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["session_key"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.login_time}"


class UserLoginHistory(models.Model):
    """Track login attempts for security auditing"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="login_history",
        null=True,
        blank=True,
    )
    username_attempted = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    success = models.BooleanField()
    failure_reason = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["ip_address", "timestamp"]),
            models.Index(fields=["success", "timestamp"]),
        ]

    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.username_attempted} - {status} - {self.timestamp}"


class UserCredential(models.Model):
    """Store professional credentials and certifications"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="credentials")
    credential_type = models.CharField(
        max_length=100
    )  # e.g., 'Medical License', 'Board Certification'
    credential_name = models.CharField(max_length=200)
    issuing_organization = models.CharField(max_length=200)
    credential_number = EncryptedCharField(max_length=100, blank=True)
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending"),
            ("VERIFIED", "Verified"),
            ("EXPIRED", "Expired"),
            ("REVOKED", "Revoked"),
        ],
        default="PENDING",
    )
    document = models.FileField(upload_to="credentials/", null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-issue_date"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["expiry_date"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.credential_name}"
