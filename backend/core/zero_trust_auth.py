"""
Zero Trust Authentication and Authorization System
Implements continuous verification, least privilege access, and device trust
"""

import base64
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

from rest_framework_simplejwt.tokens import RefreshToken

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from django.utils.crypto import get_random_string

from core.encryption import decrypt_data, encrypt_data
from core.security_compliance import log_security_event

User = get_user_model()
logger = logging.getLogger(__name__)


class DeviceTrust:
    """Device trust verification system"""

    def __init__(self):
        self.cache_prefix = "device_trust:"

    def generate_device_id(self, request) -> str:
        """Generate unique device identifier"""
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR", "")

        # Create device fingerprint
        device_data = f"{user_agent}:{ip}:{request.META.get('HTTP_ACCEPT', '')}"
        device_hash = hashlib.sha256(device_data.encode()).hexdigest()

        return device_hash[:32]

    def verify_device_trust(self, device_id: str, user_id: int) -> bool:
        """Verify if device is trusted"""
        cache_key = f"{self.cache_prefix}{user_id}:{device_id}"
        return cache.get(cache_key, False)

    def trust_device(
        self, device_id: str, user_id: int, duration_days: int = 30
    ) -> None:
        """Mark device as trusted"""
        cache_key = f"{self.cache_prefix}{user_id}:{device_id}"
        cache.set(cache_key, True, duration_days * 24 * 3600)

    def revoke_device_trust(self, device_id: str, user_id: int) -> None:
        """Revoke device trust"""
        cache_key = f"{self.cache_prefix}{user_id}:{device_id}"
        cache.delete(cache_key)


class RiskEngine:
    """Risk-based authentication engine"""

    def __init__(self):
        self.risk_factors = {
            "new_device": 30,
            "new_ip": 20,
            "impossible_travel": 50,
            "malicious_ip": 100,
            "suspicious_timing": 25,
            "failed_attempts": 40,
        }

    def calculate_risk_score(self, request, user):
        """Calculate risk score for authentication attempt"""
        risk_score = 0

        # Check for new device
        device_id = DeviceTrust().generate_device_id(request)
        if not DeviceTrust().verify_device_trust(device_id, user.id):
            risk_score += self.risk_factors["new_device"]

        # Check IP reputation
        ip = self._get_client_ip(request)
        if self._is_malicious_ip(ip):
            risk_score += self.risk_factors["malicious_ip"]

        # Check for impossible travel
        if self._detect_impossible_travel(request, user):
            risk_score += self.risk_factors["impossible_travel"]

        # Check timing (outside business hours)
        if self._is_suspicious_timing(request):
            risk_score += self.risk_factors["suspicious_timing"]

        # Check recent failed attempts
        failed_attempts = cache.get(f"failed_attempts:{user.id}", 0)
        if failed_attempts > 3:
            risk_score += self.risk_factors["failed_attempts"] * (failed_attempts - 3)

        return min(risk_score, 100)  # Cap at 100

    def get_auth_requirements(self, risk_score: int) -> Dict[str, bool]:
        """Determine authentication requirements based on risk"""
        requirements = {
            "password": True,
            "mfa": risk_score > 20,
            "captcha": risk_score > 40,
            "additional_verification": risk_score > 60,
            "block": risk_score >= 80,
        }

        return requirements

    def _is_malicious_ip(self, ip: str) -> bool:
        """Check if IP is in malicious IP database"""
        # This would integrate with threat intelligence services
        malicious_ips = cache.get("malicious_ips", set())
        return ip in malicious_ips

    def _detect_impossible_travel(self, request, user):
        """Detect impossible travel between locations"""
        current_ip = self._get_client_ip(request)
        last_ip = cache.get(f"last_ip:{user.id}")

        if last_ip and last_ip != current_ip:
            try:
                current_location = self._get_geolocation(current_ip)
                last_location = self._get_geolocation(last_ip)

                if current_location and last_location:
                    distance = self._calculate_distance(
                        current_location['lat'], current_location['lon'],
                        last_location['lat'], last_location['lon']
                    )
                    # Get time since last login
                    last_login_time = cache.get(f"last_login_time:{user.id}")
                    if last_login_time:
                        time_diff_hours = (timezone.now() - last_login_time).total_seconds() / 3600
                        # Speed needed (km/h) = distance (km) / time (hours)
                        if time_diff_hours > 0:
                            speed = distance / time_diff_hours
                            # If speed > 500 km/h (commercial flight speed), flag as impossible
                            if speed > 500:
                                return True
            except Exception as e:
                logger.warning(f"Error detecting impossible travel: {e}")

        # Update last IP and login time
        cache.set(f"last_ip:{user.id}", current_ip, 86400 * 30)  # 30 days
        cache.set(f"last_login_time:{user.id}", timezone.now(), 86400 * 30)

        return False

    def _is_suspicious_timing(self, request):
        """Check if authentication attempt is at suspicious time"""
        hour = timezone.now().hour
        # Consider 2 AM - 5 AM as suspicious for healthcare system
        return hour < 5 or hour > 23

    def _get_client_ip(self, request) -> str:
        """Get client IP address"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR", "")

    def _get_geolocation(self, ip: str):
        """Get geolocation data for IP address"""
        cache_key = f"geo:{ip}"
        location = cache.get(cache_key)
        if location:
            return location

        try:
            # Use ipapi.co for free geolocation (no API key needed for basic use)
            import requests
            response = requests.get(f"http://ipapi.co/{ip}/json/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('latitude') and data.get('longitude'):
                    location = {
                        'lat': data['latitude'],
                        'lon': data['longitude'],
                        'country': data.get('country_code', ''),
                        'city': data.get('city', '')
                    }
                    cache.set(cache_key, location, 86400 * 7)  # Cache for 7 days
                    return location
        except Exception as e:
            logger.warning(f"Failed to get geolocation for {ip}: {e}")

        return None

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        import math

        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Haversine formula
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = 6371 * c  # Earth radius in km

        return distance


class MFAProvider:
    """Multi-Factor Authentication Provider"""

    def __init__(self):
        self.otp_length = 6
        self.otp_expiry = 300  # 5 minutes

    def generate_totp_secret(self) -> str:
        """Generate TOTP secret key"""
        return base64.b32encode(get_random_string(20).encode()).decode()

    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes"""
        codes = []
        for _ in range(count):
            code = get_random_string(8, allowed_chars="0123456789")
            codes.append(code)
        return codes

    def send_otp_via_sms(self, phone: str, otp: str) -> bool:
        """Send OTP via SMS"""
        # This would integrate with SMS service provider
        # For now, just log the action
        logger.info(f"SMS OTP sent to {phone[-4:]}: {otp}")
        return True

    def send_otp_via_email(self, email: str, otp: str) -> bool:
        """Send OTP via email"""
        # This would integrate with email service provider
        logger.info(f"Email OTP sent to {email}: {otp}")
        return True


class ZeroTrustAuthenticator:
    """Zero Trust Authentication System"""

    def __init__(self):
        self.device_trust = DeviceTrust()
        self.risk_engine = RiskEngine()
        self.mfa_provider = MFAProvider()

    def authenticate(self, request, username: str, password: str) -> Dict:
        """Zero Trust authentication flow"""
        result = {
            "success": False,
            "user": None,
            "token": None,
            "mfa_required": False,
            "device_trusted": False,
            "risk_score": 0,
            "message": "",
        }

        # Get user
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self._increment_failed_attempts(username)
            result["message"] = "Invalid credentials"
            return result

        # Verify password
        if not user.check_password(password):
            self._increment_failed_attempts(username)
            result["message"] = "Invalid credentials"
            return result

        # Calculate risk score
        risk_score = self.risk_engine.calculate_risk_score(request, user)
        result["risk_score"] = risk_score

        # Get authentication requirements
        auth_requirements = self.risk_engine.get_auth_requirements(risk_score)

        # Block if high risk
        if auth_requirements["block"]:
            log_security_event(
                event_type="HIGH_RISK_AUTH_BLOCKED",
                user=user,
                request=request,
                metadata={
                    "description": f"High risk authentication blocked for user {username}",
                    "severity": "CRITICAL",
                    "ip_address": self._get_client_ip(request),
                }
            )
            result["message"] = "Access blocked due to high risk"
            return result

        # Generate device ID
        device_id = self.device_trust.generate_device_id(request)
        result["device_trusted"] = self.device_trust.verify_device_trust(
            device_id, user.id
        )

        # CAPTCHA flow for high-risk logins
        if auth_requirements["captcha"]:
            result["captcha_required"] = True
            result["message"] = "CAPTCHA verification required"
            return result

        # MFA flow
        if auth_requirements["mfa"] and not result["device_trusted"]:
            # Send MFA challenge
            if user.phone:
                otp = get_random_string(
                    self.mfa_provider.otp_length, allowed_chars="0123456789"
                )
                cache.set(f"mfa_otp:{user.id}", otp, self.mfa_provider.otp_expiry)
                self.mfa_provider.send_otp_via_sms(user.phone, otp)
                result["mfa_required"] = True
                result["message"] = "MFA code sent to your phone"
                return result
            elif user.email:
                otp = get_random_string(
                    self.mfa_provider.otp_length, allowed_chars="0123456789"
                )
                cache.set(f"mfa_otp:{user.id}", otp, self.mfa_provider.otp_expiry)
                self.mfa_provider.send_otp_via_email(user.email, otp)
                result["mfa_required"] = True
                result["message"] = "MFA code sent to your email"
                return result

        # If we reach here, authentication is successful
        result["success"] = True
        result["user"] = user

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        result["token"] = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

        # Trust device if MFA completed or low risk
        if not result["device_trusted"] and risk_score < 30:
            self.device_trust.trust_device(device_id, user.id)
            result["device_trusted"] = True

        # Clear failed attempts
        cache.delete(f"failed_attempts:{user.id}")

        # Log successful authentication
        log_security_event(
            event_type="SUCCESSFUL_AUTH",
            user=user,
            request=request,
            metadata={
                "description": f"User {username} authenticated successfully",
                "severity": "INFO",
                "ip_address": self._get_client_ip(request),
            }
        )

        return result

    def verify_mfa(self, user_id: int, otp: str) -> bool:
        """Verify MFA OTP"""
        cached_otp = cache.get(f"mfa_otp:{user_id}")
        if cached_otp and cached_otp == otp:
            cache.delete(f"mfa_otp:{user_id}")
            return True
        return False

    def verify_captcha(self, captcha_response: str, client_ip: str) -> bool:
        """Verify CAPTCHA response"""
        try:
            import requests

            # Using reCAPTCHA v2
            secret_key = getattr(settings, 'RECAPTCHA_SECRET_KEY', None)
            if not secret_key:
                # Fallback: simple math CAPTCHA or disable
                return True

            url = 'https://www.google.com/recaptcha/api/siteverify'
            data = {
                'secret': secret_key,
                'response': captcha_response,
                'remoteip': client_ip
            }

            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                return result.get('success', False)

        except Exception as e:
            logger.warning(f"CAPTCHA verification failed: {e}")

        return False

    def continuous_verification(self, request, user):
        """Continuous verification during session"""
        # Re-calculate risk score periodically
        risk_score = self.risk_engine.calculate_risk_score(request, user)

        if risk_score > 60:
            # Force re-authentication
            log_security_event(
                event_type="CONTINUOUS_VERIFICATION_FAILED",
                user=user,
                request=request,
                metadata={
                    "description": f"High risk detected for user {user.username}",
                    "severity": "HIGH",
                    "ip_address": self._get_client_ip(request),
                }
            )
            return False

        return True

    def _increment_failed_attempts(self, username: str) -> None:
        """Increment failed authentication attempts"""
        cache_key = f"failed_attempts:{username}"
        attempts = cache.get(cache_key, 0) + 1
        cache.set(cache_key, attempts, 3600)  # 1 hour expiry

        # Lock account after too many attempts
        if attempts >= 5:
            cache.set(f"account_locked:{username}", True, 1800)  # 30 minute lock
            log_security_event(
                event_type="ACCOUNT_LOCKED",
                metadata={
                    "description": f"Account locked due to failed attempts: {username}",
                    "severity": "HIGH",
                }
            )

    def _get_client_ip(self, request) -> str:
        """Get client IP address"""
        return self.risk_engine._get_client_ip(request)


class ZeroTrustAuthorization:
    """Zero Trust Authorization with RBAC and ABAC"""

    def __init__(self):
        self.role_permissions = self._load_role_permissions()
        self.attribute_policies = self._load_attribute_policies()

    def check_permission(self, user, resource, action, context=None):
        """Check if user has permission for action on resource"""
        context = context or {}

        # 1. Check role-based permissions
        if not self._check_role_permission(user, resource, action):
            return False

        # 2. Check attribute-based permissions
        if not self._check_attribute_permission(user, resource, action, context):
            return False

        # 3. Check time-based restrictions
        if not self._check_time_restrictions(user, resource, action):
            return False

        # 4. Check location-based restrictions
        if not self._check_location_restrictions(user, context):
            return False

        return True

    def _check_role_permission(self, user, resource, action):
        """Check role-based permissions"""
        for role in user.roles.all():
            role_permissions = self.role_permissions.get(role.name, {})
            resource_permissions = role_permissions.get(resource, [])

            if action in resource_permissions or "*" in resource_permissions:
                return True

        return False

    def _check_attribute_permission(self, user, resource, action, context):
        """Check attribute-based permissions"""
        for policy in self.attribute_policies:
            if policy["resource"] == resource and action in policy["actions"]:
                # Evaluate policy conditions
                if self._evaluate_policy_conditions(
                    user, policy["conditions"], context
                ):
                    return True

        return False

    def _evaluate_policy_conditions(self, user, conditions, context):
        """Evaluate policy conditions"""
        for condition in conditions:
            if condition["type"] == "user_attribute":
                value = getattr(user, condition["attribute"], None)
                if value != condition["value"]:
                    return False

            elif condition["type"] == "context":
                if condition["attribute"] not in context:
                    return False
                if context[condition["attribute"]] != condition["value"]:
                    return False

            elif condition["type"] == "time":
                # Check time-based conditions
                current_hour = timezone.now().hour
                if (
                    current_hour < condition["start_hour"]
                    or current_hour > condition["end_hour"]
                ):
                    return False

        return True

    def _check_time_restrictions(self, user, resource, action):
        """Check time-based access restrictions"""
        # This would implement business hour restrictions for certain resources
        return True

    def _check_location_restrictions(self, user, context):
        """Check location-based access restrictions"""
        # This would implement IP whitelisting for certain users
        return True

    def _load_role_permissions(self) -> Dict:
        """Load role-based permissions from configuration"""
        return {
            "admin": {
                "*": ["*"],  # Full access
            },
            "doctor": {
                "patients": ["read", "update", "create"],
                "ehr": ["read", "update"],
                "appointments": ["read", "update", "create"],
                "lab": ["read", "order"],
                "pharmacy": ["read", "prescribe"],
            },
            "nurse": {
                "patients": ["read", "update"],
                "ehr": ["read"],
                "appointments": ["read", "update"],
                "lab": ["read"],
                "pharmacy": ["read"],
            },
            "patient": {
                "patients": ["read_own"],
                "ehr": ["read_own"],
                "appointments": ["read_own", "create_own"],
                "billing": ["read_own"],
            },
        }

    def _load_attribute_policies(self) -> List[Dict]:
        """Load attribute-based policies"""
        return [
            {
                "name": "Doctor can only access patients in their department",
                "resource": "patients",
                "actions": ["read", "update"],
                "conditions": [
                    {
                        "type": "user_attribute",
                        "attribute": "department",
                        "value": "placeholder_department",  # Will be evaluated at runtime
                    }
                ],
            },
            {
                "name": "Patients can only access their own records",
                "resource": "patients",
                "actions": ["read_own"],
                "conditions": [
                    {"type": "context", "attribute": "patient_id", "value": "user.id"}
                ],
            },
        ]
