"""
HIPAA Compliance Module
Technical, Administrative, and Physical Safeguards implementation
"""

import hashlib
import json
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Union
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import TenantModel
from core.security_compliance import SecurityComplianceFramework

User = get_user_model()
logger = logging.getLogger(__name__)


class HIPAASafeguardType(Enum):
    """HIPAA Security Rule safeguard categories"""
    TECHNICAL = "technical"
    ADMINISTRATIVE = "administrative"
    PHYSICAL = "physical"


class HIPAASpecification(Enum):
    """HIPAA Security Rule implementation specifications"""
    ACCESS_CONTROL = "access_control"
    AUDIT_CONTROLS = "audit_controls"
    INTEGRITY = "integrity"
    AUTHENTICATION = "authentication"
    TRANSMISSION_SECURITY = "transmission_security"
    SECURITY_MANAGEMENT = "security_management"
    WORKFORCE_SECURITY = "workforce_security"
    INFORMATION_ACCESS = "information_access"
    TRAINING = "training"
    FACILITY_ACCESS = "facility_access"
    WORKSTATION_SECURITY = "workstation_security"
    DEVICE_SECURITY = "device_security"


class HIPAARiskLevel(Enum):
    """Risk levels for HIPAA compliance"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class HIPAAComplianceStatus(Enum):
    """Compliance status indicators"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    ASSESSMENT_NEEDED = "assessment_needed"


class HIPAASafeguard(models.Model):
    """
    HIPAA Security Rule safeguard implementation tracking
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Basic information
    name = models.CharField(max_length=200)
    description = models.TextField()
    safeguard_type = models.CharField(
        max_length=20,
        choices=[(t.value, t.name.replace('_', ' ').title()) for t in HIPAASafeguardType]
    )
    specification = models.CharField(
        max_length=30,
        choices=[(s.value, s.name.replace('_', ' ').title()) for s in HIPAASpecification]
    )

    # Implementation details
    implementation_status = models.CharField(
        max_length=20,
        choices=[
            ('IMPLEMENTED', 'Implemented'),
            ('PARTIALLY_IMPLEMENTED', 'Partially Implemented'),
            ('NOT_IMPLEMENTED', 'Not Implemented'),
            ('NOT_APPLICABLE', 'Not Applicable'),
        ],
        default='NOT_IMPLEMENTED'
    )
    implementation_date = models.DateField(null=True, blank=True)
    last_review_date = models.DateField(null=True, blank=True)
    next_review_date = models.DateField(null=True, blank=True)

    # Documentation
    implementation_notes = models.TextField(blank=True)
    policies_procedures = models.TextField(blank=True)
    evidence_locations = models.JSONField(default=dict, blank=True)

    # Compliance
    is_compliant = models.BooleanField(default=False)
    compliance_issues = models.JSONField(default=list, blank=True)
    remediation_plan = models.TextField(blank=True)

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_hipaa_safeguards'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['safeguard_type', 'specification']),
            models.Index(fields=['implementation_status']),
            models.Index(fields=['is_compliant']),
            models.Index(fields=['next_review_date']),
        ]
        ordering = ['safeguard_type', 'specification', 'name']

    def __str__(self):
        return f"{self.get_safeguard_type_display()} - {self.name}"

    def check_compliance(self) -> Tuple[bool, List[str]]:
        """
        Check if safeguard meets HIPAA requirements
        Returns (is_compliant, issues)
        """
        issues = []
        is_compliant = True

        # Check implementation status
        if self.implementation_status not in ['IMPLEMENTED', 'NOT_APPLICABLE']:
            issues.append(f"Safeguard not fully implemented: {self.implementation_status}")
            is_compliant = False

        # Check review schedule
        if self.last_review_date:
            days_since_review = (timezone.now().date() - self.last_review_date).days
            if days_since_review > 365:  # Annual review required
                issues.append("Annual review overdue")
                is_compliant = False

        # Check for existing compliance issues
        if self.compliance_issues:
            issues.extend(self.compliance_issues)
            is_compliant = False

        self.is_compliant = is_compliant and not issues
        self.save()

        return self.is_compliant, issues

    def schedule_next_review(self):
        """Schedule next annual review"""
        self.next_review_date = timezone.now().date() + timedelta(days=365)
        self.save()


class PHIAccessLog(models.Model):
    """
    Comprehensive audit trail for all Protected Health Information access
    HIPAA § 164.312(b) Audit Controls requirement
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # User information
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='phi_access_logs'
    )
    user_role = models.CharField(max_length=50, blank=True)
    user_department = models.CharField(max_length=100, blank=True)

    # Patient information
    patient_id = models.UUIDField()  # Encrypted patient identifier
    patient_name_encrypted = models.CharField(max_length=255, blank=True)

    # Access details
    access_type = models.CharField(
        max_length=20,
        choices=[
            ('VIEW', 'View/Read'),
            ('CREATE', 'Create/Add'),
            ('UPDATE', 'Modify/Update'),
            ('DELETE', 'Delete/Remove'),
            ('EXPORT', 'Export/Download'),
            ('PRINT', 'Print'),
            ('SHARE', 'Share/Disclose'),
        ]
    )
    access_purpose = models.CharField(
        max_length=50,
        choices=[
            ('TREATMENT', 'Treatment'),
            ('PAYMENT', 'Payment'),
            ('HEALTHCARE_OPERATIONS', 'Healthcare Operations'),
            ('PUBLIC_HEALTH', 'Public Health Activities'),
            ('RESEARCH', 'Research'),
            ('LEGAL', 'Legal Proceedings'),
            ('EMERGENCY', 'Emergency Treatment'),
            ('OTHER', 'Other - Requires Justification'),
        ]
    )
    purpose_justification = models.TextField(blank=True)

    # Resource accessed
    resource_type = models.CharField(max_length=50)  # e.g., 'medical_record', 'lab_result'
    resource_id = models.CharField(max_length=255)
    resource_details = models.JSONField(default=dict, blank=True)

    # Access context
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    device_fingerprint = models.CharField(max_length=100, blank=True)
    session_id = models.CharField(max_length=100, blank=True)

    # Location
    location = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')

    # Authorization
    was_authorized = models.BooleanField(default=True)
    authorization_method = models.CharField(max_length=50, blank=True)
    consent_verified = models.BooleanField(default=False)
    consent_id = models.CharField(max_length=100, blank=True)

    # Data classification
    data_sensitivity = models.CharField(
        max_length=20,
        choices=[
            ('LOW', 'Low Sensitivity'),
            ('MODERATE', 'Moderate Sensitivity'),
            ('HIGH', 'High Sensitivity'),
            ('CRITICAL', 'Critical PHI'),
        ],
        default='MODERATE'
    )

    # System information
    application = models.CharField(max_length=100, default='HMS')
    module = models.CharField(max_length=100, blank=True)
    action = models.CharField(max_length=100)

    # Audit metadata
    is_bulk_access = models.BooleanField(default=False)
    record_count = models.PositiveIntegerField(default=1)
    duration_seconds = models.PositiveIntegerField(default=0)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    # Review and investigation
    requires_review = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_phi_access'
    )
    review_date = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    is_suspicious = models.BooleanField(default=False)
    investigation_required = models.BooleanField(default=False)

    # Retention
    retention_until = models.DateTimeField(default=lambda: timezone.now() + timedelta(days=365*7))  # 7 years

    class Meta:
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['patient_id', 'timestamp']),
            models.Index(fields=['access_type', 'timestamp']),
            models.Index(fields=['access_purpose', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['requires_review']),
            models.Index(fields=['is_suspicious']),
            models.Index(fields=['resource_type']),
            models.Index(fields=['was_authorized']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user or 'Anonymous'} accessed {self.resource_type} for {self.patient_id}"

    @classmethod
    def log_access(cls, user: User, patient_id: str, access_type: str, resource_type: str,
                  resource_id: str, **kwargs) -> 'PHIAccessLog':
        """
        Create a PHI access log entry
        This should be called whenever PHI is accessed
        """
        from .utils import encrypt_phi_identifier

        try:
            # Get user details
            user_role = getattr(user, 'role', 'Unknown')
            user_department = getattr(user, 'department', 'Unknown')

            # Create log entry
            log_entry = cls.objects.create(
                user=user,
                user_role=user_role,
                user_department=user_department,
                patient_id=encrypt_phi_identifier(patient_id),
                access_type=access_type,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=kwargs.get('ip_address', '127.0.0.1'),
                user_agent=kwargs.get('user_agent', ''),
                session_id=kwargs.get('session_id', ''),
                location=kwargs.get('location', ''),
                was_authorized=kwargs.get('was_authorized', True),
                success=kwargs.get('success', True),
                record_count=kwargs.get('record_count', 1),
                duration_seconds=kwargs.get('duration_seconds', 0),
                application=kwargs.get('application', 'HMS'),
                module=kwargs.get('module', ''),
                action=kwargs.get('action', ''),
            )

            # Check for suspicious patterns
            cls._check_suspicious_access(log_entry)

            return log_entry

        except Exception as e:
            logger.error(f"Failed to log PHI access: {e}")
            raise

    @classmethod
    def _check_suspicious_access(cls, log_entry: 'PHIAccessLog'):
        """
        Check for suspicious access patterns
        """
        try:
            # Check for unusual access times
            access_hour = log_entry.timestamp.hour
            if not (8 <= access_hour <= 18):  # Outside business hours
                log_entry.requires_review = True
                log_entry.is_suspicious = True

            # Check for bulk access
            if log_entry.record_count > 50:
                log_entry.requires_review = True
                log_entry.is_bulk_access = True

            # Check for unauthorized access
            if not log_entry.was_authorized:
                log_entry.requires_review = True
                log_entry.is_suspicious = True
                log_entry.investigation_required = True

            # Check for access to sensitive data
            if log_entry.data_sensitivity in ['HIGH', 'CRITICAL']:
                log_entry.requires_review = True

            log_entry.save()

            # Trigger alerts if necessary
            if log_entry.investigation_required:
                cls._trigger_security_alert(log_entry)

        except Exception as e:
            logger.error(f"Failed to check suspicious access: {e}")

    @classmethod
    def _trigger_security_alert(cls, log_entry: 'PHIAccessLog'):
        """
        Trigger security alert for suspicious PHI access
        """
        try:
            # Send alert to security team
            alert_message = f"""
            SUSPICIOUS PHI ACCESS DETECTED:

            User: {log_entry.user.username if log_entry.user else 'Unknown'}
            Patient ID: {log_entry.patient_id}
            Access Type: {log_entry.access_type}
            Resource: {log_entry.resource_type}
            Time: {log_entry.timestamp}
            IP: {log_entry.ip_address}

            Details: {log_entry.purpose_justification}
            """

            send_mail(
                subject='SECURITY ALERT: Suspicious PHI Access',
                message=alert_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=settings.SECURITY_TEAM_EMAILS,
                fail_silently=True
            )

            # Log security event
            from core.security_compliance import log_security_event
            log_security_event(
                event_type='suspicious_phi_access',
                user=log_entry.user,
                metadata={
                    'phi_access_log_id': str(log_entry.uuid),
                    'access_type': log_entry.access_type,
                    'resource_type': log_entry.resource_type,
                    'suspicious_indicators': {
                        'unauthorized': not log_entry.was_authorized,
                        'bulk_access': log_entry.is_bulk_access,
                        'after_hours': not (8 <= log_entry.timestamp.hour <= 18)
                    }
                }
            )

        except Exception as e:
            logger.error(f"Failed to trigger security alert: {e}")


class HIPAARiskAssessment(models.Model):
    """
    HIPAA Security Risk Assessment documentation and tracking
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Assessment details
    title = models.CharField(max_length=200)
    assessment_period_start = models.DateField()
    assessment_period_end = models.DateField()
    assessment_date = models.DateTimeField(auto_now_add=True)

    # Scope
    scope_description = models.TextField()
    systems_assessed = models.JSONField(default=list)
    data_types_assessed = models.JSONField(default=list)

    # Risk identification
    threats_identified = models.JSONField(default=list)
    vulnerabilities_identified = models.JSONField(default=list)

    # Risk analysis
    risk_level = models.CharField(
        max_length=20,
        choices=[(r.value, r.name.replace('_', ' ').title()) for r in HIPAARiskLevel]
    )
    likelihood_rating = models.CharField(
        max_length=20,
        choices=[
            ('VERY_LOW', 'Very Low'),
            ('LOW', 'Low'),
            ('MODERATE', 'Moderate'),
            ('HIGH', 'High'),
            ('VERY_HIGH', 'Very High'),
        ]
    )
    impact_rating = models.CharField(
        max_length=20,
        choices=[
            ('NEGLIGIBLE', 'Negligible'),
            ('MINOR', 'Minor'),
            ('MODERATE', 'Moderate'),
            ('MAJOR', 'Major'),
            ('SEVERE', 'Severe'),
        ]
    )

    # Risk determination
    risk_score = models.DecimalField(max_digits=5, decimal_places=2)
    is_acceptable = models.BooleanField(default=False)

    # Mitigation
    mitigation_strategy = models.TextField()
    mitigation_controls = models.JSONField(default=list)
    implementation_responsible = models.CharField(max_length=100, blank=True)
    implementation_deadline = models.DateField(null=True, blank=True)

    # Review
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reviewed_risk_assessments'
    )
    review_date = models.DateTimeField(null=True, blank=True)
    next_assessment_date = models.DateField(null=True, blank=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('DRAFT', 'Draft'),
            ('REVIEW', 'Under Review'),
            ('APPROVED', 'Approved'),
            ('IMPLEMENTED', 'Mitigation Implemented'),
            ('MONITORING', 'Monitoring'),
        ],
        default='DRAFT'
    )

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_risk_assessments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['assessment_period_start']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['status']),
            models.Index(fields=['next_assessment_date']),
        ]
        ordering = ['-assessment_date']

    def __str__(self):
        return f"Risk Assessment: {self.title}"

    def calculate_risk_score(self) -> float:
        """
        Calculate risk score based on likelihood and impact
        Uses simplified risk matrix
        """
        likelihood_values = {
            'VERY_LOW': 1,
            'LOW': 2,
            'MODERATE': 3,
            'HIGH': 4,
            'VERY_HIGH': 5
        }

        impact_values = {
            'NEGLIGIBLE': 1,
            'MINOR': 2,
            'MODERATE': 3,
            'MAJOR': 4,
            'SEVERE': 5
        }

        likelihood_score = likelihood_values.get(self.likelihood_rating, 1)
        impact_score = impact_values.get(self.impact_rating, 1)

        self.risk_score = float(likelihood_score * impact_score)

        # Determine risk level
        if self.risk_score <= 4:
            self.risk_level = HIPAARiskLevel.LOW.value
        elif self.risk_score <= 9:
            self.risk_level = HIPAARiskLevel.MODERATE.value
        elif self.risk_score <= 16:
            self.risk_level = HIPAARiskLevel.HIGH.value
        else:
            self.risk_level = HIPAARiskLevel.CRITICAL.value

        self.save()
        return self.risk_score


class HIPAATrainingRecord(models.Model):
    """
    HIPAA workforce training tracking
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Training details
    training_name = models.CharField(max_length=200)
    training_description = models.TextField(blank=True)
    training_type = models.CharField(
        max_length=50,
        choices=[
            ('HIPAA_AWARENESS', 'HIPAA Awareness'),
            ('HIPAA_SECURITY', 'HIPAA Security Rule'),
            ('HIPAA_PRIVACY', 'HIPAA Privacy Rule'),
            ('PHI_HANDLING', 'PHI Handling Procedures'),
            ('BREACH_NOTIFICATION', 'Breach Notification'),
            ('SECURITY_AWARENESS', 'Security Awareness'),
            ('ROLE_SPECIFIC', 'Role-Specific Training'),
        ]
    )

    # Training content
    content_outline = models.TextField(blank=True)
    learning_objectives = models.JSONField(default=list)
    materials_provided = models.JSONField(default=list)

    # Training session
    training_date = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField()
    delivery_method = models.CharField(
        max_length=50,
        choices=[
            ('IN_PERSON', 'In-Person'),
            ('VIRTUAL', 'Virtual/Live'),
            ('E_LEARNING', 'E-Learning/Online'),
            ('RECORDED', 'Recorded Session'),
            ('DOCUMENT', 'Documentation Only'),
        ]
    )
    instructor_name = models.CharField(max_length=100, blank=True)
    instructor_qualifications = models.TextField(blank=True)

    # Attendance
    attendees = models.ManyToManyField(User, through='HIPAATrainingAttendance')
    required_for_roles = models.JSONField(default=list)
    required_for_departments = models.JSONField(default=list)

    # Assessment
    has_assessment = models.BooleanField(default=False)
    assessment_type = models.CharField(max_length=50, blank=True)
    passing_score = models.PositiveIntegerField(null=True, blank=True)

    # Compliance
    covers_hipaa_requirements = models.JSONField(default=list)
    references_policies = models.JSONField(default=list)

    # Records retention
    retention_until = models.DateTimeField(default=lambda: timezone.now() + timedelta(days=365*6))  # 6 years

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_trainings'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['training_type']),
            models.Index(fields=['training_date']),
            models.Index(fields=['is_active']),
        ]
        ordering = ['-training_date']

    def __str__(self):
        return f"{self.training_name} - {self.training_date.strftime('%Y-%m-%d')}"


class HIPAATrainingAttendance(models.Model):
    """
    Individual training attendance records
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    training = models.ForeignKey(
        HIPAATrainingRecord,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='hipaa_training_records'
    )

    # Attendance details
    attended_at = models.DateTimeField(default=timezone.now)
    attendance_method = models.CharField(
        max_length=50,
        choices=[
            ('IN_PERSON', 'In-Person'),
            ('VIRTUAL', 'Virtual/Live'),
            ('E_LEARNING', 'E-Learning/Online'),
            ('RECORDED', 'Recorded Session'),
        ]
    )
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100.0)

    # Assessment results
    assessment_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    passed_assessment = models.BooleanField(null=True, blank=True)
    assessment_date = models.DateTimeField(null=True, blank=True)

    # Certification
    certificate_issued = models.BooleanField(default=False)
    certificate_number = models.CharField(max_length=100, blank=True)
    certificate_expiry = models.DateField(null=True, blank=True)

    # Acknowledgment
    policy_acknowledged = models.BooleanField(default=False)
    acknowledgment_date = models.DateTimeField(null=True, blank=True)

    # Retraining
    retraining_required = models.BooleanField(default=False)
    retraining_reason = models.TextField(blank=True)
    next_training_date = models.DateField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'training']),
            models.Index(fields=['attended_at']),
            models.Index(fields=['passed_assessment']),
            models.Index(fields=['next_training_date']),
        ]
        unique_together = ['user', 'training']
        ordering = ['-attended_at']

    def __str__(self):
        return f"{self.user.username} - {self.training.training_name}"

    def is_compliant(self) -> bool:
        """
        Check if user is compliant with training requirements
        """
        if not self.passed_assessment:
            return False

        # Check if training is still valid (typically 1 year)
        if self.certificate_expiry and self.certificate_expiry < timezone.now().date():
            return False

        # Check if retraining is required
        if self.retraining_required:
            return False

        return True

    def schedule_retraining(self):
        """
        Schedule annual retraining
        """
        self.next_training_date = timezone.now().date() + timedelta(days=365)
        self.save()


class BusinessAssociateAgreement(models.Model):
    """
    Business Associate Agreement tracking for HIPAA compliance
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Business Associate details
    ba_name = models.CharField(max_length=200)
    ba_type = models.CharField(
        max_length=50,
        choices=[
            ('CLOUD_PROVIDER', 'Cloud Service Provider'),
            ('IT_VENDOR', 'IT Service Vendor'),
            ('BILLING_SERVICE', 'Billing Service'),
            ('EHR_VENDOR', 'EHR Vendor'),
            ('LAB_SERVICE', 'Laboratory Service'),
            ('PHARMACY', 'Pharmacy Service'),
            ('CLAIMS_PROCESSOR', 'Claims Processor'),
            ('OTHER', 'Other'),
        ]
    )
    ba_address = models.TextField()
    ba_contact_person = models.CharField(max_length=100)
    ba_contact_email = models.EmailField()
    ba_contact_phone = models.CharField(max_length=20)

    # Agreement details
    agreement_start_date = models.DateField()
    agreement_end_date = models.DateField(null=True, blank=True)
    auto_renewal = models.BooleanField(default=True)
    renewal_term_months = models.PositiveIntegerField(default=12)

    # Services provided
    services_description = models.TextField()
    phi_disclosure_purpose = models.TextField()
    permitted_uses = models.JSONField(default=list)
    prohibited_uses = models.JSONField(default=list)

    # Security requirements
    encryption_required = models.BooleanField(default=True)
    audit_rights_required = models.BooleanField(default=True)
    reporting_requirements = models.TextField(blank=True)
    breach_notification_procedure = models.TextField(blank=True)

    # Documentation
    agreement_document = models.FileField(upload_to='baa_documents/', blank=True)
    amendment_history = models.JSONField(default=list, blank=True)

    # Compliance monitoring
    last_audit_date = models.DateField(null=True, blank=True)
    next_audit_date = models.DateField(null=True, blank=True)
    compliance_issues = models.JSONField(default=list, blank=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('DRAFT', 'Draft'),
            ('PENDING_SIGNATURE', 'Pending Signature'),
            ('ACTIVE', 'Active'),
            ('EXPIRED', 'Expired'),
            ('TERMINATED', 'Terminated'),
            ('SUSPENDED', 'Suspended'),
        ],
        default='DRAFT'
    )

    # Contacts
    internal_contact = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='managed_baas'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['ba_name']),
            models.Index(fields=['status']),
            models.Index(fields=['agreement_end_date']),
            models.Index(fields=['next_audit_date']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"BAA with {self.ba_name}"

    def is_active_and_valid(self) -> bool:
        """
        Check if BAA is active and not expired
        """
        if self.status != 'ACTIVE':
            return False

        if self.agreement_end_date and self.agreement_end_date < timezone.now().date():
            return False

        return True

    def check_compliance(self) -> Dict:
        """
        Check BAA compliance status
        """
        compliance_issues = []

        # Check if agreement is current
        if not self.is_active_and_valid():
            compliance_issues.append("BAA is not active or has expired")

        # Check if audit is current
        if self.last_audit_date:
            days_since_audit = (timezone.now().date() - self.last_audit_date).days
            if days_since_audit > 365:
                compliance_issues.append("Annual audit required")

        # Check for outstanding issues
        if self.compliance_issues:
            compliance_issues.extend(self.compliance_issues)

        return {
            'is_compliant': len(compliance_issues) == 0,
            'issues': compliance_issues,
            'days_until_expiry': (
                (self.agreement_end_date - timezone.now().date()).days
                if self.agreement_end_date else None
            ),
            'days_until_audit': (
                (self.next_audit_date - timezone.now().date()).days
                if self.next_audit_date else None
            )
        }


class HIPAAComplianceManager:
    """
    Manager class for HIPAA compliance operations
    """

    def __init__(self):
        self.security_framework = SecurityComplianceFramework()

    def perform_risk_assessment(self, scope: Dict = None) -> HIPAARiskAssessment:
        """
        Perform HIPAA security risk assessment
        """
        # Create risk assessment record
        risk_assessment = HIPAARiskAssessment.objects.create(
            title=f"Annual Risk Assessment {timezone.now().year}",
            assessment_period_start=timezone.now().date() - timedelta(days=365),
            assessment_period_end=timezone.now().date(),
            scope_description=scope.get('description', 'Enterprise-wide assessment'),
            systems_assessed=scope.get('systems', ['All Systems']),
            data_types_assessed=scope.get('data_types', ['PHI', 'ePHI']),
        )

        # Analyze security events
        recent_events = SecurityEvent.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=365)
        )

        # Identify threats and vulnerabilities
        threats = []
        vulnerabilities = []

        # Check for failed logins
        failed_logins = recent_events.filter(event_type='LOGIN_FAILED').count()
        if failed_logins > 100:
            threats.append("Brute force attacks")
            vulnerabilities.append("Weak password policies or MFA not enforced")

        # Check for unauthorized access
        unauthorized_access = PHIAccessLog.objects.filter(
            was_authorized=False,
            timestamp__gte=timezone.now() - timedelta(days=365)
        ).count()
        if unauthorized_access > 0:
            threats.append("Unauthorized PHI access")
            vulnerabilities.append("Insufficient access controls")

        risk_assessment.threats_identified = threats
        risk_assessment.vulnerabilities_identified = vulnerabilities

        # Calculate risk level
        risk_score = min(failed_logins * 0.5 + unauthorized_access * 10, 25)

        if risk_score <= 5:
            risk_assessment.risk_level = HIPAARiskLevel.LOW.value
        elif risk_score <= 10:
            risk_assessment.risk_level = HIPAARiskLevel.MODERATE.value
        elif risk_score <= 15:
            risk_assessment.risk_level = HIPAARiskLevel.HIGH.value
        else:
            risk_assessment.risk_level = HIPAARiskLevel.CRITICAL.value

        risk_assessment.likelihood_rating = 'MODERATE'
        risk_assessment.impact_rating = 'MAJOR'
        risk_assessment.calculate_risk_score()

        return risk_assessment

    def generate_compliance_report(self) -> Dict:
        """
        Generate comprehensive HIPAA compliance report
        """
        report = {
            'generated_at': timezone.now(),
            'report_period': {
                'start': timezone.now() - timedelta(days=365),
                'end': timezone.now()
            },
            'sections': {}
        }

        # Safeguard implementation status
        safeguards = HIPAASafeguard.objects.all()
        safeguard_stats = {
            'total': safeguards.count(),
            'implemented': safeguards.filter(implementation_status='IMPLEMENTED').count(),
            'partially_implemented': safeguards.filter(implementation_status='PARTIALLY_IMPLEMENTED').count(),
            'not_implemented': safeguards.filter(implementation_status='NOT_IMPLEMENTED').count(),
            'compliant': safeguards.filter(is_compliant=True).count(),
        }
        report['sections']['safeguards'] = safeguard_stats

        # PHI access statistics
        phi_stats = {
            'total_access_events': PHIAccessLog.objects.count(),
            'unauthorized_access': PHIAccessLog.objects.filter(was_authorized=False).count(),
            'suspicious_access': PHIAccessLog.objects.filter(is_suspicious=True).count(),
            'bulk_access': PHIAccessLog.objects.filter(is_bulk_access=True).count(),
            'access_by_purpose': {},
            'access_by_type': {},
        }

        # Aggregate by purpose
        for purpose, _ in PHIAccessLog._meta.get_field('access_purpose').choices:
            phi_stats['access_by_purpose'][purpose] = PHIAccessLog.objects.filter(
                access_purpose=purpose
            ).count()

        # Aggregate by type
        for access_type, _ in PHIAccessLog._meta.get_field('access_type').choices:
            phi_stats['access_by_type'][access_type] = PHIAccessLog.objects.filter(
                access_type=access_type
            ).count()

        report['sections']['phi_access'] = phi_stats

        # Training compliance
        training_stats = {
            'total_employees': User.objects.filter(is_active=True).count(),
            'trained_employees': HIPAATrainingAttendance.objects.filter(
                passed_assessment=True,
                certificate_expiry__gte=timezone.now().date()
            ).values('user').distinct().count(),
            'overdue_training': HIPAATrainingAttendance.objects.filter(
                next_training_date__lt=timezone.now().date()
            ).count(),
        }
        training_stats['compliance_rate'] = (
            (training_stats['trained_employees'] / training_stats['total_employees'] * 100)
            if training_stats['total_employees'] > 0 else 0
        )
        report['sections']['training'] = training_stats

        # Business Associate agreements
        baa_stats = {
            'total_agreements': BusinessAssociateAgreement.objects.count(),
            'active_agreements': BusinessAssociateAgreement.objects.filter(status='ACTIVE').count(),
            'expired_agreements': BusinessAssociateAgreement.objects.filter(
                agreement_end_date__lt=timezone.now().date()
            ).count(),
            'audits_overdue': BusinessAssociateAgreement.objects.filter(
                next_audit_date__lt=timezone.now().date()
            ).count(),
        }
        report['sections']['business_associates'] = baa_stats

        # Risk assessment summary
        latest_risk = HIPAARiskAssessment.objects.order_by('-assessment_date').first()
        if latest_risk:
            report['sections']['risk_assessment'] = {
                'last_assessment': latest_risk.assessment_date,
                'risk_level': latest_risk.risk_level,
                'risk_score': latest_risk.risk_score,
                'mitigation_status': latest_risk.status,
            }

        # Overall compliance score
        implemented_safeguards = safeguard_stats['implemented'] + safeguard_stats['partially_implemented'] * 0.5
        safeguard_compliance = (implemented_safeguards / safeguard_stats['total'] * 100) if safeguard_stats['total'] > 0 else 0

        training_compliance = training_stats['compliance_rate']
        baa_compliance = (
            (baa_stats['active_agreements'] / baa_stats['total_agreements'] * 100)
            if baa_stats['total_agreements'] > 0 else 100
        )

        report['overall_compliance_score'] = round(
            (safeguard_compliance * 0.5 + training_compliance * 0.3 + baa_compliance * 0.2),
            2
        )

        return report

    def check_breach_notification_requirements(self, incident_data: Dict) -> Dict:
        """
        Check if breach notification is required per HIPAA rules
        """
        affected_individuals = incident_data.get('affected_individuals', 0)
        data_types = incident_data.get('data_types', [])
        was_encrypted = incident_data.get('was_encrypted', False)
        contained_immediately = incident_data.get('contained_immediately', False)

        # HIPAA breach notification threshold
        requires_notification = affected_individuals > 0

        # Check exceptions
        if was_encrypted and not incident_data.get('encryption_breached', False):
            requires_notification = False

        if contained_immediately and affected_individuals < 500:
            requires_notification = False

        # Determine notification timeline
        if requires_notification:
            if affected_individuals > 500:
                notification_deadline = 60  # days
                media_notification_required = True
            else:
                notification_deadline = 60  # days
                media_notification_required = False
        else:
            notification_deadline = None
            media_notification_required = False

        return {
            'breach_occurred': requires_notification,
            'notification_required': requires_notification,
            'notification_deadline_days': notification_deadline,
            'media_notification_required': media_notification_required,
            'individual_notification_required': requires_notification,
            'hhs_notification_required': requires_notification and affected_individuals > 500,
        }


# Create default HIPAA safeguards on migration
def create_default_hipaa_safeguards():
    """
    Create default HIPAA safeguards during migration
    """
    safeguards_data = [
        # Technical Safeguards
        {
            'name': 'Unique User Identification',
            'description': 'Assign unique name and/or number for tracking user identity',
            'safeguard_type': 'TECHNICAL',
            'specification': 'ACCESS_CONTROL',
            'implementation_status': 'IMPLEMENTED',
        },
        {
            'name': 'Emergency Access Procedure',
            'description': 'Establish procedures for obtaining necessary PHI during emergency',
            'safeguard_type': 'TECHNICAL',
            'specification': 'ACCESS_CONTROL',
            'implementation_status': 'IMPLEMENTED',
        },
        {
            'name': 'Automatic Logoff',
            'description': 'Implement electronic procedures that terminate sessions after inactivity',
            'safeguard_type': 'TECHNICAL',
            'specification': 'ACCESS_CONTROL',
            'implementation_status': 'IMPLEMENTED',
        },
        {
            'name': 'Encryption and Decryption',
            'description': 'Implement mechanisms to encrypt and decrypt PHI',
            'safeguard_type': 'TECHNICAL',
            'specification': 'TRANSMISSION_SECURITY',
            'implementation_status': 'IMPLEMENTED',
        },
        # Administrative Safeguards
        {
            'name': 'Security Management Process',
            'description': 'Implement policies to prevent, detect, contain, and correct security violations',
            'safeguard_type': 'ADMINISTRATIVE',
            'specification': 'SECURITY_MANAGEMENT',
            'implementation_status': 'IMPLEMENTED',
        },
        {
            'name': 'Workforce Security',
            'description': 'Implement policies to ensure workforce members comply with security policies',
            'safeguard_type': 'ADMINISTRATIVE',
            'specification': 'WORKFORCE_SECURITY',
            'implementation_status': 'IMPLEMENTED',
        },
        {
            'name': 'Information Access Management',
            'description': 'Implement policies for authorization and/or supervision of workforce members',
            'safeguard_type': 'ADMINISTRATIVE',
            'specification': 'INFORMATION_ACCESS',
            'implementation_status': 'IMPLEMENTED',
        },
        {
            'name': 'Security Awareness and Training',
            'description': 'Implement security awareness and training program for workforce members',
            'safeguard_type': 'ADMINISTRATIVE',
            'specification': 'TRAINING',
            'implementation_status': 'IMPLEMENTED',
        },
        # Physical Safeguards
        {
            'name': 'Facility Access Controls',
            'description': 'Implement policies to limit physical access to electronic information systems',
            'safeguard_type': 'PHYSICAL',
            'specification': 'FACILITY_ACCESS',
            'implementation_status': 'PARTIALLY_IMPLEMENTED',
        },
        {
            'name': 'Workstation Use',
            'description': 'Implement policies specifying proper functions of workstations',
            'safeguard_type': 'PHYSICAL',
            'specification': 'WORKSTATION_SECURITY',
            'implementation_status': 'IMPLEMENTED',
        },
        {
            'name': 'Device and Media Controls',
            'description': 'Implement policies for disposal and reuse of electronic media',
            'safeguard_type': 'PHYSICAL',
            'specification': 'DEVICE_SECURITY',
            'implementation_status': 'IMPLEMENTED',
        },
    ]

    for safeguard_data in safeguards_data:
        HIPAASafeguard.objects.get_or_create(
            name=safeguard_data['name'],
            defaults=safeguard_data
        )