import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import models, transaction
from django.db.models import Q, F
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from encrypted_model_fields.fields import (
    EncryptedCharField,
    EncryptedEmailField,
    EncryptedTextField,
)

from core.models import TenantModel

User = get_user_model()

logger = logging.getLogger(__name__)


class DataRetentionPolicy(models.TextChoices):
    """
    HIPAA compliant data retention policies
    """
    IMMEDIATE_DELETE = "IMMEDIATE_DELETE", _("Immediate Delete")
    RETAIN_1_YEAR = "RETAIN_1_YEAR", _("Retain 1 Year")
    RETAIN_2_YEARS = "RETAIN_2_YEARS", _("Retain 2 Years")
    RETAIN_5_YEARS = "RETAIN_5_YEARS", _("Retain 5 Years")
    RETAIN_7_YEARS = "RETAIN_7_YEARS", _("Retain 7 Years")  # HIPAA minimum
    RETAIN_10_YEARS = "RETAIN_10_YEARS", _("Retain 10 Years")
    RETAIN_20_YEARS = "RETAIN_20_YEARS", _("Retain 20 Years")  # State requirements
    RETAIN_PERMANENT = "RETAIN_PERMANENT", _("Retain Permanently")  # For research


class ConsentType(models.TextChoices):
    """
    GDPR Article 7 compliant consent types
    """
    GENERAL_TREATMENT = "GENERAL_TREATMENT", _("General Treatment Consent")
    SPECIFIC_PROCEDURE = "SPECIFIC_PROCEDURE", _("Specific Procedure Consent")
    RESEARCH_PARTICIPATION = "RESEARCH_PARTICIPATION", _("Research Participation")
    MARKETING_COMMUNICATIONS = "MARKETING_COMMUNICATIONS", _("Marketing Communications")
    DATA_SHARING = "DATA_SHARING", _("Data Sharing with Third Parties")
    EMERGENCY_CONTACT = "EMERGENCY_CONTACT", _("Emergency Contact Disclosure")
    INSURANCE_BILLING = "INSURANCE_BILLING", _("Insurance Billing and Payment")
    TELEMEDICINE = "TELEMEDICINE", _("Telemedicine Services")
    MENTAL_HEALTH = "MENTAL_HEALTH", _("Mental Health Services")
    SUBSTANCE_ABUSE = "SUBSTANCE_ABUSE", _("Substance Abuse Treatment")
    HIV_AIDS = "HIV_AIDS", _("HIV/AIDS Related Information")
    GENETIC_INFORMATION = "GENETIC_INFORMATION", _("Genetic Information")


class ConsentStatus(models.TextChoices):
    """
    Consent lifecycle status
    """
    ACTIVE = "ACTIVE", _("Active")
    EXPIRED = "EXPIRED", _("Expired")
    REVOKED = "REVOKED", _("Revoked")
    PENDING = "PENDING", _("Pending Signature")
    ARCHIVED = "ARCHIVED", _("Archived")


class DataAccessType(models.TextChoices):
    """
    HIPAA compliant access type classification
    """
    VIEW = "VIEW", _("View PHI")
    MODIFY = "MODIFY", _("Modify PHI")
    SHARE = "SHARE", _("Share PHI")
    EXPORT = "EXPORT", _("Export PHI")
    DELETE = "DELETE", _("Delete PHI")
    DOWNLOAD = "DOWNLOAD", _("Download PHI")


class AccessPurpose(models.TextChoices):
    """
    HIPAA Treatment, Payment, and Healthcare Operations (TPO)
    """
    TREATMENT = "TREATMENT", _("Treatment")
    PAYMENT = "PAYMENT", _("Payment Operations")
    HEALTHCARE_OPERATIONS = "HEALTHCARE_OPERATIONS", _("Healthcare Operations")
    PUBLIC_HEALTH = "PUBLIC_HEALTH", _("Public Health Activities")
    VICTIMS_ABUSE = "VICTIMS_ABUSE", _("Victims of Abuse, Neglect, or Domestic Violence")
    HEALTH_OVERSIGHT = "HEALTH_OVERSIGHT", _("Health Oversight Activities")
    JUDICIAL_PROCEEDINGS = "JUDICIAL_PROCEEDINGS", _("Judicial and Administrative Proceedings")
    LAW_ENFORCEMENT = "LAW_ENFORCEMENT", _("Law Enforcement Purposes")
    CORONERS_MEDICAL_EXAMINERS = "CORONERS_MEDICAL_EXAMINERS", _("Coroners, Medical Examiners, and Funeral Directors")
    ORGAN_DONATION = "ORGAN_DONATION", _("Organ, Eye, or Tissue Donation")
    RESEARCH = "RESEARCH", _("Research")
    SERIOUS_THREAT = "SERIOUS_THREAT", _("Serious Threat to Health or Safety")
    SPECIALIZED_GOVT = "SPECIALIZED_GOVT", _("Specialized Government Functions")
    WORKERS_COMP = "WORKERS_COMP", _("Workers' Compensation")


class ConsentManagement(TenantModel):
    """
    GDPR Article 7 compliant consent management system
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='consents')
    consent_type = models.CharField(max_length=50, choices=ConsentType.choices)
    status = models.CharField(max_length=20, choices=ConsentStatus.choices, default=ConsentStatus.PENDING)
    version = models.PositiveIntegerField(default=1)

    # Consent Details
    title = models.CharField(max_length=200)
    description = EncryptedTextField()
    purpose = EncryptedTextField()
    data_categories = models.JSONField(default=list, help_text="Categories of data covered by consent")
    third_parties = models.JSONField(default=list, help_text="Third parties who may receive data")
    retention_period = models.CharField(max_length=30, choices=DataRetentionPolicy.choices)

    # Consent Lifecycle
    consent_date = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    revoked_date = models.DateTimeField(null=True, blank=True)
    withdrawal_method = models.CharField(max_length=50, blank=True)

    # Consent Evidence
    consent_form_url = models.URLField(blank=True)
    digital_signature_data = models.JSONField(default=dict, blank=True)
    witness_name = models.CharField(max_length=100, blank=True)
    interpreter_used = models.BooleanField(default=False)
    interpreter_name = models.CharField(max_length=100, blank=True)
    language_preference = models.CharField(max_length=10, default='EN')

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_consents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['patient', 'consent_type', 'status']),
            models.Index(fields=['patient', 'is_active', 'consent_date']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['hospital', 'consent_type']),
        ]
        unique_together = ['patient', 'consent_type', 'version']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.patient} - {self.get_consent_type_display()} (v{self.version})"

    def is_valid(self) -> bool:
        """Check if consent is currently valid"""
        now = timezone.now()
        return (
            self.status == ConsentStatus.ACTIVE and
            self.consent_date and
            self.consent_date <= now and
            (not self.expiry_date or self.expiry_date > now)
        )

    def revoke(self, reason: str = "", revoked_by: Optional[User] = None) -> None:
        """Revoke consent with proper audit trail"""
        with transaction.atomic():
            self.status = ConsentStatus.REVOKED
            self.revoked_date = timezone.now()
            self.save()

            # Create audit entry
            ConsentAuditLog.objects.create(
                patient=self.patient,
                consent=self,
                action="REVOKED",
                action_by=revoked_by,
                details=f"Consent revoked: {reason}",
                ip_address=self._get_client_ip()
            )

    def renew(self, new_expiry_date: datetime, renewed_by: User) -> 'ConsentManagement':
        """Create new version of consent with updated expiry"""
        with transaction.atomic():
            # Archive current version
            self.status = ConsentStatus.ARCHIVED
            self.save()

            # Create new version
            new_consent = ConsentManagement.objects.create(
                patient=self.patient,
                consent_type=self.consent_type,
                title=self.title,
                description=self.description,
                purpose=self.purpose,
                data_categories=self.data_categories,
                third_parties=self.third_parties,
                retention_period=self.retention_period,
                consent_date=timezone.now(),
                expiry_date=new_expiry_date,
                version=self.version + 1,
                consent_form_url=self.consent_form_url,
                language_preference=self.language_preference,
                created_by=renewed_by,
                hospital=self.hospital
            )

            # Log renewal
            ConsentAuditLog.objects.create(
                patient=self.patient,
                consent=new_consent,
                action="RENEWED",
                action_by=renewed_by,
                details=f"Consent renewed, new expiry: {new_expiry_date}",
                ip_address=self._get_client_ip()
            )

            return new_consent

    @classmethod
    def get_active_consents(cls, patient_id: int) -> List['ConsentManagement']:
        """Get all currently valid consents for a patient"""
        now = timezone.now()
        return cls.objects.filter(
            patient_id=patient_id,
            status=ConsentStatus.ACTIVE,
            consent_date__lte=now,
            is_active=True
        ).filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gt=now)
        )

    @staticmethod
    def _get_client_ip() -> str:
        """Get client IP address (implementation depends on request context)"""
        # This should be overridden with actual request context
        return "127.0.0.1"


class ConsentAuditLog(TenantModel):
    """
    Complete audit trail for consent management (GDPR Article 7.3)
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='consent_audit_logs')
    consent = models.ForeignKey(ConsentManagement, on_delete=models.CASCADE, related_name='audit_logs')

    action = models.CharField(max_length=50, help_text="Action performed")
    action_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='consent_audit_actions')
    action_date = models.DateTimeField(auto_now_add=True)
    details = models.TextField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)

    # For tracking changes
    previous_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)

    # Security context
    session_id = models.CharField(max_length=100, blank=True)
    device_fingerprint = models.CharField(max_length=100, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['patient', 'action_date']),
            models.Index(fields=['consent', 'action_date']),
            models.Index(fields=['action_by', 'action_date']),
            models.Index(fields=['hospital', 'action_date']),
        ]
        ordering = ['-action_date']

    def __str__(self):
        return f"{self.patient} - {self.action} by {self.action_by}"


class DataSubjectRequest(TenantModel):
    """
    GDPR Articles 15, 16, 17, 18, 20, 21 compliant data subject requests
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='data_requests')
    request_type = models.CharField(
        max_length=50,
        choices=[
            ("ACCESS", "Right of Access"),
            ("RECTIFICATION", "Right to Rectification"),
            ("ERASURE", "Right to Erasure / Right to be Forgotten"),
            ("RESTRICT", "Right to Restrict Processing"),
            ("DATA_PORTABILITY", "Right to Data Portability"),
            ("OBJECT", "Right to Object"),
            ("AUTOMATED_DECISION", "Right Regarding Automated Decision Making"),
        ]
    )
    status = models.CharField(
        max_length=30,
        choices=[
            ("PENDING", "Pending Review"),
            ("IN_PROGRESS", "In Progress"),
            ("COMPLETED", "Completed"),
            ("REJECTED", "Rejected"),
            ("ESCALATED", "Escalated"),
        ],
        default="PENDING"
    )

    # Request details
    description = models.TextField()
    scope = models.JSONField(default=list, help_text="Specific data categories requested")
    timeframe = models.JSONField(default=dict, help_text="Timeframe for data requested")

    # Processing timeline
    received_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    completed_date = models.DateTimeField(null=True, blank=True)

    # Response
    response_data = models.JSONField(default=dict, blank=True)
    response_message = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    # Handling
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_requests')
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='completed_requests')

    # Metadata
    priority = models.CharField(max_length=20, choices=[("NORMAL", "Normal"), ("URGENT", "Urgent")], default="NORMAL")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['patient', 'request_type', 'status']),
            models.Index(fields=['status', 'due_date']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['hospital', 'received_date']),
        ]
        ordering = ['-received_date']

    def __str__(self):
        return f"{self.patient} - {self.get_request_type_display()}"

    def save(self, *args, **kwargs):
        if not self.due_date:
            # GDPR requires response within 30 days
            self.due_date = self.received_date + timedelta(days=30)
        super().save(*args, **kwargs)

    def process_access_request(self) -> Dict:
        """Process GDPR Article 15 access request"""
        from .services import DataAccessService

        try:
            data_access_service = DataAccessService()
            accessible_data = data_access_service.get_patient_data_summary(self.patient.id, self.scope)

            self.response_data = {
                'data_summary': accessible_data,
                'data_sources': data_access_service.get_data_sources(),
                'data_processors': data_access_service.get_data_processors(),
                'retention_policies': data_access_service.get_retention_policies(),
            }
            self.status = "COMPLETED"
            self.completed_date = timezone.now()
            self.save()

            return self.response_data

        except Exception as e:
            logger.error(f"Error processing access request {self.id}: {e}")
            raise

    def process_erasure_request(self) -> bool:
        """Process GDPR Article 17 erasure request"""
        from .services import DataErasureService

        try:
            erasure_service = DataErasureService()
            success = erasure_service.erase_patient_data(
                self.patient.id,
                self.scope,
                preserve_legal_obligations=True
            )

            if success:
                self.status = "COMPLETED"
                self.completed_date = timezone.now()
                self.response_message = "Data has been successfully erased in accordance with your request."
            else:
                self.status = "REJECTED"
                self.rejection_reason = "Unable to complete erasure due to legal or contractual obligations."

            self.save()
            return success

        except Exception as e:
            logger.error(f"Error processing erasure request {self.id}: {e}")
            raise


class DataSubjectRequestAudit(TenantModel):
    """
    Audit trail for data subject requests
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    request = models.ForeignKey(DataSubjectRequest, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=50)
    action_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action_date = models.DateTimeField(auto_now_add=True)
    details = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=['request', 'action_date']),
            models.Index(fields=['hospital', 'action_date']),
        ]
        ordering = ['-action_date']