import logging
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

import pyotp
import qrcode
import redis
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import update_last_login
from django.core.cache import cache
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from .models import DataSubjectRequest
from .services import DataAccessService

User = get_user_model()

logger = logging.getLogger(__name__)


class MultiFactorAuthentication:
    """
    HIPAA compliant Multi-Factor Authentication system
    """

    def __init__(self):
        self.issuer = getattr(settings, 'MFA_ISSUER', 'HMS Enterprise')
        self.token_validity_minutes = getattr(settings, 'MFA_TOKEN_VALIDITY_MINUTES', 5)
        self.max_attempts = getattr(settings, 'MFA_MAX_ATTEMPTS', 5)
        self.lockout_duration_minutes = getattr(settings, 'MFA_LOCKOUT_MINUTES', 30)

    def generate_totp_secret(self, user: User) -> str:
        """
        Generate TOTP secret for user
        """
        return pyotp.random_base32()

    def generate_totp_qr_code(self, user: User, secret: str) -> str:
        """
        Generate QR code for TOTP setup
        """
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=user.email, issuer_name=self.issuer)

        # Generate QR code
        qr_img = qrcode.make(provisioning_uri)
        qr_code_data = qr_img.get_image().tobytes()

        return provisioning_uri

    def verify_totp_token(self, user: User, token: str) -> bool:
        """
        Verify TOTP token for user
        """
        if not user.mfa_secret:
            return False

        # Check rate limiting
        cache_key = f"mfa_attempts_{user.id}"
        attempts = cache.get(cache_key, 0)

        if attempts >= self.max_attempts:
            lockout_key = f"mfa_lockout_{user.id}"
            if cache.get(lockout_key):
                raise AuthenticationFailed("Account temporarily locked due to too many MFA attempts")

        totp = pyotp.TOTP(user.mfa_secret)

        if totp.verify(token, valid_window=1):  # Allow 1 step window for clock drift
            # Reset attempts on successful verification
            cache.delete(cache_key)
            cache.delete(f"mfa_lockout_{user.id}")
            return True
        else:
            # Increment failed attempts
            cache.set(cache_key, attempts + 1, 3600)

            # Lock account if max attempts reached
            if attempts + 1 >= self.max_attempts:
                cache.set(f"mfa_lockout_{user.id}", True, self.lockout_duration_minutes * 60)
                logger.warning(f"MFA account locked for user {user.id}")

            return False

    def generate_backup_codes(self, user: User, count: int = 10) -> list:
        """
        Generate backup codes for MFA recovery
        """
        backup_codes = []
        for _ in range(count):
            code = ''.join(random.choices(string.digits + string.ascii_uppercase, k=8))
            backup_codes.append(code)

        # Store hashed backup codes (in production, use proper hashing)
        user.mfa_backup_codes = backup_codes
        user.save()

        return backup_codes

    def verify_backup_code(self, user: User, code: str) -> bool:
        """
        Verify backup code for MFA recovery
        """
        if not user.mfa_backup_codes:
            return False

        if code in user.mfa_backup_codes:
            # Remove used backup code
            user.mfa_backup_codes.remove(code)
            user.save()
            return True

        return False

    def enforce_mfa_requirement(self, user: User) -> bool:
        """
        Check if user is required to use MFA
        """
        # Require MFA for all users accessing PHI
        if user.has_perm('patients.view_patient'):
            return True

        # Require MFA for administrative users
        if user.is_staff or user.is_superuser:
            return True

        # Require MFA for users with sensitive access
        sensitive_permissions = [
            'billing.view_billing',
            'ehr.view_medicalrecord',
            'pharmacy.view_prescription',
        ]
        return any(user.has_perm(perm) for perm in sensitive_permissions)


class HIPAACompliantJWTAuthentication(JWTAuthentication):
    """
    HIPAA compliant JWT authentication with enhanced security
    """

    def __init__(self):
        super().__init__()
        self.data_access_service = DataAccessService()

    def authenticate(self, request):
        """
        Enhanced authentication with HIPAA compliance checks
        """
        try:
            # Perform standard JWT authentication
            auth_result = super().authenticate(request)

            if not auth_result:
                return None

            user, token = auth_result

            # Enhanced security checks
            if not self._validate_user_security_profile(user, request):
                return None

            if not self._validate_token_security(token, request):
                return None

            if not self._validate_access_compliance(user, request):
                return None

            # Update last login and audit trail
            self._update_security_audit(user, request)

            return user, token

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    def _validate_user_security_profile(self, user: User, request) -> bool:
        """
        Validate user security profile
        """
        # Check if user account is active
        if not user.is_active:
            logger.warning(f"Authentication attempt for inactive user {user.id}")
            return False

        # Check MFA requirement
        mfa_auth = MultiFactorAuthentication()
        if mfa_auth.enforce_mfa_requirement(user) and not user.mfa_enabled:
            logger.warning(f"User {user.id} attempted authentication without required MFA")
            return False

        # Check for any account restrictions
        if getattr(user, 'account_locked', False):
            logger.warning(f"Authentication attempt for locked account {user.id}")
            return False

        # Check password expiration
        if hasattr(user, 'password_last_changed'):
            password_age = timezone.now() - user.password_last_changed
            max_password_age = getattr(settings, 'PASSWORD_MAX_AGE_DAYS', 90)
            if password_age.days > max_password_age:
                logger.warning(f"User {user.id} password expired")
                return False

        return True

    def _validate_token_security(self, token, request) -> bool:
        """
        Validate token security attributes
        """
        # Check token expiration
        if token.get('exp', 0) < timezone.now().timestamp():
            logger.warning("Expired token used for authentication")
            return False

        # Check token issuer
        expected_issuer = getattr(settings, 'JWT_ISSUER', 'HMS')
        if token.get('iss') != expected_issuer:
            logger.warning(f"Invalid token issuer: {token.get('iss')}")
            return False

        # Check token audience
        expected_audience = getattr(settings, 'JWT_AUDIENCE', 'HMS_API')
        if token.get('aud') != expected_audience:
            logger.warning(f"Invalid token audience: {token.get('aud')}")
            return False

        # Check for token revocation
        jti = token.get('jti')
        if jti and self._is_token_revoked(jti):
            logger.warning(f"Revoked token used for authentication: {jti}")
            return False

        return True

    def _validate_access_compliance(self, user: User, request) -> bool:
        """
        Validate access compliance requirements
        """
        # Check if user has completed required compliance training
        if hasattr(user, 'compliance_training_required') and user.compliance_training_required:
            if not hasattr(user, 'compliance_training_completed') or not user.compliance_training_completed:
                logger.warning(f"User {user.id} attempting access without compliance training")
                return False

        # Check if user has accepted HIPAA agreement
        if hasattr(user, 'hipaa_agreement_required') and user.hipaa_agreement_required:
            if not hasattr(user, 'hipaa_agreement_accepted') or not user.hipaa_agreement_accepted:
                logger.warning(f"User {user.id} attempting access without HIPAA agreement")
                return False

        # Check for any access restrictions
        if hasattr(user, 'access_restricted') and user.access_restricted:
            logger.warning(f"User {user.id} has restricted access")
            return False

        return True

    def _update_security_audit(self, user: User, request) -> None:
        """
        Update security audit trail
        """
        from .models import DataSubjectRequest

        # Update last login
        update_last_login(None, user)

        # Log authentication event
        try:
            DataSubjectRequest.objects.create(
                user=user,
                action_type="AUTHENTICATION",
                resource_type="USER_LOGIN",
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                timestamp=timezone.now()
            )
        except Exception as e:
            logger.error(f"Failed to log authentication event: {e}")

        # Update session security
        request.session['last_security_check'] = timezone.now().isoformat()
        request.session['security_level'] = self._determine_security_level(user)

    def _is_token_revoked(self, jti: str) -> bool:
        """
        Check if token has been revoked
        """
        cache_key = f"revoked_token_{jti}"
        return cache.get(cache_key, False)

    def _determine_security_level(self, user: User) -> str:
        """
        Determine user's security level based on role and permissions
        """
        if user.is_superuser:
            return "ADMIN"
        elif user.is_staff:
            return "STAFF"
        elif user.has_perm('patients.view_patient'):
            return "CLINICAL"
        else:
            return "BASIC"

    def _get_client_ip(self, request) -> str:
        """
        Get client IP address with proxy support
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        return ip or '127.0.0.1'


class RoleBasedAccessControl:
    """
    HIPAA compliant Role-Based Access Control (RBAC) system
    """

    def __init__(self):
        self.role_permissions = self._define_role_permissions()
        self.phi_access_matrix = self._define_phi_access_matrix()

    def _define_role_permissions(self) -> Dict[str, Dict]:
        """
        Define HIPAA compliant role permissions
        """
        return {
            'PHYSICIAN': {
                'can_view_own_patients': True,
                'can_modify_own_patients': True,
                'can_view_department_patients': True,
                'can_prescribe_medications': True,
                'can_order_tests': True,
                'can_view_billing': True,
                'can_export_patient_data': True,
            },
            'NURSE': {
                'can_view_assigned_patients': True,
                'can_modify_assigned_patients': True,
                'can_view_department_patients': True,
                'can_administer_medications': True,
                'can_record_vitals': True,
                'can_view_billing': False,
                'can_export_patient_data': False,
            },
            'ADMINISTRATOR': {
                'can_view_all_patients': True,
                'can_modify_patient_records': False,
                'can_view_billing': True,
                'can_process_billing': True,
                'can_export_patient_data': False,
                'can_manage_users': True,
            },
            'BILLING_STAFF': {
                'can_view_patient_billing': True,
                'can_process_claims': True,
                'can_view_demographics': True,
                'can_view_medical_necessity': True,
                'can_export_billing_data': True,
                'can_export_patient_data': False,
            },
            'RECEPTIONIST': {
                'can_view_patient_schedules': True,
                'can_schedule_appointments': True,
                'can_view_demographics': True,
                'can_view_contact_info': True,
                'can_export_patient_data': False,
            },
            'LAB_TECHNICIAN': {
                'can_view_test_orders': True,
                'can_record_test_results': True,
                'can_view_patient_demographics': True,
                'can_export_test_data': True,
                'can_export_patient_data': False,
            },
            'PHARMACIST': {
                'can_view_prescriptions': True,
                'can_dispense_medications': True,
                'can_view_patient_demographics': True,
                'can_view_allergies': True,
                'can_export_medication_data': True,
                'can_export_patient_data': False,
            },
        }

    def _define_phi_access_matrix(self) -> Dict[str, Dict]:
        """
        Define PHI access control matrix
        """
        return {
            'DEMOGRAPHICS': {
                'PHYSICIAN': 'FULL',
                'NURSE': 'FULL',
                'ADMINISTRATOR': 'LIMITED',
                'BILLING_STAFF': 'LIMITED',
                'RECEPTIONIST': 'FULL',
                'LAB_TECHNICIAN': 'LIMITED',
                'PHARMACIST': 'LIMITED',
            },
            'MEDICAL_HISTORY': {
                'PHYSICIAN': 'FULL',
                'NURSE': 'FULL',
                'ADMINISTRATOR': 'NONE',
                'BILLING_STAFF': 'LIMITED',
                'RECEPTIONIST': 'NONE',
                'LAB_TECHNICIAN': 'NONE',
                'PHARMACIST': 'FULL',
            },
            'DIAGNOSES': {
                'PHYSICIAN': 'FULL',
                'NURSE': 'FULL',
                'ADMINISTRATOR': 'NONE',
                'BILLING_STAFF': 'LIMITED',
                'RECEPTIONIST': 'NONE',
                'LAB_TECHNICIAN': 'NONE',
                'PHARMACIST': 'FULL',
            },
            'MEDICATIONS': {
                'PHYSICIAN': 'FULL',
                'NURSE': 'FULL',
                'ADMINISTRATOR': 'NONE',
                'BILLING_STAFF': 'LIMITED',
                'RECEPTIONIST': 'NONE',
                'LAB_TECHNICIAN': 'NONE',
                'PHARMACIST': 'FULL',
            },
            'BILLING_INFORMATION': {
                'PHYSICIAN': 'LIMITED',
                'NURSE': 'NONE',
                'ADMINISTRATOR': 'FULL',
                'BILLING_STAFF': 'FULL',
                'RECEPTIONIST': 'LIMITED',
                'LAB_TECHNICIAN': 'NONE',
                'PHARMACIST': 'NONE',
            },
            'INSURANCE_INFORMATION': {
                'PHYSICIAN': 'LIMITED',
                'NURSE': 'NONE',
                'ADMINISTRATOR': 'FULL',
                'BILLING_STAFF': 'FULL',
                'RECEPTIONIST': 'LIMITED',
                'LAB_TECHNICIAN': 'NONE',
                'PHARMACIST': 'NONE',
            },
        }

    def can_access_phi(self, user: User, patient_id: int, phi_category: str, access_type: str = 'VIEW') -> bool:
        """
        Check if user can access specific PHI category
        """
        # Get user role (implementation depends on user model)
        user_role = self._get_user_role(user)

        if not user_role:
            return False

        # Check role permissions for PHI category
        phi_access = self.phi_access_matrix.get(phi_category, {})
        access_level = phi_access.get(user_role, 'NONE')

        if access_level == 'NONE':
            return False

        # Check specific permissions for access type
        role_permissions = self.role_permissions.get(user_role, {})

        if access_type == 'VIEW':
            return role_permissions.get('can_view_own_patients', False)
        elif access_type == 'MODIFY':
            return role_permissions.get('can_modify_own_patients', False)
        elif access_type == 'EXPORT':
            return role_permissions.get('can_export_patient_data', False)

        return False

    def _get_user_role(self, user: User) -> Optional[str]:
        """
        Get user's role from user model
        """
        # Implementation depends on how roles are stored in user model
        # This is a placeholder implementation
        if hasattr(user, 'role'):
            return user.role

        # Fallback: determine role from user groups/permissions
        if user.is_superuser:
            return 'PHYSICIAN'  # Default for superusers
        elif user.is_staff:
            return 'ADMINISTRATOR'

        return None

    def enforce_minimum_necessary_principle(self, user: User, requested_data: Dict) -> Dict:
        """
        Enforce HIPAA minimum necessary principle
        """
        filtered_data = {}
        user_role = self._get_user_role(user)

        if not user_role:
            return {}

        # Filter data based on user role and permissions
        for data_category, data_value in requested_data.items():
            if self.can_access_phi(user, None, data_category, 'VIEW'):
                filtered_data[data_category] = data_value

        return filtered_data

    def log_phi_access(self, user: User, patient_id: int, phi_category: str,
                      access_type: str, purpose: str, ip_address: str = None) -> bool:
        """
        Log PHI access for audit trail
        """
        try:
            from .models import DataSubjectRequest

            DataSubjectRequest.objects.create(
                user=user,
                patient_id=patient_id,
                action_type=f"PHI_{access_type}",
                resource_type=phi_category,
                ip_address=ip_address or "127.0.0.1",
                timestamp=timezone.now(),
                metadata={
                    'purpose': purpose,
                    'access_type': access_type,
                    'phi_category': phi_category
                }
            )

            return True

        except Exception as e:
            logger.error(f"Failed to log PHI access: {e}")
            return False


class SessionSecurity:
    """
    Enhanced session security for HIPAA compliance
    """

    def __init__(self):
        self.session_timeout_minutes = getattr(settings, 'HIPAA_SESSION_TIMEOUT', 15)
        self.max_concurrent_sessions = getattr(settings, 'MAX_CONCURRENT_SESSIONS', 3)

    def enforce_session_timeout(self, request) -> bool:
        """
        Enforce HIPAA session timeout requirements
        """
        if not request.user.is_authenticated:
            return True

        last_activity = request.session.get('last_activity')
        if not last_activity:
            return True

        last_activity_time = datetime.fromisoformat(last_activity)
        timeout_threshold = timezone.now() - timedelta(minutes=self.session_timeout_minutes)

        if last_activity_time < timeout_threshold:
            logger.warning(f"Session timeout for user {request.user.id}")
            return False

        # Update last activity
        request.session['last_activity'] = timezone.now().isoformat()
        return True

    def enforce_concurrent_session_limit(self, user: User) -> bool:
        """
        Enforce concurrent session limits
        """
        # Implementation should check number of active sessions
        # For now, return True
        return True

    def validate_session_binding(self, request) -> bool:
        """
        Validate session is bound to IP and user agent
        """
        if not request.user.is_authenticated:
            return True

        session_ip = request.session.get('session_ip')
        session_ua = request.session.get('session_ua')

        current_ip = self._get_client_ip(request)
        current_ua = request.META.get('HTTP_USER_AGENT', '')

        if session_ip and session_ip != current_ip:
            logger.warning(f"Session IP mismatch for user {request.user.id}")
            return False

        if session_ua and session_ua != current_ua:
            logger.warning(f"Session user agent mismatch for user {request.user.id}")
            return False

        return True

    def _get_client_ip(self, request) -> str:
        """
        Get client IP address with proxy support
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        return ip or '127.0.0.1'