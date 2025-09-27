"""
services module
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Union
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.utils.crypto import get_random_string

from .models import (
    AccessPurpose,
    ConsentManagement,
    DataAccessType,
    DataRetentionPolicy,
    DataSubjectRequest,
)

User = get_user_model()

logger = logging.getLogger(__name__)


class DataAccessService:
    """
    HIPAA compliant data access monitoring and control
    """

    def __init__(self):
        self.cache_timeout = 3600  # 1 hour cache for access patterns

    def can_access_phi(
        self, user: User, patient_id: int, access_type: DataAccessType
    ) -> bool:
        """
        Check if user has appropriate authorization to access PHI
        """
        # Check if user has required role
        if not self._has_sufficient_role(user, access_type):
            return False

        # Check patient assignment/relationship
        if not self._has_patient_relationship(user, patient_id):
            return False

        # Check if consent exists and is valid
        if not self._has_valid_consent(patient_id):
            return False

        # Check for any access restrictions
        if self._is_access_restricted(user, patient_id):
            return False

        return True

    def log_data_access(
        self,
        user: User,
        patient_id: int,
        access_type: DataAccessType,
        purpose: AccessPurpose,
        resource_type: str,
        resource_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
    ) -> bool:
        """
        Log all PHI access for HIPAA compliance
        """
        try:
            from .models import DataSubjectRequest

            # Create access log entry
            access_log = DataSubjectRequest.objects.create(
                user=user,
                patient_id=patient_id,
                access_type=access_type,
                purpose=purpose,
                resource_type=resource_type,
                resource_id=resource_id or "",
                ip_address=ip_address or "127.0.0.1",
                user_agent=user_agent or "",
                timestamp=timezone.now(),
            )

            # Update access patterns cache
            self._update_access_patterns(user.id, patient_id, access_type)

            # Check for suspicious access patterns
            if self._detect_suspicious_access(user.id, patient_id):
                self._trigger_security_alert(user.id, patient_id, access_type)

            return True

        except Exception as e:
            logger.error(f"Failed to log data access: {e}")
            return False

    def get_patient_data_summary(
        self, patient_id: int, scope: List[str] = None
    ) -> Dict:
        """
        Get comprehensive summary of patient data (GDPR Article 15)
        """
        try:
            summary = {
                "personal_information": self._get_personal_info_summary(patient_id),
                "medical_records": self._get_medical_records_summary(patient_id),
                "appointments": self._get_appointments_summary(patient_id),
            }

            if scope:
                # Filter by requested scope
                filtered_summary = {}
                for category in scope:
                    if category in summary:
                        filtered_summary[category] = summary[category]
                return filtered_summary

            return summary

        except Exception as e:
            logger.error(f"Error getting patient data summary: {e}")
            raise

    def get_data_sources(self) -> List[Dict]:
        """
        Get list of all systems storing patient data
        """
        return [
            {"name": "Patient Records", "type": "PHI Storage", "encrypted": True},
            {"name": "EHR System", "type": "Medical Records", "encrypted": True},
            {"name": "Appointment System", "type": "Scheduling", "encrypted": True},
            {"name": "Billing System", "type": "Financial", "encrypted": True},
            {"name": "Laboratory System", "type": "Test Results", "encrypted": True},
            {"name": "Pharmacy System", "type": "Medications", "encrypted": True},
        ]

    def get_data_processors(self) -> List[Dict]:
        """
        Get list of third-party data processors (GDPR Article 30)
        """
        return [
            {
                "name": "Medical Laboratory Services",
                "purpose": "Laboratory test processing",
                "data_categories": ["Test Results", "Patient Demographics"],
                "retention_period": "7 years",
            },
            {
                "name": "Radiology Imaging Centers",
                "purpose": "Medical imaging services",
                "data_categories": ["Medical Images", "Patient Demographics"],
                "retention_period": "10 years",
            },
            {
                "name": "Insurance Companies",
                "purpose": "Claims processing and payment",
                "data_categories": ["Treatment Records", "Billing Information"],
                "retention_period": "7 years",
            },
        ]

    def get_retention_policies(self) -> List[Dict]:
        """
        Get current data retention policies
        """
        return [
            {
                "data_type": "Adult Medical Records",
                "retention_period": "7 years after last visit",
                "legal_basis": "HIPAA minimum requirement",
            },
            {
                "data_type": "Minor Medical Records",
                "retention_period": "7 years after age of majority",
                "legal_basis": "State law requirements",
            },
            {
                "data_type": "Billing Records",
                "retention_period": "7 years",
                "legal_basis": "HIPAA and tax requirements",
            },
            {
                "data_type": "Immunization Records",
                "retention_period": "Permanent",
                "legal_basis": "Public health requirements",
            },
        ]

    def _has_sufficient_role(self, user: User, access_type: DataAccessType) -> bool:
        """
        Check if user role allows requested access type
        """
        # Implementation depends on user roles and permissions system
        # This is a placeholder for role-based access control
        return True

    def _has_patient_relationship(self, user: User, patient_id: int) -> bool:
        """
        Check if user has legitimate relationship with patient
        """
        # Check if user is assigned to patient's care team
        # This should be implemented based on hospital staffing model
        return True

    def _has_valid_consent(self, patient_id: int) -> bool:
        """
        Check if patient has valid consent for treatment
        """
        active_consents = ConsentManagement.get_active_consents(patient_id)
        treatment_consent = active_consents.filter(
            consent_type=ConsentManagement.ConsentType.GENERAL_TREATMENT
        ).exists()
        return treatment_consent

    def _is_access_restricted(self, user: User, patient_id: int) -> bool:
        """
        Check if there are any access restrictions
        """
        # Check for VIP status, mental health restrictions, etc.
        return False

    def _update_access_patterns(
        self, user_id: int, patient_id: int, access_type: str
    ) -> None:
        """
        Update user access pattern cache for anomaly detection
        """
        cache_key = f"access_pattern_{user_id}_{patient_id}"
        pattern_data = cache.get(cache_key, [])

        pattern_data.append(
            {"timestamp": timezone.now().isoformat(), "access_type": access_type}
        )

        # Keep last 100 accesses
        if len(pattern_data) > 100:
            pattern_data = pattern_data[-100:]

        cache.set(cache_key, pattern_data, self.cache_timeout)

    def _detect_suspicious_access(self, user_id: int, patient_id: int) -> bool:
        """
        Detect suspicious access patterns
        """
        cache_key = f"access_pattern_{user_id}_{patient_id}"
        pattern_data = cache.get(cache_key, [])

        if len(pattern_data) < 3:
            return False

        # Check for rapid successive accesses
        recent_accesses = [
            p
            for p in pattern_data
            if (timezone.now() - datetime.fromisoformat(p["timestamp"])).total_seconds()
            < 300
        ]

        if len(recent_accesses) > 10:  # More than 10 accesses in 5 minutes
            return True

        # Check for unusual access patterns
        # Add more sophisticated anomaly detection here

        return False

    def _trigger_security_alert(
        self, user_id: int, patient_id: int, access_type: str
    ) -> None:
        """
        Trigger security alert for suspicious activity
        """
        # Implementation should send alerts to security team
        logger.warning(
            f"Security alert: Suspicious access by user {user_id} to patient {patient_id} ({access_type})"
        )

    def _get_personal_info_summary(self, patient_id: int) -> Dict:
        """Get summary of personal information"""
        # Implementation should query patient demographics
        return {
            "data_categories": [
                "Personal Identifiers",
                "Contact Information",
                "Demographics",
            ],
            "last_updated": timezone.now().date().isoformat(),
            "encrypted": True,
        }

    def _get_medical_records_summary(self, patient_id: int) -> Dict:
        """Get summary of medical records"""
        return {
            "data_categories": [
                "Diagnoses",
                "Medications",
                "Procedures",
                "Lab Results",
            ],
            "record_count": 0,  # Should query actual count
            "last_updated": timezone.now().date().isoformat(),
            "encrypted": True,
        }

    def _get_appointments_summary(self, patient_id: int) -> Dict:
        """Get summary of appointment data"""
        return {
            "data_categories": ["Appointments", "Visit Notes", "Referrals"],
            "appointment_count": 0,  # Should query actual count
            "last_appointment": None,  # Should query last appointment
            "encrypted": True,
        }


class DataErasureService:
    """
    GDPR Article 17 compliant data erasure service
    """

    def __init__(self):
        self.legal_obligation_fields = [
            "created_at",
            "updated_at",
            "deleted_at",
            "audit_trail",
        ]

    def erase_patient_data(
        self,
        patient_id: int,
        scope: List[str] = None,
        preserve_legal_obligations: bool = True,
    ) -> bool:
        """
        Securely erase patient data while maintaining legal obligations
        """
        try:
            with transaction.atomic():
                # Erase personal identifiable information
                self._erase_personal_data(patient_id, scope, preserve_legal_obligations)

                # Erase medical records (if not required for legal retention)
                self._erase_medical_data(patient_id, scope, preserve_legal_obligations)

                # Erase billing information
                self._erase_billing_data(patient_id, scope, preserve_legal_obligations)

                # Log erasure action
                self._log_erasure_action(patient_id, scope)

                return True

        except Exception as e:
            logger.error(f"Error erasing patient {patient_id} data: {e}")
            return False

    def anonymize_patient_data(self, patient_id: int) -> bool:
        """
        Anonymize patient data for research purposes while preserving statistical value
        """
        try:
            with transaction.atomic():
                # Replace identifiers with anonymous codes
                self._replace_identifiers(patient_id)

                # Aggregate or remove sensitive free-text fields
                self._anonymize_free_text(patient_id)

                # Preserve only essential medical information
                self._preserve_medical_essentials(patient_id)

                # Log anonymization
                self._log_anonymization_action(patient_id)

                return True

        except Exception as e:
            logger.error(f"Error anonymizing patient {patient_id} data: {e}")
            return False

    def _erase_personal_data(
        self, patient_id: int, scope: List[str], preserve_legal_obligations: bool
    ) -> None:
        """
        Erase personal identifiable information
        """
        from patients.models import Patient

        patient = Patient.objects.get(id=patient_id)

        if not scope or "personal_info" in scope:
            # Clear sensitive fields but preserve legal requirement fields
            patient.first_name = "ERASED"
            patient.last_name = "ERASED"
            patient.phone_primary = ""
            patient.phone_secondary = ""
            patient.email = ""
            patient.address_line1 = ""
            patient.address_line2 = ""
            patient.save()

    def _erase_medical_data(
        self, patient_id: int, scope: List[str], preserve_legal_obligations: bool
    ) -> None:
        """
        Erase medical records considering retention requirements
        """
        # Implementation should handle different medical record types
        # based on retention policies and legal requirements
        pass

    def _erase_billing_data(
        self, patient_id: int, scope: List[str], preserve_legal_obligations: bool
    ) -> None:
        """
        Erase billing information while preserving tax/legal requirements
        """
        # Implementation should handle billing data erasure
        # considering financial record retention requirements
        pass

    def _replace_identifiers(self, patient_id: int) -> None:
        """
        Replace patient identifiers with anonymous codes
        """
        from patients.models import Patient

        patient = Patient.objects.get(id=patient_id)
        patient.medical_record_number = f"ANON_{uuid4().hex[:8]}"
        patient.save()

    def _anonymize_free_text(self, patient_id: int) -> None:
        """
        Anonymize free-text fields containing sensitive information
        """
        # Implementation should use NLP techniques to identify and remove PHI
        pass

    def _preserve_medical_essentials(self, patient_id: int) -> None:
        """
        Preserve essential medical information required for care continuity
        """
        # Implementation should preserve diagnoses, allergies, medications
        # but remove identifying information
        pass

    def _log_erasure_action(self, patient_id: int, scope: List[str]) -> None:
        """
        Log data erasure for audit purposes
        """
        logger.info(f"Data erasure completed for patient {patient_id}, scope: {scope}")

    def _log_anonymization_action(self, patient_id: int) -> None:
        """
        Log data anonymization for audit purposes
        """
        logger.info(f"Data anonymization completed for patient {patient_id}")


class AuditTrailService:
    """
    Comprehensive audit trail service for HIPAA compliance
    """

    def __init__(self):
        self.audit_cache_timeout = 86400  # 24 hours

    def log_system_event(
        self,
        event_type: str,
        description: str,
        user: User = None,
        ip_address: str = None,
        metadata: Dict = None,
    ) -> bool:
        """
        Log system-wide security events
        """
        try:
            from .models import SystemAuditLog

            SystemAuditLog.objects.create(
                event_type=event_type,
                description=description,
                user=user,
                ip_address=ip_address or "127.0.0.1",
                timestamp=timezone.now(),
                metadata=metadata or {},
            )

            return True

        except Exception as e:
            logger.error(f"Failed to log system event: {e}")
            return False

    def get_access_logs(
        self,
        patient_id: int,
        start_date: datetime = None,
        end_date: datetime = None,
        user_id: int = None,
    ) -> List[Dict]:
        """
        Get PHI access logs for a patient
        """
        # Implementation should query audit logs
        return []

    def get_user_activity_summary(self, user_id: int, days: int = 30) -> Dict:
        """
        Get summary of user activity for compliance monitoring
        """
        start_date = timezone.now() - timedelta(days=days)

        # Implementation should aggregate user activity data
        return {
            "total_accesses": 0,
            "unique_patients_accessed": 0,
            "access_types": {},
            "unusual_activity_flags": [],
        }

    def generate_compliance_report(
        self, start_date: datetime, end_date: datetime
    ) -> Dict:
        """
        Generate comprehensive compliance report
        """
        return {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "summary": {
                "total_phi_accesses": 0,
                "unique_users": 0,
                "consent_requests": 0,
                "data_erasure_requests": 0,
                "security_incidents": 0,
            },
            "recommendations": [],
        }


class DataRetentionService:
    """
    Automated data retention and disposal service
    """

    def __init__(self):
        self.retention_policies = {
            DataRetentionPolicy.RETAIN_1_YEAR: timedelta(days=365),
            DataRetentionPolicy.RETAIN_2_YEARS: timedelta(days=730),
            DataRetentionPolicy.RETAIN_5_YEARS: timedelta(days=1825),
            DataRetentionPolicy.RETAIN_7_YEARS: timedelta(days=2555),
            DataRetentionPolicy.RETAIN_10_YEARS: timedelta(days=3650),
            DataRetentionPolicy.RETAIN_20_YEARS: timedelta(days=7300),
        }

    def apply_retention_policies(self, dry_run: bool = False) -> Dict:
        """
        Apply data retention policies across all patient data
        """
        results = {
            "records_processed": 0,
            "records_deleted": 0,
            "records_anonymized": 0,
            "errors": [],
        }

        try:
            # Get patients with expired retention periods
            expired_patients = self._get_expired_records()

            for patient in expired_patients:
                try:
                    if dry_run:
                        results["records_processed"] += 1
                        results["records_deleted"] += 1
                    else:
                        if self._should_erase_patient(patient):
                            if self._erase_patient_record(patient):
                                results["records_deleted"] += 1
                        else:
                            if self._anonymize_patient_record(patient):
                                results["records_anonymized"] += 1

                        results["records_processed"] += 1

                except Exception as e:
                    results["errors"].append(
                        {"patient_id": patient.id, "error": str(e)}
                    )

            return results

        except Exception as e:
            logger.error(f"Error applying retention policies: {e}")
            results["errors"].append({"general": str(e)})
            return results

    def _get_expired_records(self):
        """
        Get patient records that have exceeded retention periods
        """
        # Implementation should query for expired records
        # based on retention policies and last activity dates
        return []

    def _should_erase_patient(self, patient) -> bool:
        """
        Determine if patient record should be erased or anonymized
        """
        # Check if there are legal requirements to retain data
        return False

    def _erase_patient_record(self, patient) -> bool:
        """
        Securely erase patient record
        """
        erasure_service = DataErasureService()
        return erasure_service.erase_patient_data(patient.id)

    def _anonymize_patient_record(self, patient) -> bool:
        """
        Anonymize patient record for research/statistical purposes
        """
        erasure_service = DataErasureService()
        return erasure_service.anonymize_patient_data(patient.id)
