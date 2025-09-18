import uuid
from decimal import Decimal
from core.models import TimeStampedModel
from django.contrib.auth import get_user_model
from django.db import models
from encrypted_model_fields.fields import EncryptedTextField
User = get_user_model()
class SubscriptionTier(models.Model):
    TIER_CHOICES = [
        ("BASIC", "Basic"),
        ("PREMIUM", "Premium"),
        ("ENTERPRISE", "Enterprise"),
        ("CUSTOM", "Custom"),
    ]
    name = models.CharField(max_length=50, unique=True)
    tier_type = models.CharField(max_length=20, choices=TIER_CHOICES)
    description = models.TextField()
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2)
    max_users = models.PositiveIntegerField()
    max_beds = models.PositiveIntegerField()
    storage_gb = models.PositiveIntegerField()
    api_calls_per_month = models.PositiveIntegerField()
    support_level = models.CharField(max_length=20, default="EMAIL")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["price_monthly"]
    def __str__(self):
        return f"{self.name} - ${self.price_monthly}/month"
class ModulePermission(models.Model):
    MODULE_CHOICES = [
        ("PATIENT_REGISTRATION", "Patient Registration"),
        ("OPD_MANAGEMENT", "OPD Management"),
        ("IPD_MANAGEMENT", "IPD Management"),
        ("EMERGENCY_DEPARTMENT", "Emergency Department"),
        ("OPERATION_THEATRE", "Operation Theatre"),
        ("PHARMACY_MANAGEMENT", "Pharmacy Management"),
        ("LABORATORY_MANAGEMENT", "Laboratory Management"),
        ("RADIOLOGY_MANAGEMENT", "Radiology Management"),
        ("BLOOD_BANK", "Blood Bank Management"),
        ("BILLING_INVOICING", "Billing & Invoicing"),
        ("INSURANCE_TPA", "Insurance & TPA"),
        ("HR_PAYROLL", "HR & Payroll"),
        ("HOUSEKEEPING", "Housekeeping & Maintenance"),
        ("BIOMEDICAL_EQUIPMENT", "Biomedical Equipment"),
        ("DIETARY_MANAGEMENT", "Dietary Management"),
        ("AMBULANCE_MANAGEMENT", "Ambulance Management"),
        ("PATIENT_PORTAL", "Patient Portal"),
        ("DOCTOR_PORTAL", "Doctor Portal"),
        ("E_PRESCRIPTION", "E-Prescription"),
        ("NOTIFICATIONS", "Notification System"),
        ("FEEDBACK_MANAGEMENT", "Feedback & Complaints"),
        ("MARKETING_CRM", "Marketing CRM"),
        ("ANALYTICS_REPORTING", "Analytics & Reporting"),
        ("MRD_MANAGEMENT", "Medical Records Department"),
        ("COMPLIANCE_CHECKLISTS", "NABH/JCI Compliance"),
        ("BACKUP_RECOVERY", "Backup & Disaster Recovery"),
        ("CYBERSECURITY", "Cybersecurity Enhancements"),
        ("ACCOUNTING_ADVANCED", "Advanced Accounting"),
    ]
    module_name = models.CharField(max_length=30, choices=MODULE_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField()
    is_core_module = models.BooleanField(default=False)
    min_tier_required = models.CharField(
        max_length=20, choices=SubscriptionTier.TIER_CHOICES, default="BASIC"
    )
    def __str__(self):
        return self.display_name
class TierModuleAccess(models.Model):
    tier = models.ForeignKey(
        SubscriptionTier, on_delete=models.CASCADE, related_name="module_access"
    )
    module = models.ForeignKey(ModulePermission, on_delete=models.CASCADE)
    is_enabled = models.BooleanField(default=True)
    feature_limits = models.JSONField(default=dict, blank=True)
    class Meta:
        unique_together = ["tier", "module"]
    def __str__(self):
        return f"{self.tier.name} - {self.module.display_name}"
class HospitalSubscription(TimeStampedModel):
    BILLING_CYCLE_CHOICES = [
        ("MONTHLY", "Monthly"),
        ("YEARLY", "Yearly"),
    ]
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("SUSPENDED", "Suspended"),
        ("CANCELLED", "Cancelled"),
        ("TRIAL", "Trial"),
        ("EXPIRED", "Expired"),
    ]
    hospital = models.OneToOneField(
        "hospitals.Hospital", on_delete=models.CASCADE, related_name="superadmin_subscription"
    )
    tier = models.ForeignKey(SubscriptionTier, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="TRIAL")
    billing_cycle = models.CharField(
        max_length=10, choices=BILLING_CYCLE_CHOICES, default="MONTHLY"
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    trial_end_date = models.DateTimeField(null=True, blank=True)
    current_users = models.PositiveIntegerField(default=0)
    current_beds = models.PositiveIntegerField(default=0)
    storage_used_gb = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    api_calls_this_month = models.PositiveIntegerField(default=0)
    monthly_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    last_payment_date = models.DateTimeField(null=True, blank=True)
    next_billing_date = models.DateTimeField()
    billing_contact_name = models.CharField(max_length=200)
    billing_contact_email = models.EmailField()
    billing_contact_phone = models.CharField(max_length=20)
    billing_address = EncryptedTextField()
    auto_renewal = models.BooleanField(default=True)
    payment_method = models.CharField(max_length=50, blank=True)
    def __str__(self):
        return f"{self.hospital.name} - {self.tier.name} ({self.status})"
    @property
    def is_trial(self):
        return self.status == "TRIAL"
    @property
    def is_active(self):
        return self.status == "ACTIVE"
    @property
    def days_remaining(self):
        from django.utils import timezone
        if self.end_date:
            delta = self.end_date - timezone.now()
            return max(0, delta.days)
        return 0
    def can_access_module(self, module_name):
        if not self.is_active and not self.is_trial:
            return False
        try:
            module = ModulePermission.objects.get(module_name=module_name)
            access = TierModuleAccess.objects.get(tier=self.tier, module=module)
            return access.is_enabled
        except (ModulePermission.DoesNotExist, TierModuleAccess.DoesNotExist):
            return False
class SuperadminUser(TimeStampedModel):
    ROLE_CHOICES = [
        ("SUPER_ADMIN", "Super Administrator"),
        ("ADMIN", "Administrator"),
        ("SUPPORT", "Support Manager"),
        ("BILLING", "Billing Manager"),
        ("TECHNICAL", "Technical Manager"),
    ]
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="superadmin_profile"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    can_manage_subscriptions = models.BooleanField(default=False)
    can_manage_users = models.BooleanField(default=False)
    can_view_analytics = models.BooleanField(default=True)
    can_access_support = models.BooleanField(default=True)
    can_manage_billing = models.BooleanField(default=False)
    accessible_hospitals = models.ManyToManyField("hospitals.Hospital", blank=True)
    ip_whitelist = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.role})"
class GlobalSettings(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_encrypted = models.BooleanField(default=False)
    category = models.CharField(max_length=50, default="GENERAL")
    last_modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    modified_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["category", "key"]
    def __str__(self):
        return f"{self.key}: {self.value[:50]}..."
class SystemAlert(TimeStampedModel):
    ALERT_TYPES = [
        ("INFO", "Information"),
        ("WARNING", "Warning"),
        ("ERROR", "Error"),
        ("MAINTENANCE", "Maintenance"),
        ("SECURITY", "Security"),
    ]
    SEVERITY_CHOICES = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
        ("CRITICAL", "Critical"),
    ]
    title = models.CharField(max_length=200)
    message = models.TextField()
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    target_all_hospitals = models.BooleanField(default=True)
    target_hospitals = models.ManyToManyField("hospitals.Hospital", blank=True)
    target_tiers = models.ManyToManyField(SubscriptionTier, blank=True)
    is_active = models.BooleanField(default=True)
    show_from = models.DateTimeField()
    show_until = models.DateTimeField(null=True, blank=True)
    show_on_dashboard = models.BooleanField(default=True)
    send_email = models.BooleanField(default=False)
    send_sms = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    class Meta:
        ordering = ["-created_at"]
    def __str__(self):
        return f"{self.title} ({self.alert_type})"
class UsageMetrics(TimeStampedModel):
    hospital = models.ForeignKey("hospitals.Hospital", on_delete=models.CASCADE)
    date = models.DateField()
    active_users = models.PositiveIntegerField(default=0)
    logins_count = models.PositiveIntegerField(default=0)
    api_calls = models.PositiveIntegerField(default=0)
    patients_created = models.PositiveIntegerField(default=0)
    appointments_booked = models.PositiveIntegerField(default=0)
    bills_generated = models.PositiveIntegerField(default=0)
    prescriptions_created = models.PositiveIntegerField(default=0)
    storage_used_mb = models.PositiveIntegerField(default=0)
    bandwidth_used_mb = models.PositiveIntegerField(default=0)
    avg_response_time_ms = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    class Meta:
        unique_together = ["hospital", "date"]
        ordering = ["-date"]
    def __str__(self):
        return f"{self.hospital.name} - {self.date}"