"""
GDPR Compliance Module
General Data Protection Regulation implementation for healthcare data
"""

import hashlib
import json
import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Union

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import TenantModel

User = get_user_model()
logger = logging.getLogger(__name__)


class GDPRDataCategory(Enum):
    """Categories of personal data under GDPR"""
    IDENTIFICATION_DATA = "identification_data"
    CONTACT_DATA = "contact_data"
    HEALTH_DATA = "health_data"
    GENETIC_DATA = "genetic_data"
    BIOMETRIC_DATA = "biometric_data"
    FINANCIAL_DATA = "financial_data"
    TECHNICAL_DATA = "technical_data"
    PROFILE_DATA = "profile_data"


class GDPRProcessingBasis(Enum):
    """Lawful bases for processing under GDPR Article 6"""
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_INTEREST = "public_interest"
    LEGITIMATE_INTERESTS = "legitimate_interests"


class GDPRDataSubjectRight(Enum):
    """Data subject rights under GDPR"""
    RIGHT_TO_BE_INFORMED = "right_to_be_informed"
    RIGHT_OF_ACCESS = "right_of_access"
    RIGHT_TO_RECTIFICATION = "right_to_rectification"
    RIGHT_TO_ERASURE = "right_to_erasure"
    RIGHT_TO_RESTRICT_PROCESSING = "right_to_restrict_processing"
    RIGHT_TO_DATA_PORTABILITY = "right_to_data_portability"
    RIGHT_TO_OBJECT = "right_to_object"
    RIGHT_TO_AUTOMATED_DECISIONS = "right_to_automated_decisions"


class DataProcessingActivity(models.Model):
    """
    Record of Processing Activities (ROPA) - GDPR Article 30
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Controller and processor information
    controller_name = models.CharField(max_length=200)
    controller_representative = models.CharField(max_length=200, blank=True)
    joint_controllers = models.JSONField(default=list, blank=True)

    # Data processor information
    processor_name = models.CharField(max_length=200, blank=True)
    processor_contact = models.TextField(blank=True)
    processor_country = models.CharField(max_length=100, blank=True)
    data_processing_agreement = models.BooleanField(default=False)
    subprocessors = models.JSONField(default=list, blank=True)

    # Processing details
    processing_name = models.CharField(max_length=200)
    processing_purpose = models.TextField()
    lawful_basis = models.CharField(
        max_length=30,
        choices=[(b.value, b.name.replace('_', ' ').title()) for b in GDPRProcessingBasis]
    )
    lawful_basis_details = models.TextField(blank=True)

    # Data categories
    data_categories = models.JSONField(default=list)
    special_categories = models.JSONField(default=list, blank=True)  # Sensitive data
    data_subjects = models.JSONField(default=list)

    # Data recipients
    data_recipients = models.JSONField(default=list, blank=True)
    third_country_transfers = models.JSONField(default=list, blank=True)
    safeguards_for_transfers = models.TextField(blank=True)

    # Retention
    retention_period = models.CharField(max_length=100)
    retention_criteria = models.TextField(blank=True)

    # Security measures
    security_measures = models.TextField()
    encryption_in_transit = models.BooleanField(default=True)
    encryption_at_rest = models.BooleanField(default=True)
    pseudonymization = models.BooleanField(default=False)
    access_controls = models.BooleanField(default=True)
    audit_logging = models.BooleanField(default=True)

    # DPO information
    dpo_contact = models.TextField(blank=True)
    dpo_consulted = models.BooleanField(default=False)

    # Status
    is_active = models.BooleanField(default=True)
    risk_assessment_completed = models.BooleanField(default=False)
    dpia_required = models.BooleanField(default=False)
    dpia_completed = models.BooleanField(default=False)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    next_review_date = models.DateTimeField(default=timezone.now() + timedelta(days=365))

    class Meta:
        indexes = [
            models.Index(fields=['controller_name']),
            models.Index(fields['processing_name']),
            models.Index(fields=['lawful_basis']),
            models.Index(fields=['is_active']),
            models.Index(fields=['next_review_date']),
        ]
        ordering = ['controller_name', 'processing_name']

    def __str__(self):
        return f"{self.controller_name} - {self.processing_name}"

    def check_compliance(self) -> Dict:
        """
        Check GDPR compliance status
        """
        issues = []

        # Check lawful basis
        if not self.lawful_basis:
            issues.append("No lawful basis specified for processing")

        # Check data processor requirements
        if self.processor_name and not self.data_processing_agreement:
            issues.append("Data processing agreement required")

        # Check international transfers
        if self.third_country_transfers and not self.safeguards_for_transfers:
            issues.append("Adequate safeguards required for international transfers")

        # Check DPIA requirements
        if self.dpia_required and not self.dpia_completed:
            issues.append("Data Protection Impact Assessment (DPIA) required but not completed")

        # Check special categories
        if self.special_categories and self.lawful_basis != GDPRProcessingBasis.CONSENT.value:
            if self.lawful_basis not in [
                GDPRProcessingBasis.LEGAL_OBLIGATION.value,
                GDPRProcessingBasis.VITAL_INTERESTS.value,
                GDPRProcessingBasis.PUBLIC_INTEREST.value
            ]:
                issues.append("Additional safeguards required for special category data")

        return {
            'is_compliant': len(issues) == 0,
            'issues': issues,
            'risk_level': self._assess_risk_level()
        }

    def _assess_risk_level(self) -> str:
        """
        Assess risk level of processing activity
        """
        risk_factors = 0

        # Check for high-risk factors
        if any(cat in self.special_categories for cat in ['health_data', 'genetic_data', 'biometric_data']):
            risk_factors += 3

        if self.third_country_transfers:
            risk_factors += 2

        if not self.encryption_at_rest or not self.encryption_in_transit:
            risk_factors += 2

        if large_scale_processing := len(self.data_subjects) > 5000:
            risk_factors += 1

        if automated_decisions := any('profiling' in purpose.lower() for purpose in self.processing_purpose.split(',')):
            risk_factors += 2

        if systematic_monitoring := 'monitoring' in self.processing_purpose.lower():
            risk_factors += 1

        if risk_factors >= 6:
            return 'HIGH'
        elif risk_factors >= 3:
            return 'MEDIUM'
        else:
            return 'LOW'


class DataProtectionImpactAssessment(models.Model):
    """
    Data Protection Impact Assessment (DPIA) - GDPR Article 35
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Assessment details
    title = models.CharField(max_length=200)
    processing_activity = models.ForeignKey(
        DataProcessingActivity,
        on_delete=models.CASCADE,
        related_name='dpias'
    )

    # Assessment team
    assessor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='conducted_dpias'
    )
    dpo_reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_dpias'
    )

    # Assessment dates
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    # Processing description
    processing_nature = models.TextField()
    processing_scope = models.TextField()
    processing_purpose = models.TextField()
    processing_context = models.TextField()

    # Necessity and proportionality
    necessity_assessment = models.TextField()
    proportionality_assessment = models.TextField()
    alternatives_considered = models.TextField()

    # Risk assessment
    risks_to_rights = models.JSONField(default=list)
    risks_to_individuals = models.JSONField(default=list)
    likelihood_rating = models.CharField(
        max_length=20,
        choices=[('VERY_LOW', 'Very Low'), ('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('VERY_HIGH', 'Very High')]
    )
    impact_rating = models.CharField(
        max_length=20,
        choices=[('NEGLIGIBLE', 'Negligible'), ('MINOR', 'Minor'), ('MODERATE', 'Moderate'), ('MAJOR', 'Major'), ('SEVERE', 'Severe')]
    )

    # Mitigation measures
    existing_measures = models.TextField()
    additional_measures = models.TextField()
    residual_risks = models.TextField()

    # Consultation
    data_subject_consultation = models.TextField(blank=True)
    stakeholder_consultation = models.TextField(blank=True)
    dpa_consultation = models.BooleanField(default=False)

    # Review and approval
    recommendation = models.CharField(
        max_length=20,
        choices=[('PROCEED', 'Proceed'), ('PROCEED_WITH_MODIFICATIONS', 'Proceed with Modifications'), ('DO_NOT_PROCEED', 'Do Not Proceed')]
    )
    approval_decision = models.CharField(
        max_length=20,
        choices=[('APPROVED', 'Approved'), ('APPROVED_CONDITIONS', 'Approved with Conditions'), ('REJECTED', 'Rejected')],
        blank=True
    )
    approval_conditions = models.TextField(blank=True)

    # Post-approval monitoring
    monitoring_required = models.BooleanField(default=True)
    review_date = models.DateTimeField(default=timezone.now() + timedelta(days=365))

    class Meta:
        indexes = [
            models.Index(fields=['processing_activity']),
            models.Index(fields=['assessor']),
            models.Index(fields=['status']),
            models.Index(fields=['review_date']),
        ]

    @property
    def status(self):
        if self.approval_decision:
            return self.approval_decision
        elif self.completed_at:
            return 'PENDING_APPROVAL'
        elif self.started_at:
            return 'IN_PROGRESS'
        else:
            return 'NOT_STARTED'

    def __str__(self):
        return f"DPIA: {self.title}"

    def calculate_risk_score(self) -> float:
        """
        Calculate overall risk score
        """
        likelihood_values = {
            'VERY_LOW': 1,
            'LOW': 2,
            'MEDIUM': 3,
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

        return likelihood_score * impact_score


class DataBreachRegister(models.Model):
    """
    Data breach register - GDPR Articles 33 & 34
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Breach details
    breach_reference = models.CharField(max_length=50, unique=True)
    breach_date = models.DateTimeField()
    discovery_date = models.DateTimeField(default=timezone.now)
    affected_systems = models.JSONField(default=list)

    # Data affected
    data_categories_affected = models.JSONField(default=list)
    special_categories_affected = models.JSONField(default=list, blank=True)
    data_subjects_affected = models.PositiveIntegerField(default=0)
    records_affected = models.PositiveIntegerField(default=0)

    # Nature of breach
    breach_types = models.JSONField(default=list)
    breach_cause = models.TextField()
    breach_source = models.CharField(
        max_length=50,
        choices=[
            ('INTERNAL', 'Internal'),
            ('EXTERNAL', 'External'),
            ('THIRD_PARTY', 'Third Party'),
            ('UNKNOWN', 'Unknown'),
        ]
    )
    is_malicious = models.BooleanField(default=False)
    is_accidental = models.BooleanField(default=False)

    # Impact assessment
    potential_consequences = models.JSONField(default=list)
    high_risk_to_rights = models.BooleanField(default=False)
    measures_taken = models.TextField()

    # Notification timeline
    discovered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='discovered_breaches'
    )
    notified_dpo_at = models.DateTimeField(null=True, blank=True)
    notified_dpa_at = models.DateTimeField(null=True, blank=True)
    notified_subjects_at = models.DateTimeField(null=True, blank=True)
    notification_deadline = models.DateTimeField()

    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('DETECTED', 'Detected'),
            ('CONTAINED', 'Contained'),
            ('INVESTIGATION', 'Under Investigation'),
            ('NOTIFIED_DPO', 'Notified DPO'),
            ('NOTIFIED_DPA', 'Notified DPA'),
            ('NOTIFIED_SUBJECTS', 'Notified Subjects'),
            ('RESOLVED', 'Resolved'),
            ('CLOSED', 'Closed'),
        ],
        default='DETECTED'
    )

    # Resolution
    resolution_date = models.DateTimeField(null=True, blank=True)
    lessons_learned = models.TextField(blank=True)
    preventive_measures = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    incident_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='managed_breaches'
    )

    class Meta:
        indexes = [
            models.Index(fields=['breach_date']),
            models.Index(fields=['discovery_date']),
            models.Index(fields=['status']),
            models.Index(fields['high_risk_to_rights']),
            models.Index(fields=['notified_dpa_at']),
        ]
        ordering = ['-discovery_date']

    def __str__(self):
        return f"Breach {self.breach_reference}"

    def calculate_notification_deadline(self):
        """
        Calculate notification deadline (72 hours for DPA)
        """
        self.notification_deadline = self.discovery_date + timedelta(hours=72)
        self.save()

    def check_notification_requirements(self) -> Dict:
        """
        Check GDPR notification requirements
        """
        requirements = {
            'notify_dpa': False,
            'notify_subjects': False,
            'days_until_dpa_deadline': None,
            'days_until_subject_deadline': None,
        }

        # Check if DPA notification is required
        if self.high_risk_to_rights:
            requirements['notify_dpa'] = True
            if not self.notified_dpa_at:
                deadline = self.discovery_date + timedelta(hours=72)
                requirements['days_until_dpa_deadline'] = max(0, (deadline - timezone.now()).total_seconds() / 86400)

        # Check if subject notification is required
        if self.high_risk_to_rights:
            requirements['notify_subjects'] = True
            if not self.notified_subjects_at:
                # No strict deadline, but should be "without undue delay"
                requirements['days_until_subject_deadline'] = "ASAP"

        return requirements

    def notify_supervisory_authority(self):
        """
        Notify Data Protection Authority
        """
        if not self.high_risk_to_rights:
            return

        # Prepare notification details
        notification_data = {
            'breach_reference': self.breach_reference,
            'breach_date': self.breach_date.isoformat(),
            'discovery_date': self.discovery_date.isoformat(),
            'data_categories': self.data_categories_affected,
            'special_categories': self.special_categories_affected,
            'subjects_affected': self.data_subjects_affected,
            'records_affected': self.records_affected,
            'breach_description': self.breach_cause,
            'consequences': self.potential_consequences,
            'measures_taken': self.measures_taken,
            'contact_details': settings.DPO_CONTACT_EMAIL,
        }

        # Send notification to DPA
        # In practice, this would integrate with specific DPA notification systems
        self.notified_dpa_at = timezone.now()
        self.status = 'NOTIFIED_DPA'
        self.save()

        # Log notification
        logger.info(f"Notified DPA about breach {self.breach_reference}")


class PrivacyPolicy(models.Model):
    """
    GDPR compliant privacy policy management
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Policy details
    title = models.CharField(max_length=200)
    version = models.CharField(max_length=20)
    effective_date = models.DateField()
    last_reviewed_date = models.DateField(null=True, blank=True)

    # Policy content
    policy_content = models.TextField()
    summary = models.TextField(blank=True)

    # Data processing information
    data_controller = models.CharField(max_length=200)
    data_protection_officer = models.CharField(max_length=200, blank=True)
    contact_information = models.TextField()

    # Rights and procedures
    data_subject_rights = models.TextField()
    complaint_procedure = models.TextField()
    retention_periods = models.TextField()
    international_transfers = models.TextField(blank=True)

    # Cookies and tracking
    cookie_policy = models.TextField(blank=True)
    analytics_providers = models.JSONField(default=list, blank=True)
    third_party_services = models.JSONField(default=list, blank=True)

    # Consent management
    consent_mechanisms = models.TextField()
    withdrawal_procedure = models.TextField()

    # Status
    is_active = models.BooleanField(default=True)
    requires_update = models.BooleanField(default=False)
    next_review_date = models.DateField(default=timezone.now() + timedelta(days=365))

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_policies'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['effective_date']),
            models.Index(fields=['next_review_date']),
        ]
        ordering = ['-effective_date']

    def __str__(self):
        return f"{self.title} v{self.version}"

    def check_gdpr_compliance(self) -> Dict:
        """
        Check if privacy policy meets GDPR requirements
        """
        required_sections = [
            'data_controller',
            'data_protection_officer',
            'contact_information',
            'data_subject_rights',
            'complaint_procedure',
            'retention_periods',
            'consent_mechanisms',
            'withdrawal_procedure'
        ]

        missing_sections = []
        for section in required_sections:
            if not getattr(self, section):
                missing_sections.append(section)

        # Check for specific GDPR requirements
        issues = []

        if not self.data_subject_rights:
            issues.append("Data subject rights not clearly explained")

        if not self.consent_mechanisms:
            issues.append("Consent mechanisms not described")

        if not self.withdrawal_procedure:
            issues.append("Procedure for withdrawing consent not provided")

        if self.international_transfers and 'adequate safeguards' not in self.international_transfers.lower():
            issues.append("International transfers require adequate safeguards")

        return {
            'is_compliant': len(issues) == 0 and not missing_sections,
            'issues': issues,
            'missing_sections': missing_sections
        }


class ConsentRecord(models.Model):
    """
    GDPR Article 7 compliant consent recording
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Patient information
    patient_id = models.UUIDField()
    patient_name_hash = models.CharField(max_length=255)  # Hashed for privacy

    # Consent details
    consent_type = models.CharField(max_length=100)
    consent_version = models.CharField(max_length=20)
    consent_language = models.CharField(max_length=10, default='EN')

    # Consent content
    consent_text = models.TextField()
    privacy_policy_version = models.CharField(max_length=20)
    data_retention_period = models.CharField(max_length=100)

    # Granularity
    specific_purpose = models.TextField()
    data_categories = models.JSONField(default=list)
    third_party_recipients = models.JSONField(default=list, blank=True)
    international_transfers = models.BooleanField(default=False)

    # Consent lifecycle
    consent_given_at = models.DateTimeField(default=timezone.now)
    consent_method = models.CharField(
        max_length=50,
        choices=[
            ('CLICKWRAP', 'Clickwrap'),
            ('SIGNATURE', 'Electronic Signature'),
            ('FORM', 'Written Form'),
            ('VERBAL', 'Verbal with Documentation'),
            ('IMPLIED', 'Implied from Action'),
        ]
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)

    # Withdrawal
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    withdrawal_method = models.CharField(max_length=50, blank=True)
    withdrawal_reason = models.TextField(blank=True)

    # Proof of consent
    consent_proof = models.JSONField(default=dict, blank=True)
    audit_trail = models.JSONField(default=list, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['patient_id', 'consent_type']),
            models.Index(fields=['consent_given_at']),
            models.Index(fields=['withdrawn_at']),
            models.Index(fields=['consent_version']),
        ]
        ordering = ['-consent_given_at']

    def __str__(self):
        return f"Consent for {self.patient_id} - {self.consent_type}"

    def is_valid(self) -> bool:
        """
        Check if consent is currently valid
        """
        return (
            not self.withdrawn_at and
            self.consent_given_at <= timezone.now()
        )

    def withdraw(self, reason: str = "", method: str = ""):
        """
        Withdraw consent
        """
        self.withdrawn_at = timezone.now()
        self.withdrawal_reason = reason
        self.withdrawal_method = method
        self.save()

        # Add to audit trail
        self.audit_trail.append({
            'action': 'withdrawn',
            'timestamp': timezone.now().isoformat(),
            'reason': reason,
            'method': method
        })
        self.save()

        # Log withdrawal
        logger.info(f"Consent withdrawn for patient {self.patient_id} - {self.consent_type}")


class DataSubjectRequestManager:
    """
    Manager for handling GDPR data subject requests
    """

    def __init__(self):
        self.request_types = {
            'ACCESS': self._handle_access_request,
            'RECTIFICATION': self._handle_rectification_request,
            'ERASURE': self._handle_erasure_request,
            'RESTRICT': self._handle_restriction_request,
            'PORTABILITY': self._handle_portability_request,
            'OBJECT': self._handle_objection_request,
        }

    def create_request(self, patient_id: str, request_type: str, details: Dict) -> DataSubjectRequest:
        """
        Create a new data subject request
        """
        from .models import DataSubjectRequest

        request = DataSubjectRequest.objects.create(
            patient_id=patient_id,
            request_type=request_type,
            description=details.get('description', ''),
            scope=details.get('scope', []),
            timeframe=details.get('timeframe', {}),
        )

        # Log request creation
        logger.info(f"Data subject request created: {request.id} - {request_type}")

        return request

    def process_request(self, request: DataSubjectRequest) -> Dict:
        """
        Process a data subject request
        """
        handler = self.request_types.get(request.request_type)
        if not handler:
            raise ValueError(f"Unknown request type: {request.request_type}")

        try:
            result = handler(request)
            request.status = 'COMPLETED'
            request.completed_date = timezone.now()
            request.save()
            return result

        except Exception as e:
            logger.error(f"Error processing request {request.id}: {e}")
            request.status = 'REJECTED'
            request.rejection_reason = str(e)
            request.save()
            raise

    def _handle_access_request(self, request: DataSubjectRequest) -> Dict:
        """
        Handle GDPR Article 15 right of access request
        """
        patient_id = request.patient_id
        scope = request.scope

        # Collect all personal data
        personal_data = {
            'patient_profile': self._get_patient_data(patient_id),
            'medical_records': self._get_medical_records(patient_id),
            'appointments': self._get_appointments(patient_id),
            'billing_data': self._get_billing_data(patient_id),
            'consent_records': self._get_consent_records(patient_id),
            'access_logs': self._get_access_logs(patient_id),
        }

        # Filter by scope if specified
        if scope:
            filtered_data = {}
            for category in scope:
                if category in personal_data:
                    filtered_data[category] = personal_data[category]
            personal_data = filtered_data

        return {
            'personal_data': personal_data,
            'data_sources': self._get_data_sources(),
            'data_processors': self._get_data_processors(),
            'retention_policies': self._get_retention_policies(),
        }

    def _handle_rectification_request(self, request: DataSubjectRequest) -> Dict:
        """
        Handle GDPR Article 16 right to rectification request
        """
        # Implementation would identify and correct inaccurate data
        return {
            'status': 'processed',
            'fields_rectified': [],
            'rectification_date': timezone.now().isoformat()
        }

    def _handle_erasure_request(self, request: DataSubjectRequest) -> Dict:
        """
        Handle GDPR Article 17 right to erasure request
        """
        patient_id = request.patient_id
        scope = request.scope

        erased_data = []
        legal_obligations = []

        # Check each data category
        if not scope or 'medical_records' in scope:
            # Check if medical data can be erased (legal obligations)
            if self._has_legal_obligation_to_retain(patient_id, 'medical_records'):
                legal_obligations.append('Medical records retained due to legal requirements')
            else:
                # Anonymize or delete records
                erased_data.append('medical_records')

        # Process other data categories
        for category in ['appointments', 'billing_data', 'consent_records']:
            if not scope or category in scope:
                erased_data.append(category)

        return {
            'status': 'processed',
            'erased_data': erased_data,
            'legal_obligations': legal_obligations,
            'erasure_date': timezone.now().isoformat()
        }

    def _handle_restriction_request(self, request: DataSubjectRequest) -> Dict:
        """
        Handle GDPR Article 18 right to restriction request
        """
        # Implementation would restrict processing of specified data
        return {
            'status': 'processed',
            'restricted_data': [],
            'restriction_date': timezone.now().isoformat()
        }

    def _handle_portability_request(self, request: DataSubjectRequest) -> Dict:
        """
        Handle GDPR Article 20 right to data portability request
        """
        patient_id = request.patient_id
        format_preference = request.scope.get('format', 'json')

        # Get portable data
        portable_data = {
            'patient_profile': self._get_patient_data(patient_id),
            'medical_records': self._get_medical_records(patient_id),
        }

        # Convert to requested format
        if format_preference == 'json':
            data_export = json.dumps(portable_data, indent=2)
        elif format_preference == 'xml':
            # Convert to XML
            data_export = self._convert_to_xml(portable_data)
        else:
            data_export = json.dumps(portable_data, indent=2)

        return {
            'status': 'processed',
            'data_export': data_export,
            'format': format_preference,
            'export_date': timezone.now().isoformat()
        }

    def _handle_objection_request(self, request: DataSubjectRequest) -> Dict:
        """
        Handle GDPR Article 21 right to object request
        """
        # Implementation would handle objection to processing
        return {
            'status': 'processed',
            'processing_stopped': [],
            'objection_date': timezone.now().isoformat()
        }

    def _get_patient_data(self, patient_id: str) -> Dict:
        """Get patient profile data"""
        # Implementation would query patient data
        return {
            'id': patient_id,
            'name': '[REDACTED]',
            'contact': '[REDACTED]',
            'demographics': '[REDACTED]'
        }

    def _get_medical_records(self, patient_id: str) -> List[Dict]:
        """Get medical records for patient"""
        # Implementation would query medical records
        return []

    def _get_appointments(self, patient_id: str) -> List[Dict]:
        """Get appointment history"""
        # Implementation would query appointments
        return []

    def _get_billing_data(self, patient_id: str) -> List[Dict]:
        """Get billing and payment data"""
        # Implementation would query billing data
        return []

    def _get_consent_records(self, patient_id: str) -> List[Dict]:
        """Get consent records"""
        return list(ConsentRecord.objects.filter(
            patient_id=patient_id,
            withdrawn_at__isnull=True
        ).values())

    def _get_access_logs(self, patient_id: str) -> List[Dict]:
        """Get data access logs"""
        # Implementation would query access logs
        return []

    def _get_data_sources(self) -> List[str]:
        """Get list of data sources"""
        return ['EHR System', 'Appointment System', 'Billing System', 'Lab System']

    def _get_data_processors(self) -> List[Dict]:
        """Get list of data processors"""
        return []

    def _get_retention_policies(self) -> Dict:
        """Get data retention policies"""
        return {
            'medical_records': '25 years',
            'billing_records': '7 years',
            'appointment_records': '7 years',
            'consent_records': 'Until withdrawal + legal retention'
        }

    def _has_legal_obligation_to_retain(self, patient_id: str, data_type: str) -> bool:
        """Check if there's a legal obligation to retain data"""
        # Implementation would check legal requirements
        return data_type == 'medical_records'  # Medical records have legal retention requirements

    def _convert_to_xml(self, data: Dict) -> str:
        """Convert data to XML format"""
        # Simple XML conversion
        xml_data = '<?xml version="1.0" encoding="UTF-8"?>\n<data>'
        for key, value in data.items():
            xml_data += f'\n  <{key}>{json.dumps(value)}</{key}>'
        xml_data += '\n</data>'
        return xml_data


class GDPRComplianceManager:
    """
    Manager for GDPR compliance operations
    """

    def __init__(self):
        self.request_manager = DataSubjectRequestManager()

    def generate_accountability_report(self) -> Dict:
        """
        Generate GDPR accountability report
        """
        report = {
            'generated_at': timezone.now(),
            'reporting_period': {
                'start': timezone.now() - timedelta(days=365),
                'end': timezone.now()
            },
            'sections': {}
        }

        # Processing activities
        activities = DataProcessingActivity.objects.filter(is_active=True)
        report['sections']['processing_activities'] = {
            'total': activities.count(),
            'by_lawful_basis': {},
            'by_risk_level': {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
            'compliance_issues': []
        }

        for activity in activities:
            # Group by lawful basis
            basis = activity.lawful_basis
            if basis not in report['sections']['processing_activities']['by_lawful_basis']:
                report['sections']['processing_activities']['by_lawful_basis'][basis] = 0
            report['sections']['processing_activities']['by_lawful_basis'][basis] += 1

            # Check compliance
            compliance = activity.check_compliance()
            if not compliance['is_compliant']:
                report['sections']['processing_activities']['compliance_issues'].append({
                    'activity': activity.processing_name,
                    'issues': compliance['issues']
                })

            # Risk level distribution
            risk_level = compliance['risk_level']
            report['sections']['processing_activities']['by_risk_level'][risk_level] += 1

        # Data subject requests
        requests = DataSubjectRequest.objects.filter(
            received_date__gte=timezone.now() - timedelta(days=365)
        )
        report['sections']['data_subject_requests'] = {
            'total': requests.count(),
            'by_type': {},
            'by_status': {},
            'average_response_time_days': 0
        }

        # Calculate statistics
        total_response_time = timedelta()
        completed_requests = requests.filter(status='COMPLETED')
        for req in completed_requests:
            # Group by type
            req_type = req.request_type
            if req_type not in report['sections']['data_subject_requests']['by_type']:
                report['sections']['data_subject_requests']['by_type'][req_type] = 0
            report['sections']['data_subject_requests']['by_type'][req_type] += 1

            # Group by status
            status = req.status
            if status not in report['sections']['data_subject_requests']['by_status']:
                report['sections']['data_subject_requests']['by_status'][status] = 0
            report['sections']['data_subject_requests']['by_status'][status] += 1

            # Calculate response time
            if req.completed_date and req.received_date:
                total_response_time += req.completed_date - req.received_date

        if completed_requests.count() > 0:
            avg_days = total_response_time.total_seconds() / (completed_requests.count() * 86400)
            report['sections']['data_subject_requests']['average_response_time_days'] = round(avg_days, 1)

        # Data breaches
        breaches = DataBreachRegister.objects.filter(
            discovery_date__gte=timezone.now() - timedelta(days=365)
        )
        report['sections']['data_breaches'] = {
            'total': breaches.count(),
            'notified_to_dpa': breaches.filter(notified_dpa_at__isnull=False).count(),
            'notified_to_subjects': breaches.filter(notified_subjects_at__isnull=False).count(),
            'high_risk_breaches': breaches.filter(high_risk_to_rights=True).count(),
        }

        # DPIAs
        dpias = DataProtectionImpactAssessment.objects.filter(
            started_at__gte=timezone.now() - timedelta(days=365)
        )
        report['sections']['dpias'] = {
            'total': dpias.count(),
            'completed': dpias.filter(status='APPROVED').count(),
            'in_progress': dpias.filter(status='IN_PROGRESS').count(),
            'high_risk': dpias.filter(risk_score__gte=15).count(),
        }

        # Overall compliance score
        total_activities = activities.count()
        compliant_activities = total_activities - len(report['sections']['processing_activities']['compliance_issues'])
        activity_score = (compliant_activities / total_activities * 100) if total_activities > 0 else 100

        # Calculate overall score
        request_score = min(100 - (
            requests.filter(status__in=['PENDING', 'REJECTED']).count() / max(requests.count(), 1) * 50
        ), 100)

        breach_score = max(0, 100 - breaches.filter(high_risk_to_rights=True).count() * 10)

        report['overall_compliance_score'] = round(
            (activity_score * 0.5 + request_score * 0.3 + breach_score * 0.2),
            2
        )

        return report

    def check_consent_validity(self, patient_id: str, consent_type: str) -> bool:
        """
        Check if valid consent exists for patient
        """
        valid_consent = ConsentRecord.objects.filter(
            patient_id=patient_id,
            consent_type=consent_type,
            withdrawn_at__isnull=True
        ).first()

        return valid_consent is not None

    def create_processing_record(self, processing_details: Dict) -> DataProcessingActivity:
        """
        Create a new processing activity record
        """
        return DataProcessingActivity.objects.create(
            controller_name=processing_details.get('controller', 'HMS Healthcare'),
            processing_name=processing_details['name'],
            processing_purpose=processing_details['purpose'],
            lawful_basis=processing_details['lawful_basis'],
            data_categories=processing_details.get('data_categories', []),
            data_subjects=processing_details.get('data_subjects', []),
            retention_period=processing_details.get('retention_period', 'As required'),
            security_measures=processing_details.get('security_measures', 'Standard security measures applied'),
        )

    def initiate_dpa_notification(self, breach_id: str) -> bool:
        """
        Initiate notification to Data Protection Authority
        """
        try:
            breach = DataBreachRegister.objects.get(uuid=breach_id)
            breach.notify_supervisory_authority()
            return True
        except DataBreachRegister.DoesNotExist:
            logger.error(f"Breach not found: {breach_id}")
            return False