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
    def __init__(self):
        self.trust_cache_timeout = 3600  
    def verify_device_trust(
        self, user, device_fingerprint: str, request: HttpRequest
    ) -> Dict:
        from authentication.models import TrustedDevice, DeviceTrustVerification
        try:
            device = TrustedDevice.objects.get(
                user=user, device_fingerprint=device_fingerprint, is_active=True
            )
        except TrustedDevice.DoesNotExist:
            return {
                "trusted": False,
                "trust_score": 0,
                "reason": "Device not recognized",
                "verification_methods": [],
            }
        if device.is_expired():
            return {
                "trusted": False,
                "trust_score": 0,
                "reason": "Device trust expired",
                "verification_methods": [],
            }
        verifications = DeviceTrustVerification.objects.filter(
            user=user, device=device, is_verified=True
        ).exclude(expires_at__lt=timezone.now())
        verification_methods = [v.verification_type for v in verifications]
        trust_score = self._calculate_trust_score(device, verification_methods)
        return {
            "trusted": trust_score >= 70,  
            "trust_score": trust_score,
            "reason": "Device verified" if trust_score >= 70 else "Insufficient trust",
            "verification_methods": verification_methods,
            "device_id": device.id,
        }
    def _calculate_trust_score(self, device, verification_methods: List[str]) -> int:
        score = device.trust_score  
        method_weights = {
            "CERTIFICATE": 20,
            "BIOMETRIC": 25,
            "LOCATION": 10,
            "BEHAVIORAL": 15,
            "NETWORK": 10,
        }
        for method in verification_methods:
            score += method_weights.get(method, 5)
        return min(100, score)
    def add_device_verification(
        self, user, device, verification_type: str, verification_data: Dict
    ) -> bool:
        from authentication.models import DeviceTrustVerification
        verification = DeviceTrustVerification.objects.create(
            user=user,
            device=device,
            verification_type=verification_type,
            verification_data=verification_data,
            is_verified=True,
            verified_at=timezone.now(),
            expires_at=timezone.now() + timedelta(days=90),  
            confidence_score=85,  
            risk_level="LOW",
        )
        device.trust_score = min(100, device.trust_score + 10)
        device.save()
        return True
class ContinuousAuthenticator:
    def __init__(self):
        self.check_interval = 300  
        self.risk_threshold = 70
    def check_continuous_auth(self, user, session, current_data: Dict) -> Dict:
        from authentication.models import ContinuousAuthentication
        try:
            cont_auth = ContinuousAuthentication.objects.get(user=user, session=session)
        except ContinuousAuthentication.DoesNotExist:
            cont_auth = ContinuousAuthentication.objects.create(
                user=user, session=session, baseline_risk_score=10  
            )
        cont_auth.last_check = timezone.now()
        anomalies = cont_auth.check_anomaly(current_data)
        needs_reauth = (
            cont_auth.current_risk_score > self.risk_threshold
            or cont_auth.anomaly_detected
            or cont_auth.requires_reauth
        )
        result = {
            "needs_reauth": needs_reauth,
            "risk_score": cont_auth.current_risk_score,
            "anomalies": anomalies,
            "last_check": cont_auth.last_check,
            "reauth_reason": cont_auth.reauth_reason if needs_reauth else None,
        }
        cont_auth.save()
        return result
    def update_behavior_baseline(self, user, session, behavior_data: Dict):
        from authentication.models import ContinuousAuthentication
        cont_auth, created = ContinuousAuthentication.objects.get_or_create(
            user=user, session=session
        )
        if "keystroke_pattern" in behavior_data:
            cont_auth.keystroke_pattern = behavior_data["keystroke_pattern"]
        if "mouse_movement" in behavior_data:
            cont_auth.mouse_movement = behavior_data["mouse_movement"]
        if "device_orientation" in behavior_data:
            cont_auth.device_orientation = behavior_data["device_orientation"]
        if "network_behavior" in behavior_data:
            cont_auth.network_behavior = behavior_data["network_behavior"]
        cont_auth.current_risk_score = cont_auth.baseline_risk_score
        cont_auth.anomaly_detected = False
        cont_auth.requires_reauth = False
        cont_auth.save()
class MicrosegmentationManager:
    def __init__(self):
        self.segment_cache_timeout = 1800  
    def get_user_segments(self, user) -> List[str]:
        cache_key = f"user_segments_{user.id}"
        segments = cache.get(cache_key)
        if segments is None:
            segments = self._calculate_user_segments(user)
            cache.set(cache_key, segments, self.segment_cache_timeout)
        return segments
    def _calculate_user_segments(self, user) -> List[str]:
        segments = ["public"]  
        role_segments = {
            "SUPER_ADMIN": ["admin", "management", "hr", "finance", "clinical"],
            "HOSPITAL_ADMIN": ["management", "hr", "finance", "clinical"],
            "DOCTOR": ["clinical", "patient_records"],
            "NURSE": ["clinical", "patient_records"],
            "PHARMACIST": ["pharmacy", "clinical"],
            "LAB_TECHNICIAN": ["laboratory", "clinical"],
            "BILLING_CLERK": ["billing", "finance"],
            "RECEPTIONIST": ["reception", "scheduling"],
        }
        if user.role in role_segments:
            segments.extend(role_segments[user.role])
        if hasattr(user, "department") and user.department:
            segments.append(f"dept_{user.department.name.lower()}")
        current_hour = timezone.now().hour
        if 9 <= current_hour <= 17:
            segments.append("business_hours")
        else:
            segments.append("after_hours")
        return list(set(segments))  
    def check_segment_access(self, user, resource: str, action: str) -> bool:
        user_segments = self.get_user_segments(user)
        access_rules = {
            "patient_records": ["clinical", "admin", "management"],
            "billing_data": ["billing", "finance", "admin", "management"],
            "pharmacy_inventory": ["pharmacy", "admin", "management"],
            "lab_results": ["laboratory", "clinical", "admin", "management"],
            "hr_records": ["hr", "admin", "management"],
            "admin_panel": ["admin", "management"],
        }
        required_segments = access_rules.get(resource, ["admin"])
        return any(segment in user_segments for segment in required_segments)
class LeastPrivilegeEnforcer:
    def __init__(self):
        self.policy_cache_timeout = 3600  
    def check_access(
        self, user, resource: str, action: str, context: Dict = None
    ) -> Tuple[bool, str]:
        permissions = self._get_user_permissions(user)
        resource_permission = f"{resource}:{action}"
        if resource_permission not in permissions:
            return False, f"Insufficient permissions for {resource_permission}"
        context_check = self._check_context_restrictions(
            user, resource, action, context
        )
        if not context_check[0]:
            return context_check
        time_check = self._check_time_restrictions(user, resource, action)
        if not time_check[0]:
            return time_check
        return True, "Access granted"
    def _get_user_permissions(self, user) -> List[str]:
        cache_key = f"user_permissions_{user.id}"
        permissions = cache.get(cache_key)
        if permissions is None:
            permissions = self._calculate_user_permissions(user)
            cache.set(cache_key, permissions, self.policy_cache_timeout)
        return permissions
    def _calculate_user_permissions(self, user) -> List[str]:
        permissions = []
        role_permissions = {
            "SUPER_ADMIN": [
                "patients:*",
                "billing:*",
                "pharmacy:*",
                "lab:*",
                "hr:*",
                "admin:*",
                "reports:*",
                "settings:*",
            ],
            "HOSPITAL_ADMIN": [
                "patients:read",
                "patients:write",
                "billing:read",
                "billing:write",
                "pharmacy:read",
                "reports:*",
                "hr:read",
            ],
            "DOCTOR": [
                "patients:read",
                "patients:write",
                "ehr:*",
                "lab:read",
                "pharmacy:read",
            ],
            "NURSE": ["patients:read", "patients:write", "ehr:read", "vitals:*"],
            "PHARMACIST": ["pharmacy:*", "patients:read", "prescriptions:*"],
            "LAB_TECHNICIAN": ["lab:*", "patients:read", "lab_results:*"],
            "BILLING_CLERK": ["billing:*", "patients:read", "insurance:read"],
        }
        if user.role in role_permissions:
            permissions.extend(role_permissions[user.role])
        if hasattr(user, "department") and user.department:
            dept_permissions = self._get_department_permissions(user.department.name)
            permissions.extend(dept_permissions)
        return list(set(permissions))  
    def _get_department_permissions(self, department: str) -> List[str]:
        dept_permissions = {
            "Emergency": ["emergency:*", "triage:*"],
            "Surgery": ["surgery:*", "ot:*"],
            "ICU": ["icu:*", "critical_care:*"],
            "Pediatrics": ["pediatrics:*"],
            "Maternity": ["maternity:*", "obgyn:*"],
        }
        return dept_permissions.get(department, [])
    def _check_context_restrictions(
        self, user, resource: str, action: str, context: Dict
    ) -> Tuple[bool, str]:
        if not context:
            return True, "No context restrictions"
        if context.get("emergency_access", False) and user.role in ["DOCTOR", "NURSE"]:
            return True, "Emergency access granted"
        if resource.startswith("patient") and context.get("patient_id"):
            if not self._check_patient_relationship(user, context["patient_id"]):
                return False, "No relationship with patient"
        return True, "Context check passed"
    def _check_time_restrictions(
        self, user, resource: str, action: str
    ) -> Tuple[bool, str]:
        current_hour = timezone.now().hour
        sensitive_resources = ["billing", "hr", "admin"]
        if any(res in resource for res in sensitive_resources):
            if action in ["write", "delete"] and not (9 <= current_hour <= 17):
                return False, "Sensitive operations restricted to business hours"
        return True, "Time restrictions passed"
    def _check_patient_relationship(self, user, patient_id: int) -> bool:
        return user.role in ["DOCTOR", "NURSE", "SUPER_ADMIN", "HOSPITAL_ADMIN"]
device_verifier = DeviceTrustVerifier()
continuous_auth = ContinuousAuthenticator()
microsegmentation = MicrosegmentationManager()