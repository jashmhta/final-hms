import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest
from django.utils import timezone

from .anomaly_detection import ml_detector, behavior_analytics

logger = logging.getLogger(__name__)


class DeviceTrustVerifier:
    """Device trust verification for zero-trust architecture"""

    def __init__(self):
        self.trust_cache_timeout = 3600  # 1 hour

    def verify_device_trust(self, user, device_fingerprint: str, request: HttpRequest) -> Dict:
        """Verify device trust level"""
        from authentication.models import TrustedDevice, DeviceTrustVerification

        try:
            device = TrustedDevice.objects.get(
                user=user,
                device_fingerprint=device_fingerprint,
                is_active=True
            )
        except TrustedDevice.DoesNotExist:
            return {
                'trusted': False,
                'trust_score': 0,
                'reason': 'Device not recognized',
                'verification_methods': []
            }

        # Check if trust is expired
        if device.is_expired():
            return {
                'trusted': False,
                'trust_score': 0,
                'reason': 'Device trust expired',
                'verification_methods': []
            }

        # Get verification methods
        verifications = DeviceTrustVerification.objects.filter(
            user=user,
            device=device,
            is_verified=True
        ).exclude(expires_at__lt=timezone.now())

        verification_methods = [v.verification_type for v in verifications]

        # Calculate trust score
        trust_score = self._calculate_trust_score(device, verification_methods)

        return {
            'trusted': trust_score >= 70,  # 70% threshold for trust
            'trust_score': trust_score,
            'reason': 'Device verified' if trust_score >= 70 else 'Insufficient trust',
            'verification_methods': verification_methods,
            'device_id': device.id
        }

    def _calculate_trust_score(self, device, verification_methods: List[str]) -> int:
        """Calculate device trust score"""
        score = device.trust_score  # Base score from device

        # Bonus for verification methods
        method_weights = {
            'CERTIFICATE': 20,
            'BIOMETRIC': 25,
            'LOCATION': 10,
            'BEHAVIORAL': 15,
            'NETWORK': 10
        }

        for method in verification_methods:
            score += method_weights.get(method, 5)

        return min(100, score)

    def add_device_verification(self, user, device, verification_type: str, verification_data: Dict) -> bool:
        """Add device verification method"""
        from authentication.models import DeviceTrustVerification

        verification = DeviceTrustVerification.objects.create(
            user=user,
            device=device,
            verification_type=verification_type,
            verification_data=verification_data,
            is_verified=True,
            verified_at=timezone.now(),
            expires_at=timezone.now() + timedelta(days=90),  # 90 days validity
            confidence_score=85,  # High confidence for new verifications
            risk_level='LOW'
        )

        # Update device trust score
        device.trust_score = min(100, device.trust_score + 10)
        device.save()

        return True


class ContinuousAuthenticator:
    """Continuous authentication monitoring"""

    def __init__(self):
        self.check_interval = 300  # 5 minutes
        self.risk_threshold = 70

    def check_continuous_auth(self, user, session, current_data: Dict) -> Dict:
        """Check continuous authentication status"""
        from authentication.models import ContinuousAuthentication

        try:
            cont_auth = ContinuousAuthentication.objects.get(
                user=user,
                session=session
            )
        except ContinuousAuthentication.DoesNotExist:
            # Create new continuous auth record
            cont_auth = ContinuousAuthentication.objects.create(
                user=user,
                session=session,
                baseline_risk_score=10  # Low baseline
            )

        # Update with current data
        cont_auth.last_check = timezone.now()

        # Check for anomalies
        anomalies = cont_auth.check_anomaly(current_data)

        # Determine if re-authentication is needed
        needs_reauth = (
            cont_auth.current_risk_score > self.risk_threshold or
            cont_auth.anomaly_detected or
            cont_auth.requires_reauth
        )

        result = {
            'needs_reauth': needs_reauth,
            'risk_score': cont_auth.current_risk_score,
            'anomalies': anomalies,
            'last_check': cont_auth.last_check,
            'reauth_reason': cont_auth.reauth_reason if needs_reauth else None
        }

        cont_auth.save()
        return result

    def update_behavior_baseline(self, user, session, behavior_data: Dict):
        """Update user's behavior baseline"""
        from authentication.models import ContinuousAuthentication

        cont_auth, created = ContinuousAuthentication.objects.get_or_create(
            user=user,
            session=session
        )

        # Update behavior patterns
        if 'keystroke_pattern' in behavior_data:
            cont_auth.keystroke_pattern = behavior_data['keystroke_pattern']

        if 'mouse_movement' in behavior_data:
            cont_auth.mouse_movement = behavior_data['mouse_movement']

        if 'device_orientation' in behavior_data:
            cont_auth.device_orientation = behavior_data['device_orientation']

        if 'network_behavior' in behavior_data:
            cont_auth.network_behavior = behavior_data['network_behavior']

        # Reset risk scores
        cont_auth.current_risk_score = cont_auth.baseline_risk_score
        cont_auth.anomaly_detected = False
        cont_auth.requires_reauth = False

        cont_auth.save()


class MicrosegmentationManager:
    """Network microsegmentation management"""

    def __init__(self):
        self.segment_cache_timeout = 1800  # 30 minutes

    def get_user_segments(self, user) -> List[str]:
        """Get user's network segments based on role and context"""
        cache_key = f"user_segments_{user.id}"
        segments = cache.get(cache_key)

        if segments is None:
            segments = self._calculate_user_segments(user)
            cache.set(cache_key, segments, self.segment_cache_timeout)

        return segments

    def _calculate_user_segments(self, user) -> List[str]:
        """Calculate network segments for user"""
        segments = ['public']  # Everyone gets public access

        # Role-based segments
        role_segments = {
            'SUPER_ADMIN': ['admin', 'management', 'hr', 'finance', 'clinical'],
            'HOSPITAL_ADMIN': ['management', 'hr', 'finance', 'clinical'],
            'DOCTOR': ['clinical', 'patient_records'],
            'NURSE': ['clinical', 'patient_records'],
            'PHARMACIST': ['pharmacy', 'clinical'],
            'LAB_TECHNICIAN': ['laboratory', 'clinical'],
            'BILLING_CLERK': ['billing', 'finance'],
            'RECEPTIONIST': ['reception', 'scheduling'],
        }

        if user.role in role_segments:
            segments.extend(role_segments[user.role])

        # Department-based segments
        if hasattr(user, 'department') and user.department:
            segments.append(f"dept_{user.department.name.lower()}")

        # Context-based segments (time/location based)
        current_hour = timezone.now().hour
        if 9 <= current_hour <= 17:
            segments.append('business_hours')
        else:
            segments.append('after_hours')

        return list(set(segments))  # Remove duplicates

    def check_segment_access(self, user, resource: str, action: str) -> bool:
        """Check if user has access to resource in their segments"""
        user_segments = self.get_user_segments(user)

        # Define resource access rules
        access_rules = {
            'patient_records': ['clinical', 'admin', 'management'],
            'billing_data': ['billing', 'finance', 'admin', 'management'],
            'pharmacy_inventory': ['pharmacy', 'admin', 'management'],
            'lab_results': ['laboratory', 'clinical', 'admin', 'management'],
            'hr_records': ['hr', 'admin', 'management'],
            'admin_panel': ['admin', 'management'],
        }

        required_segments = access_rules.get(resource, ['admin'])

        # Check if user has any required segment
        return any(segment in user_segments for segment in required_segments)


class LeastPrivilegeEnforcer:
    """Least privilege access control enforcement"""

    def __init__(self):
        self.policy_cache_timeout = 3600  # 1 hour

    def check_access(self, user, resource: str, action: str, context: Dict = None) -> Tuple[bool, str]:
        """Check if user has least privilege access to resource"""
        # Get user's effective permissions
        permissions = self._get_user_permissions(user)

        # Check resource-specific permissions
        resource_permission = f"{resource}:{action}"
        if resource_permission not in permissions:
            return False, f"Insufficient permissions for {resource_permission}"

        # Check context-based restrictions
        context_check = self._check_context_restrictions(user, resource, action, context)
        if not context_check[0]:
            return context_check

        # Check time-based restrictions
        time_check = self._check_time_restrictions(user, resource, action)
        if not time_check[0]:
            return time_check

        return True, "Access granted"

    def _get_user_permissions(self, user) -> List[str]:
        """Get user's effective permissions"""
        cache_key = f"user_permissions_{user.id}"
        permissions = cache.get(cache_key)

        if permissions is None:
            permissions = self._calculate_user_permissions(user)
            cache.set(cache_key, permissions, self.policy_cache_timeout)

        return permissions

    def _calculate_user_permissions(self, user) -> List[str]:
        """Calculate user's permissions based on role and attributes"""
        permissions = []

        # Base permissions by role
        role_permissions = {
            'SUPER_ADMIN': [
                'patients:*', 'billing:*', 'pharmacy:*', 'lab:*', 'hr:*',
                'admin:*', 'reports:*', 'settings:*'
            ],
            'HOSPITAL_ADMIN': [
                'patients:read', 'patients:write', 'billing:read', 'billing:write',
                'pharmacy:read', 'reports:*', 'hr:read'
            ],
            'DOCTOR': [
                'patients:read', 'patients:write', 'ehr:*', 'lab:read', 'pharmacy:read'
            ],
            'NURSE': [
                'patients:read', 'patients:write', 'ehr:read', 'vitals:*'
            ],
            'PHARMACIST': [
                'pharmacy:*', 'patients:read', 'prescriptions:*'
            ],
            'LAB_TECHNICIAN': [
                'lab:*', 'patients:read', 'lab_results:*'
            ],
            'BILLING_CLERK': [
                'billing:*', 'patients:read', 'insurance:read'
            ],
        }

        if user.role in role_permissions:
            permissions.extend(role_permissions[user.role])

        # Add department-specific permissions
        if hasattr(user, 'department') and user.department:
            dept_permissions = self._get_department_permissions(user.department.name)
            permissions.extend(dept_permissions)

        return list(set(permissions))  # Remove duplicates

    def _get_department_permissions(self, department: str) -> List[str]:
        """Get department-specific permissions"""
        dept_permissions = {
            'Emergency': ['emergency:*', 'triage:*'],
            'Surgery': ['surgery:*', 'ot:*'],
            'ICU': ['icu:*', 'critical_care:*'],
            'Pediatrics': ['pediatrics:*'],
            'Maternity': ['maternity:*', 'obgyn:*'],
        }

        return dept_permissions.get(department, [])

    def _check_context_restrictions(self, user, resource: str, action: str, context: Dict) -> Tuple[bool, str]:
        """Check context-based access restrictions"""
        if not context:
            return True, "No context restrictions"

        # Emergency access override
        if context.get('emergency_access', False) and user.role in ['DOCTOR', 'NURSE']:
            return True, "Emergency access granted"

        # Patient relationship check
        if resource.startswith('patient') and context.get('patient_id'):
            if not self._check_patient_relationship(user, context['patient_id']):
                return False, "No relationship with patient"

        return True, "Context check passed"

    def _check_time_restrictions(self, user, resource: str, action: str) -> Tuple[bool, str]:
        """Check time-based access restrictions"""
        current_hour = timezone.now().hour

        # Restrict sensitive operations to business hours
        sensitive_resources = ['billing', 'hr', 'admin']
        if any(res in resource for res in sensitive_resources):
            if action in ['write', 'delete'] and not (9 <= current_hour <= 17):
                return False, "Sensitive operations restricted to business hours"

        return True, "Time restrictions passed"

    def _check_patient_relationship(self, user, patient_id: int) -> bool:
        """Check if user has legitimate relationship with patient"""
        # This would check if user is assigned to patient, is their doctor, etc.
        # For now, return True for doctors and nurses
        return user.role in ['DOCTOR', 'NURSE', 'SUPER_ADMIN', 'HOSPITAL_ADMIN']


# Global instances
device_verifier = DeviceTrustVerifier()
continuous_auth = ContinuousAuthenticator()
microsegmentation = MicrosegmentationManager()
least_privilege = LeastPrivilegeEnforcer()</content>
