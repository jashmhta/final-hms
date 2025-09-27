"""
middleware module
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

from .models import AccessPurpose, DataAccessType
from .services import AuditTrailService, DataAccessService

User = get_user_model()

logger = logging.getLogger(__name__)


class HIPAASecurityMiddleware(MiddlewareMixin):
    """
    HIPAA compliant security middleware for data protection
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        self.data_access_service = DataAccessService()
        self.audit_service = AuditTrailService()

        # Security configurations
        self.max_phi_requests_per_minute = getattr(
            settings, "HIPAA_MAX_REQUESTS_PER_MINUTE", 100
        )
        self.session_timeout_minutes = getattr(settings, "HIPAA_SESSION_TIMEOUT", 15)
        self.blocked_countries = getattr(settings, "HIPAA_BLOCKED_COUNTRIES", [])
        self.required_headers = getattr(
            settings,
            "HIPAA_REQUIRED_HEADERS",
            ["X-Content-Type-Options", "X-Frame-Options", "X-XSS-Protection"],
        )

        # PHI data patterns for detection
        self.phi_patterns = [
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
            r"\b\d{10}\b",  # Phone number
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
            r"\b\d{2}/\d{2}/\d{4}\b",  # Date
            r"\b\d{3}-\d{3}-\d{4}\b",  # US Phone
        ]

    def process_request(self, request):
        """
        Process incoming requests for HIPAA compliance
        """
        # Security header validation
        if not self._validate_security_headers(request):
            return self._security_violation_response(
                "Missing required security headers"
            )

        # Geographic restriction check
        if not self._check_geographic_restriction(request):
            return self._security_violation_response(
                "Access restricted from this location"
            )

        # Session timeout validation
        if not self._validate_session_timeout(request):
            return self._security_violation_response("Session expired")

        # PHI detection in request data
        phi_detected = self._detect_phi_in_request(request)
        if phi_detected:
            self._log_phi_detection(request, phi_detected)

        # Rate limiting
        if not self._check_rate_limit(request):
            return self._security_violation_response("Rate limit exceeded")

        # Request validation
        if not self._validate_request_structure(request):
            return self._security_violation_response("Invalid request structure")

        return None

    def process_response(self, request, response):
        """
        Process outgoing responses for HIPAA compliance
        """
        # Add security headers
        response = self._add_security_headers(response)

        # PHI detection in response data
        if hasattr(response, "data"):
            phi_in_response = self._detect_phi_in_data(response.data)
            if phi_in_response:
                logger.warning(
                    f"PHI detected in response for {request.path}: {phi_in_response}"
                )
                self._audit_service.log_system_event(
                    "PHI_LEAK_DETECTED",
                    f"PHI found in response: {request.path}",
                    request.user if request.user.is_authenticated else None,
                    self._get_client_ip(request),
                    {"phi_detected": phi_in_response},
                )

        # Response logging for audit trail
        self._log_response_access(request, response)

        return response

    def process_exception(self, request, exception):
        """
        Handle exceptions with HIPAA compliance in mind
        """
        # Log security exceptions
        self._audit_service.log_system_event(
            "SECURITY_EXCEPTION",
            f"Exception occurred: {str(exception)}",
            request.user if request.user.is_authenticated else None,
            self._get_client_ip(request),
            {"exception_type": type(exception).__name__},
        )

        # Never expose sensitive information in error responses
        return JsonResponse(
            {
                "error": "An internal error occurred",
                "error_code": "INTERNAL_ERROR",
                "timestamp": timezone.now().isoformat(),
            },
            status=500,
        )

    def _validate_security_headers(self, request) -> bool:
        """
        Validate required security headers
        """
        for header in self.required_headers:
            if header not in request.headers:
                logger.warning(f"Missing security header: {header}")
                return False
        return True

    def _check_geographic_restriction(self, request) -> bool:
        """
        Check if request is from allowed geographic location
        """
        if not self.blocked_countries:
            return True

        client_ip = self._get_client_ip(request)
        # Implementation should use IP geolocation service
        # For now, assume allowed
        return True

    def _validate_session_timeout(self, request) -> bool:
        """
        Validate session timeout requirements
        """
        if not request.user.is_authenticated:
            return True

        last_activity = request.session.get("last_activity")
        if not last_activity:
            return True

        last_activity_time = datetime.fromisoformat(last_activity)
        timeout_threshold = timezone.now() - timedelta(
            minutes=self.session_timeout_minutes
        )

        if last_activity_time < timeout_threshold:
            logger.warning(f"Session timeout for user {request.user.id}")
            return False

        # Update last activity
        request.session["last_activity"] = timezone.now().isoformat()
        return True

    def _detect_phi_in_request(self, request) -> List[str]:
        """
        Detect potential PHI in incoming request data
        """
        detected_phi = []

        # Check GET parameters
        for key, value in request.GET.items():
            if isinstance(value, str):
                for pattern in self.phi_patterns:
                    if re.search(pattern, value):
                        detected_phi.append(f"GET parameter '{key}': {value[:50]}...")

        # Check POST data
        if hasattr(request, "POST"):
            for key, value in request.POST.items():
                if isinstance(value, str):
                    for pattern in self.phi_patterns:
                        if re.search(pattern, value):
                            detected_phi.append(
                                f"POST parameter '{key}': {value[:50]}..."
                            )

        # Check JSON body
        if hasattr(request, "body") and request.body:
            try:
                import json

                body_str = request.body.decode("utf-8")
                for pattern in self.phi_patterns:
                    if re.search(pattern, body_str):
                        detected_phi.append("Request body contains potential PHI")
            except:
                pass

        return detected_phi

    def _detect_phi_in_data(self, data) -> List[str]:
        """
        Detect potential PHI in response data
        """
        detected_phi = []

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    for pattern in self.phi_patterns:
                        if re.search(pattern, value):
                            detected_phi.append(f"Field '{key}' contains potential PHI")
                elif isinstance(value, (dict, list)):
                    detected_phi.extend(self._detect_phi_in_data(value))
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    detected_phi.extend(self._detect_phi_in_data(item))

        return detected_phi

    def _check_rate_limit(self, request) -> bool:
        """
        Implement rate limiting for PHI access
        """
        if not request.user.is_authenticated:
            return True

        cache_key = f"hipaa_rate_limit_{request.user.id}"
        current_minute = timezone.now().replace(second=0, microsecond=0)
        request_count = cache.get(f"{cache_key}_{current_minute}", 0)

        if request_count >= self.max_phi_requests_per_minute:
            logger.warning(f"Rate limit exceeded for user {request.user.id}")
            return False

        cache.set(f"{cache_key}_{current_minute}", request_count + 1, 60)
        return True

    def _validate_request_structure(self, request) -> bool:
        """
        Validate request structure for security
        """
        # Check for potential SQL injection in query parameters
        for key, value in request.GET.items():
            if isinstance(value, str):
                sql_injection_patterns = [
                    r"(?i)\b(select|insert|update|delete|drop|create|alter|union)\b",
                    r"(?i)\b(or|and)\s+\d+\s*=\s*\d+",
                    r"(?i)(\b;|\b--)",
                    r"(?i)\b(exec|execute|sp_)\b",
                ]
                for pattern in sql_injection_patterns:
                    if re.search(pattern, value):
                        logger.warning(
                            f"Potential SQL injection in parameter '{key}': {value}"
                        )
                        return False

        # Check for XSS patterns
        for key, value in request.GET.items():
            if isinstance(value, str):
                xss_patterns = [
                    r"<script.*?>.*?</script>",
                    r"javascript:",
                    r"on\w+\s*=",
                    r"<iframe.*?>",
                    r"<object.*?>",
                ]
                for pattern in xss_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        logger.warning(f"Potential XSS in parameter '{key}': {value}")
                        return False

        return True

    def _add_security_headers(self, response):
        """
        Add HIPAA compliant security headers
        """
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'"
        )
        response["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"

        return response

    def _log_response_access(self, request, response) -> None:
        """
        Log response access for audit trail
        """
        if not request.user.is_authenticated:
            return

        # Extract patient ID from request if applicable
        patient_id = self._extract_patient_id_from_request(request)
        if patient_id:
            access_type = self._determine_access_type(request.method, request.path)
            purpose = self._determine_access_purpose(request.path)

            self.data_access_service.log_data_access(
                user=request.user,
                patient_id=patient_id,
                access_type=access_type,
                purpose=purpose,
                resource_type="API_RESPONSE",
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )

    def _extract_patient_id_from_request(self, request) -> Optional[int]:
        """
        Extract patient ID from request path
        """
        import re

        path_patterns = [
            r"/api/patients/(\d+)/",
            r"/api/ehr/patients/(\d+)/",
            r"/api/appointments/patients/(\d+)/",
            r"/api/medications/patients/(\d+)/",
        ]

        for pattern in path_patterns:
            match = re.search(pattern, request.path)
            if match:
                return int(match.group(1))

        return None

    def _determine_access_type(self, method: str, path: str) -> DataAccessType:
        """
        Determine access type based on request method and path
        """
        if method == "GET":
            return DataAccessType.VIEW
        elif method in ["POST", "PUT", "PATCH"]:
            return DataAccessType.MODIFY
        elif method == "DELETE":
            return DataAccessType.DELETE
        else:
            return DataAccessType.VIEW

    def _determine_access_purpose(self, path: str) -> AccessPurpose:
        """
        Determine access purpose based on request path
        """
        if "/billing/" in path:
            return AccessPurpose.PAYMENT
        elif "/ehr/" in path or "/medical/" in path:
            return AccessPurpose.TREATMENT
        elif "/appointments/" in path:
            return AccessPurpose.TREATMENT
        elif "/admin/" in path:
            return AccessPurpose.HEALTHCARE_OPERATIONS
        else:
            return AccessPurpose.TREATMENT

    def _get_client_ip(self, request) -> str:
        """
        Get client IP address with proxy support
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")

        return ip or "127.0.0.1"

    def _log_phi_detection(self, request, detected_phi: List[str]) -> None:
        """
        Log PHI detection for security monitoring
        """
        self._audit_service.log_system_event(
            "PHI_DETECTED",
            f"PHI detected in request: {request.path}",
            request.user if request.user.is_authenticated else None,
            self._get_client_ip(request),
            {
                "detected_phi": detected_phi,
                "request_method": request.method,
                "request_path": request.path,
            },
        )

    def _security_violation_response(self, message: str) -> JsonResponse:
        """
        Return standardized security violation response
        """
        return JsonResponse(
            {
                "error": "Security violation",
                "error_code": "SECURITY_VIOLATION",
                "message": message,
                "timestamp": timezone.now().isoformat(),
            },
            status=403,
        )


class DataLeakPreventionMiddleware(MiddlewareMixin):
    """
    Advanced Data Loss Prevention middleware for healthcare data
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        self.sensitive_data_patterns = [
            # SSN patterns
            r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
            # Credit card patterns
            r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            # Medical record numbers
            r"\b(?:MRN|Medical Record)\s*[:#]?\s*\w+\b",
            # Patient identifiers
            r"\bPatient\s+ID\s*[:#]?\s*\w+\b",
            # Insurance numbers
            r"\b(?:Policy|Insurance)\s+Number\s*[:#]?\s*\w+\b",
        ]

    def process_response(self, request, response):
        """
        Scan response for potential data leaks
        """
        if hasattr(response, "content"):
            content = response.content.decode("utf-8", errors="ignore")
            detected_leaks = self._scan_for_data_leaks(content)

            if detected_leaks:
                logger.warning(f"Data leak prevention triggered for {request.path}")
                self._handle_data_leak(request, response, detected_leaks)

        return response

    def _scan_for_data_leaks(self, content: str) -> List[Dict]:
        """
        Scan content for potential data leaks
        """
        leaks = []

        for pattern in self.sensitive_data_patterns:
            import re

            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                leaks.append(
                    {
                        "pattern": pattern,
                        "match": match.group(),
                        "position": match.start(),
                        "severity": "HIGH",
                    }
                )

        return leaks

    def _handle_data_leak(self, request, response, leaks: List[Dict]) -> None:
        """
        Handle detected data leaks
        """
        # Log the security incident
        self._audit_service.log_system_event(
            "DATA_LEAK_DETECTED",
            f"Potential data leak in response: {request.path}",
            request.user if request.user.is_authenticated else None,
            self._get_client_ip(request),
            {
                "leaks": leaks,
                "request_method": request.method,
                "request_path": request.path,
            },
        )

        # In production, this should trigger immediate alerts
        # and potentially block the response
        logger.error(f"CRITICAL: Data leak detected in response for {request.path}")


class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Enhanced session security for healthcare applications
    """

    def process_request(self, request):
        """
        Validate session security
        """
        if not request.user.is_authenticated:
            return None

        # Check session binding to IP and user agent
        if not self._validate_session_binding(request):
            self._handle_session_hijack(request)
            return None

        # Check concurrent sessions
        if not self._validate_concurrent_sessions(request):
            self._handle_concurrent_session(request)
            return None

        return None

    def _validate_session_binding(self, request) -> bool:
        """
        Validate session is bound to original IP and user agent
        """
        session_ip = request.session.get("session_ip")
        session_ua = request.session.get("session_ua")

        current_ip = self._get_client_ip(request)
        current_ua = request.META.get("HTTP_USER_AGENT", "")

        if session_ip and session_ip != current_ip:
            logger.warning(
                f"Session IP mismatch for user {request.user.id}: {session_ip} vs {current_ip}"
            )
            return False

        if session_ua and session_ua != current_ua:
            logger.warning(f"Session user agent mismatch for user {request.user.id}")
            return False

        # Bind session to current IP and UA if not already bound
        if not session_ip:
            request.session["session_ip"] = current_ip
        if not session_ua:
            request.session["session_ua"] = current_ua

        return True

    def _validate_concurrent_sessions(self, request) -> bool:
        """
        Validate concurrent session limits
        """
        max_concurrent_sessions = getattr(settings, "MAX_CONCURRENT_SESSIONS", 3)

        # Implementation should check number of active sessions for user
        # For now, assume valid
        return True

    def _handle_session_hijack(self, request) -> None:
        """
        Handle potential session hijacking
        """
        logger.error(f"Potential session hijack detected for user {request.user.id}")

        # Terminate current session
        from django.contrib.auth import logout

        logout(request)

        # Log security incident
        self._audit_service.log_system_event(
            "SESSION_HIJACK_DETECTED",
            f"Session hijacking attempt for user {request.user.id}",
            request.user,
            self._get_client_ip(request),
        )

    def _handle_concurrent_session(self, request) -> None:
        """
        Handle concurrent session violations
        """
        logger.warning(f"Concurrent session limit exceeded for user {request.user.id}")

        # Log security incident
        self._audit_service.log_system_event(
            "CONCURRENT_SESSION_VIOLATION",
            f"Concurrent session limit exceeded for user {request.user.id}",
            request.user,
            self._get_client_ip(request),
        )

    def _get_client_ip(self, request) -> str:
        """
        Get client IP address with proxy support
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")

        return ip or "127.0.0.1"
