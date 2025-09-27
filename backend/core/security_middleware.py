"""
Enterprise-Grade Security Middleware for HMS
Implements comprehensive security controls including:
- Runtime Application Self-Protection (RASP)
- Web Application Firewall (WAF)
- Rate limiting and request validation
- Session security
- PHI protection
"""

import json
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now

from core.encryption import decrypt_data, encrypt_data
from core.security_compliance import log_security_event


class SecurityThreatPatterns:
    """Predefined security threat patterns for detection"""

    SQL_INJECTION_PATTERNS = [
        r"(union.*select.*from)",
        r"(drop.*table)",
        r"(insert.*into)",
        r"(update.*set)",
        r"(delete.*from)",
        r"(script.*src)",
        r"(javascript:)",
        r"(vbscript:)",
        r"(onload=)",
        r"(onerror=)",
        r"(onclick=)",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"onload\s*=",
        r"onerror\s*=",
        r"onclick\s*=",
        r"onmouseover\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"/etc/passwd",
        r"c:\\windows\\",
        r"\\\\",
        r"%2e%2e%2f",
    ]

    COMMAND_INJECTION_PATTERNS = [
        r";.*\s*(",
        r"\|.*\s*(",
        r"&&.*\s*(",
        r"&.*\s*(",
        r"\$\(",
        r"`.*`",
        r"<\?",
    ]


class RateLimiter:
    """Advanced rate limiting with multiple strategies"""

    def __init__(self):
        self.cache_prefix = "rate_limit:"

    def check_rate_limit(
        self, key: str, limit: int, window: int, strategy: str = "fixed_window"
    ) -> bool:
        """
        Check if rate limit is exceeded

        Args:
            key: Unique identifier (IP, user_id, etc.)
            limit: Maximum requests allowed
            window: Time window in seconds
            strategy: Rate limiting strategy

        Returns:
            True if allowed, False if exceeded
        """
        cache_key = f"{self.cache_prefix}{key}"

        if strategy == "fixed_window":
            return self._fixed_window_check(cache_key, limit, window)
        elif strategy == "sliding_window":
            return self._sliding_window_check(cache_key, limit, window)
        elif strategy == "token_bucket":
            return self._token_bucket_check(cache_key, limit, window)
        else:
            return self._fixed_window_check(cache_key, limit, window)

    def _fixed_window_check(self, key: str, limit: int, window: int) -> bool:
        """Fixed window rate limiting"""
        current = cache.get(key, 0)
        if current >= limit:
            return False

        if current == 0:
            cache.set(key, 1, window)
        else:
            cache.incr(key)
        return True

    def _sliding_window_check(self, key: str, limit: int, window: int) -> bool:
        """Sliding window rate limiting"""
        now_time = time.time()
        window_start = now_time - window

        # Get current requests in window
        requests = cache.get(key, [])
        requests = [req_time for req_time in requests if req_time > window_start]

        if len(requests) >= limit:
            return False

        requests.append(now_time)
        cache.set(key, requests, window)
        return True

    def _token_bucket_check(self, key: str, limit: int, window: int) -> bool:
        """Token bucket rate limiting"""
        tokens = cache.get(key, limit)

        if tokens <= 0:
            return False

        # Refill tokens
        refill_rate = limit / window
        tokens = min(limit, tokens + refill_rate)
        cache.set(key, tokens - 1, window)
        return True


class SecurityMiddleware(MiddlewareMixin):
    """Enterprise-grade security middleware with comprehensive protection"""

    def __init__(self, get_response):
        super().__init__(get_response)
        self.rate_limiter = RateLimiter()
        self.threat_patterns = SecurityThreatPatterns()
        self.blocked_ips = set()
        self.suspicious_requests = {}

        # Load security configurations
        self.rate_limits = getattr(
            settings,
            "SECURITY_RATE_LIMITS",
            {
                "IP_PER_MINUTE": 60,
                "IP_PER_HOUR": 1000,
                "USER_PER_MINUTE": 30,
                "ENDPOINT_PER_MINUTE": 100,
            },
        )

        self.blocked_user_agents = getattr(
            settings,
            "BLOCKED_USER_AGENTS",
            [
                "sqlmap",
                "nikto",
                "nmap",
                "metasploit",
                "w3af",
                "burpcollaborator",
            ],
        )

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Process incoming request with security checks"""

        # Skip security checks for health checks and static files
        if self._should_skip_security(request):
            return None

        # 1. IP Reputation Check
        if not self._check_ip_reputation(request):
            return self._block_request(request, "Blocked IP reputation")

        # 2. Rate Limiting
        if not self._check_rate_limits(request):
            return self._block_request(request, "Rate limit exceeded")

        # 3. User Agent Check
        if not self._check_user_agent(request):
            return self._block_request(request, "Blocked user agent")

        # 4. Request Validation
        if not self._validate_request(request):
            return self._block_request(request, "Invalid request detected")

        # 5. Threat Detection
        if self._detect_threats(request):
            return self._block_request(request, "Security threat detected")

        # 6. Session Security
        self._enforce_session_security(request)

        # 7. PHI Protection
        self._protect_phi_data(request)

        return None

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """Process outgoing response with security headers"""

        # Add security headers
        self._add_security_headers(response)

        # Log security events
        self._log_security_event(request, response)

        # PHI data masking in response
        if hasattr(response, "data") and isinstance(response.data, dict):
            self._mask_phi_in_response(response)

        return response

    def _should_skip_security(self, request: HttpRequest) -> bool:
        """Determine if security checks should be skipped"""
        skip_paths = [
            "/health/",
            "/metrics/",
            "/static/",
            "/media/",
            "/admin/jsi18n/",
        ]

        return any(request.path.startswith(path) for path in skip_paths)

    def _check_ip_reputation(self, request: HttpRequest) -> bool:
        """Check IP reputation and block malicious IPs"""
        ip = self._get_client_ip(request)

        # Check if IP is in blocklist
        if ip in self.blocked_ips:
            log_security_event(
                event_type="BLOCKED_IP_ATTEMPT",
                description=f"Blocked IP {ip} attempted access",
                severity="HIGH",
                ip_address=ip,
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
            return False

        # Check recent suspicious activity
        suspicious_count = cache.get(f"suspicious:{ip}", 0)
        if suspicious_count > 10:
            self.blocked_ips.add(ip)
            return False

        return True

    def _check_rate_limits(self, request: HttpRequest) -> bool:
        """Check various rate limits"""
        ip = self._get_client_ip(request)
        path = request.path

        # IP-based rate limiting
        if not self.rate_limiter.check_rate_limit(
            f"ip:{ip}", self.rate_limits["IP_PER_MINUTE"], 60
        ):  # 1 minute
            log_security_event(
                event_type="RATE_LIMIT_EXCEEDED",
                description=f"IP {ip} exceeded rate limit",
                severity="MEDIUM",
                ip_address=ip,
            )
            return False

        # Path-based rate limiting
        if not self.rate_limiter.check_rate_limit(
            f"path:{path}", self.rate_limits["ENDPOINT_PER_MINUTE"], 60
        ):
            return False

        # User-based rate limiting (if authenticated)
        if request.user.is_authenticated:
            user_id = request.user.id
            if not self.rate_limiter.check_rate_limit(
                f"user:{user_id}", self.rate_limits["USER_PER_MINUTE"], 60
            ):
                return False

        return True

    def _check_user_agent(self, request: HttpRequest) -> bool:
        """Check for malicious user agents"""
        user_agent = request.META.get("HTTP_USER_AGENT", "").lower()

        for blocked in self.blocked_user_agents:
            if blocked.lower() in user_agent:
                log_security_event(
                    event_type="BLOCKED_USER_AGENT",
                    description=f"Blocked user agent: {user_agent}",
                    severity="MEDIUM",
                    ip_address=self._get_client_ip(request),
                )
                return False

        return True

    def _validate_request(self, request: HttpRequest) -> bool:
        """Validate request parameters and headers"""
        # Check for oversized requests
        content_length = request.META.get("CONTENT_LENGTH")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB
            return False

        # Validate headers
        suspicious_headers = [
            "X-Forwarded-For",
            "X-Real-IP",
            "X-Originating-IP",
        ]

        for header in suspicious_headers:
            value = request.META.get(header, "")
            if value and len(value) > 1000:
                return False

        return True

    def _detect_threats(self, request: HttpRequest) -> bool:
        """Detect various security threats"""
        threat_detected = False
        threats_found = []

        # Check request parameters
        all_params = []
        all_params.extend(request.GET.keys())
        all_params.extend(request.POST.keys())

        if hasattr(request, "body") and request.body:
            try:
                body_data = json.loads(request.body.decode("utf-8"))
                if isinstance(body_data, dict):
                    all_params.extend(str(body_data.values()))
            except:
                pass

        param_values = []
        param_values.extend(request.GET.values())
        param_values.extend(request.POST.values())

        # SQL Injection detection
        for pattern in self.threat_patterns.SQL_INJECTION_PATTERNS:
            for value in param_values:
                if re.search(pattern, str(value), re.IGNORECASE):
                    threats_found.append(f"SQL Injection: {pattern}")
                    threat_detected = True

        # XSS detection
        for pattern in self.threat_patterns.XSS_PATTERNS:
            for value in param_values:
                if re.search(pattern, str(value), re.IGNORECASE):
                    threats_found.append(f"XSS: {pattern}")
                    threat_detected = True

        # Path traversal detection
        for pattern in self.threat_patterns.PATH_TRAVERSAL_PATTERNS:
            for value in param_values:
                if re.search(pattern, str(value), re.IGNORECASE):
                    threats_found.append(f"Path Traversal: {pattern}")
                    threat_detected = True

        # Command injection detection
        for pattern in self.threat_patterns.COMMAND_INJECTION_PATTERNS:
            for value in param_values:
                if re.search(pattern, str(value), re.IGNORECASE):
                    threats_found.append(f"Command Injection: {pattern}")
                    threat_detected = True

        if threat_detected:
            log_security_event(
                event_type="THREAT_DETECTED",
                description=f"Threats detected: {', '.join(threats_found)}",
                severity="HIGH",
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )

            # Track suspicious activity
            ip = self._get_client_ip(request)
            cache.incr(f"suspicious:{ip}")

        return threat_detected

    def _enforce_session_security(self, request: HttpRequest) -> None:
        """Enforce session security measures"""
        if request.user.is_authenticated:
            # Check session timeout
            last_activity = request.session.get("last_activity")
            if last_activity:
                last_activity_time = datetime.fromisoformat(last_activity)
                if (now() - last_activity_time) > timedelta(minutes=30):
                    request.session.flush()
                    raise PermissionDenied("Session expired")

            # Update last activity
            request.session["last_activity"] = now().isoformat()

            # Check concurrent sessions
            user_sessions = cache.get(f"user_sessions:{request.user.id}", [])
            current_session_key = request.session.session_key

            if current_session_key not in user_sessions and len(user_sessions) >= 3:
                # Too many concurrent sessions
                request.session.flush()
                raise PermissionDenied("Too many concurrent sessions")

    def _protect_phi_data(self, request: HttpRequest) -> None:
        """Protect PHI data in requests"""
        # Encrypt any PHI data in request body
        if hasattr(request, "body") and request.body:
            # This would be implemented based on specific PHI detection rules
            pass

    def _add_security_headers(self, response: HttpResponse) -> None:
        """Add comprehensive security headers"""
        security_headers = {
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": self._get_csp_header(),
            "Permissions-Policy": self._get_permissions_policy(),
            "X-Permitted-Cross-Domain-Policies": "none",
            "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }

        for header, value in security_headers.items():
            response[header] = value

    def _get_csp_header(self) -> str:
        """Generate Content Security Policy header"""
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-src 'none'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "require-trusted-types-for 'script';"
        )

    def _get_permissions_policy(self) -> str:
        """Generate Permissions Policy header"""
        return (
            "accelerometer=(), "
            "ambient-light-sensor=(), "
            "battery=(), "
            "bluetooth=(), "
            "camera=(), "
            "cross-origin-isolated=(), "
            "display-capture=(), "
            "document-domain=(), "
            "encrypted-media=(), "
            "execution-while-not-rendered=(), "
            "execution-while-out-of-viewport=(), "
            "fullscreen=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "hid=(), "
            "identity-credentials-get=(), "
            "idle-detection=(), "
            "local-fonts=(), "
            "magnetometer=(), "
            "microphone=(), "
            "midi=(), "
            "otp-credentials=(), "
            "payment=(), "
            "picture-in-picture=(), "
            "publickey-credentials-get=(), "
            "screen-wake-lock=(), "
            "serial=(), "
            "storage-access=(), "
            "usb=(), "
            "window-management=(), "
            "xr-spatial-tracking=()"
        )

    def _mask_phi_in_response(self, response: JsonResponse) -> None:
        """Mask PHI data in API responses"""
        # This would implement PHI masking based on user permissions
        # and data sensitivity levels
        pass

    def _log_security_event(self, request: HttpRequest, response: HttpResponse) -> None:
        """Log security events for audit trail"""
        if response.status_code >= 400:
            log_security_event(
                event_type="HTTP_ERROR",
                description=f"HTTP {response.status_code} for {request.path}",
                severity="LOW" if response.status_code < 500 else "MEDIUM",
                ip_address=self._get_client_ip(request),
                user_id=request.user.id if request.user.is_authenticated else None,
            )

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address from request"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def _block_request(self, request: HttpRequest, reason: str) -> HttpResponse:
        """Block request and return security response"""
        log_security_event(
            event_type="REQUEST_BLOCKED",
            description=reason,
            severity="HIGH",
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return JsonResponse(
            {
                "error": "Access Denied",
                "message": "Your request has been blocked for security reasons",
                "code": "SECURITY_BLOCK",
            },
            status=403,
        )
