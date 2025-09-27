"""
Enterprise API Security Gateway
Provides comprehensive API protection including:
- Authentication and authorization
- Rate limiting and throttling
- Request validation and sanitization
- Threat detection and prevention
- API documentation and discovery
- Monitoring and analytics
"""

import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from core.security_compliance import log_security_event
from core.security_middleware import RateLimiter, SecurityMiddleware
from core.zero_trust_auth import ZeroTrustAuthorization

logger = logging.getLogger(__name__)


class APIEndpoint:
    """API endpoint configuration"""

    def __init__(
        self,
        path: str,
        methods: List[str],
        auth_required: bool = True,
        scopes: List[str] = None,
        rate_limit: Dict = None,
        allowed_origins: List[str] = None,
        validation_rules: Dict = None,
        sensitive: bool = False,
    ):
        self.path = path
        self.methods = methods
        self.auth_required = auth_required
        self.scopes = scopes or []
        self.rate_limit = rate_limit or {"requests": 100, "window": 60}
        self.allowed_origins = allowed_origins or []
        self.validation_rules = validation_rules or {}
        self.sensitive = sensitive


class APIGatewayConfig:
    """API Gateway Configuration"""

    def __init__(self):
        self.endpoints = self._load_endpoints()
        self.global_rate_limits = {
            "per_minute": 1000,
            "per_hour": 10000,
            "per_day": 100000,
        }
        self.blocked_ips = set()
        self.blocked_tokens = set()
        self.sensitive_patterns = self._load_sensitive_patterns()

    def _load_endpoints(self) -> Dict[str, APIEndpoint]:
        """Load API endpoint configurations"""
        return {
            # Health endpoints
            "/health/": APIEndpoint(
                path="/health/",
                methods=["GET"],
                auth_required=False,
                rate_limit={"requests": 10, "window": 60},
            ),
            # Authentication endpoints
            "/api/auth/login/": APIEndpoint(
                path="/api/auth/login/",
                methods=["POST"],
                auth_required=False,
                rate_limit={"requests": 5, "window": 60},
            ),
            "/api/auth/refresh/": APIEndpoint(
                path="/api/auth/refresh/",
                methods=["POST"],
                auth_required=True,
                rate_limit={"requests": 10, "window": 60},
            ),
            "/api/auth/mfa/": APIEndpoint(
                path="/api/auth/mfa/",
                methods=["POST"],
                auth_required=True,
                rate_limit={"requests": 3, "window": 60},
            ),
            # Patient endpoints
            "/api/patients/": APIEndpoint(
                path="/api/patients/",
                methods=["GET", "POST"],
                auth_required=True,
                scopes=["patients.read", "patients.write"],
                sensitive=True,
                validation_rules={
                    "POST": {
                        "required_fields": ["first_name", "last_name", "date_of_birth"],
                        "max_body_size": 1024 * 1024,  # 1MB
                    }
                },
            ),
            "/api/patients/(?P<pk>[^/.]+)/": APIEndpoint(
                path="/api/patients/{pk}/",
                methods=["GET", "PUT", "DELETE"],
                auth_required=True,
                scopes=["patients.read", "patients.write"],
                sensitive=True,
                validation_rules={
                    "PUT": {
                        "required_fields": ["first_name", "last_name"],
                        "max_body_size": 512 * 1024,  # 512KB
                    }
                },
            ),
            # EHR endpoints
            "/api/ehr/records/": APIEndpoint(
                path="/api/ehr/records/",
                methods=["GET", "POST"],
                auth_required=True,
                scopes=["ehr.read", "ehr.write"],
                sensitive=True,
                rate_limit={"requests": 50, "window": 60},
            ),
            # Lab endpoints
            "/api/lab/results/": APIEndpoint(
                path="/api/lab/results/",
                methods=["GET", "POST"],
                auth_required=True,
                scopes=["lab.read", "lab.write"],
                sensitive=True,
            ),
            # Pharmacy endpoints
            "/api/pharmacy/prescriptions/": APIEndpoint(
                path="/api/pharmacy/prescriptions/",
                methods=["GET", "POST"],
                auth_required=True,
                scopes=["pharmacy.read", "pharmacy.write"],
                sensitive=True,
                rate_limit={"requests": 30, "window": 60},
            ),
            # Billing endpoints (PCI DSS sensitive)
            "/api/billing/payments/": APIEndpoint(
                path="/api/billing/payments/",
                methods=["POST"],
                auth_required=True,
                scopes=["billing.write"],
                sensitive=True,
                rate_limit={"requests": 10, "window": 60},
                validation_rules={
                    "POST": {
                        "required_fields": ["amount", "payment_method"],
                        "pci_compliance": True,
                    }
                },
            ),
        }

    def _load_sensitive_patterns(self) -> List[re.Pattern]:
        """Load patterns for sensitive data detection"""
        patterns = [
            # Credit card numbers
            re.compile(
                r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b"
            ),
            # Social Security Numbers
            re.compile(r"\b\d{3}[-]?\d{2}[-]?\d{4}\b"),
            # Medical record numbers
            re.compile(r"\bMRN\s*[#:]?\s*\d+\b", re.IGNORECASE),
            # Email addresses
            re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        ]
        return patterns


class APIValidator:
    """API Request and Response Validation"""

    def __init__(self):
        self.content_types = {
            "json": "application/json",
            "form": "application/x-www-form-urlencoded",
            "multipart": "multipart/form-data",
        }

    def validate_request(
        self, request: HttpRequest, endpoint: APIEndpoint
    ) -> Tuple[bool, Dict]:
        """Validate incoming request"""
        errors = []

        # 1. Check content type
        content_type = request.content_type.split(";")[0]
        if content_type not in self.content_types.values():
            errors.append(f"Unsupported content type: {content_type}")

        # 2. Check content length
        content_length = request.META.get("CONTENT_LENGTH")
        if content_length:
            content_length = int(content_length)
            max_size = endpoint.validation_rules.get("max_body_size", 10 * 1024 * 1024)
            if content_length > max_size:
                errors.append(f"Request body too large: {content_length} bytes")

        # 3. Validate request body
        if request.method in ["POST", "PUT", "PATCH"]:
            if not self._validate_request_body(request, endpoint):
                errors.append("Invalid request body")

        # 4. Check for sensitive data in logs
        if self._contains_sensitive_data(request):
            errors.append("Request contains sensitive data that should not be logged")

        return len(errors) == 0, {"errors": errors}

    def _validate_request_body(
        self, request: HttpRequest, endpoint: APIEndpoint
    ) -> bool:
        """Validate request body structure"""
        try:
            if request.content_type == "application/json":
                data = json.loads(request.body)
            else:
                return True  # Skip validation for non-JSON

            # Check required fields
            rules = endpoint.validation_rules.get(request.method, {})
            required_fields = rules.get("required_fields", [])

            for field in required_fields:
                if field not in data:
                    return False

            # PCI DSS compliance checks
            if rules.get("pci_compliance"):
                if not self._validate_pci_compliance(data):
                    return False

            return True
        except (json.JSONDecodeError, KeyError):
            return False

    def _validate_pci_compliance(self, data: Dict) -> bool:
        """Validate PCI DSS compliance for payment data"""
        # Check for raw credit card numbers
        card_number = data.get("card_number", "")
        if re.match(r"\b\d{13,19}\b", card_number):
            return False

        # Check for CVV
        cvv = data.get("cvv", "")
        if len(cvv) > 0:
            return False

        return True

    def _contains_sensitive_data(self, request: HttpRequest) -> bool:
        """Check if request contains sensitive data that should not be logged"""
        # This would check for PHI, PII, etc.
        return False

    def sanitize_response(
        self, response_data: Dict, user_permissions: List[str]
    ) -> Dict:
        """Sanitize response based on user permissions"""
        sanitized = response_data.copy()

        # Remove sensitive fields based on permissions
        if "patients.sensitive" not in user_permissions:
            # Remove sensitive patient data
            if "patients" in sanitized:
                for patient in sanitized["patients"]:
                    patient.pop("ssn", None)
                    patient.pop("insurance_number", None)

        return sanitized


class APIMonitor:
    """API Monitoring and Analytics"""

    def __init__(self):
        self.metrics_prefix = "api_metrics:"
        self.alert_thresholds = {
            "error_rate": 0.05,  # 5%
            "response_time_p95": 2000,  # 2 seconds
            "concurrent_requests": 1000,
        }

    def log_request(
        self, request: HttpRequest, response: HttpResponse, duration: float
    ):
        """Log API request metrics"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "duration": duration,
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "ip_address": self._get_client_ip(request),
        }

        # Store metrics
        cache_key = f"{self.metrics_prefix}{request.path}:{request.method}"
        metrics_list = cache.get(cache_key, [])
        metrics_list.append(metrics)

        # Keep only last 1000 requests
        if len(metrics_list) > 1000:
            metrics_list = metrics_list[-1000:]

        cache.set(cache_key, metrics_list, 3600)  # 1 hour retention

        # Check for alerts
        self._check_alerts(metrics)

    def get_metrics(
        self, path: str = None, method: str = None, time_range: int = 3600
    ) -> Dict:
        """Get API metrics"""
        if path and method:
            cache_key = f"{self.metrics_prefix}{path}:{method}"
            requests = cache.get(cache_key, [])
        else:
            requests = []
            # Aggregate all requests (this would be optimized in production)

        if not requests:
            return {}

        # Filter by time range
        cutoff_time = datetime.now() - timedelta(seconds=time_range)
        requests = [
            r for r in requests if datetime.fromisoformat(r["timestamp"]) > cutoff_time
        ]

        # Calculate metrics
        total_requests = len(requests)
        successful_requests = len([r for r in requests if r["status_code"] < 400])
        error_rate = (
            1 - (successful_requests / total_requests) if total_requests > 0 else 0
        )

        response_times = [r["duration"] for r in requests]
        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0
        )
        p95_response_time = (
            sorted(response_times)[int(len(response_times) * 0.95)]
            if response_times
            else 0
        )

        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "error_rate": error_rate,
            "avg_response_time": avg_response_time,
            "p95_response_time": p95_response_time,
            "status_codes": self._count_status_cocryptography.fernet.Fernet(requests),
        }

    def _check_alerts(self, metrics: Dict):
        """Check for alert conditions"""
        # Get recent metrics for the endpoint
        recent_metrics = self.get_metrics(
            metrics["path"], metrics["method"], 300
        )  # 5 minutes

        if recent_metrics.get("error_rate", 0) > self.alert_thresholds["error_rate"]:
            log_security_event(
                event_type="HIGH_ERROR_RATE",
                description=f"High error rate for {metrics['path']}: {recent_metrics['error_rate']:.2%}",
                severity="HIGH",
            )

        if (
            recent_metrics.get("p95_response_time", 0)
            > self.alert_thresholds["response_time_p95"]
        ):
            log_security_event(
                event_type="HIGH_RESPONSE_TIME",
                description=f"High response time for {metrics['path']}: {recent_metrics['p95_response_time']}ms",
                severity="MEDIUM",
            )

    def _count_status_cocryptography.fernet.Fernet(self, requests: List[Dict]) -> Dict:
        """Count status code occurrences"""
        status_codes = {}
        for request in requests:
            code = request["status_code"]
            status_codes[code] = status_codes.get(code, 0) + 1
        return status_codes

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR", "")


class APISecurityGateway(View):
    """Main API Security Gateway"""

    def __init__(self):
        self.config = APIGatewayConfig()
        self.validator = APIValidator()
        self.monitor = APIMonitor()
        self.rate_limiter = RateLimiter()
        self.auth = ZeroTrustAuthorization()

    @method_decorator(csrf_exempt)
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Dispatch request through security gateway"""
        start_time = time.time()

        try:
            # 1. Find matching endpoint
            endpoint = self._find_matching_endpoint(request)
            if not endpoint:
                return self._not_found_response()

            # 2. Check CORS
            cors_response = self._check_cors(request, endpoint)
            if cors_response:
                return cors_response

            # 3. Apply global rate limiting
            if not self._check_global_rate_limit(request):
                return self._rate_limit_response()

            # 4. Apply endpoint-specific rate limiting
            if not self._check_endpoint_rate_limit(request, endpoint):
                return self._rate_limit_response()

            # 5. Authentication check
            if endpoint.auth_required:
                auth_result = self._authenticate_request(request)
                if not auth_result["success"]:
                    return auth_result["response"]

                # Set user in request for downstream use
                request.user = auth_result["user"]
                request.auth_scopes = auth_result["scopes"]

            # 6. Authorization check
            if endpoint.auth_required and not self._authorize_request(
                request, endpoint
            ):
                return self._forbidden_response()

            # 7. Request validation
            is_valid, validation_result = self.validator.validate_request(
                request, endpoint
            )
            if not is_valid:
                return self._validation_error_response(validation_result)

            # 8. Forward to actual endpoint
            response = self._forward_request(request, endpoint)

            # 9. Response sanitization
            if hasattr(response, "data") and isinstance(response.data, dict):
                response.data = self.validator.sanitize_response(
                    response.data, getattr(request, "auth_scopes", [])
                )

            # 10. Log metrics
            duration = (time.time() - start_time) * 1000  # Convert to milliseconds
            self.monitor.log_request(request, response, duration)

            return response

        except Exception as e:
            logger.error(f"API Gateway error: {str(e)}", exc_info=True)
            return self._error_response()

    def _find_matching_endpoint(self, request: HttpRequest) -> Optional[APIEndpoint]:
        """Find matching endpoint configuration"""
        path = request.path

        # Exact match first
        if path in self.config.endpoints:
            return self.config.endpoints[path]

        # Pattern matching for dynamic endpoints
        for endpoint_path, endpoint in self.config.endpoints.items():
            if "{" in endpoint_path and "}" in endpoint_path:
                # Convert to regex pattern
                pattern = endpoint_path.replace("{", "(?P<").replace("}", "[^/.]+)")
                if re.match(f"^{pattern}$", path):
                    return endpoint

        return None

    def _check_cors(
        self, request: HttpRequest, endpoint: APIEndpoint
    ) -> Optional[HttpResponse]:
        """Check CORS preflight and headers"""
        if request.method == "OPTIONS":
            response = JsonResponse({})
            self._add_cors_headers(response, endpoint)
            return response

        origin = request.META.get("HTTP_ORIGIN")
        if (
            origin
            and origin not in endpoint.allowed_origins
            and "*" not in endpoint.allowed_origins
        ):
            return JsonResponse({"error": "CORS policy violation"}, status=403)

        return None

    def _add_cors_headers(self, response: HttpResponse, endpoint: APIEndpoint):
        """Add CORS headers to response"""
        if endpoint.allowed_origins:
            response["Access-Control-Allow-Origin"] = ", ".join(
                endpoint.allowed_origins
            )
        else:
            response["Access-Control-Allow-Origin"] = "*"

        response["Access-Control-Allow-Methods"] = ", ".join(endpoint.methods)
        response["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization, X-Requested-With"
        )
        response["Access-Control-Max-Age"] = "86400"

    def _check_global_rate_limit(self, request: HttpRequest) -> bool:
        """Check global rate limits"""
        ip = self._get_client_ip(request)

        # Check per minute limit
        if not self.rate_limiter.check_rate_limit(
            f"global:{ip}", self.config.global_rate_limits["per_minute"], 60
        ):
            return False

        # Check per hour limit
        if not self.rate_limiter.check_rate_limit(
            f"global_hourly:{ip}", self.config.global_rate_limits["per_hour"], 3600
        ):
            return False

        return True

    def _check_endpoint_rate_limit(
        self, request: HttpRequest, endpoint: APIEndpoint
    ) -> bool:
        """Check endpoint-specific rate limits"""
        ip = self._get_client_ip(request)
        user_id = (
            getattr(request.user, "id", None) if hasattr(request, "user") else None
        )

        # IP-based rate limiting
        if not self.rate_limiter.check_rate_limit(
            f"endpoint:{endpoint.path}:{ip}",
            endpoint.rate_limit["requests"],
            endpoint.rate_limit["window"],
        ):
            return False

        # User-based rate limiting if authenticated
        if user_id:
            if not self.rate_limiter.check_rate_limit(
                f"user_endpoint:{user_id}:{endpoint.path}",
                endpoint.rate_limit["requests"],
                endpoint.rate_limit["window"],
            ):
                return False

        return True

    def _authenticate_request(self, request: HttpRequest) -> Dict:
        """Authenticate request"""
        # Check JWT token
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return {
                "success": False,
                "response": self._unauthorized_response("Missing or invalid token"),
            }

        token = auth_header[7:]  # Remove 'Bearer ' prefix

        # This would integrate with your JWT authentication system
        # For now, return a placeholder
        return {
            "success": True,
            "user": None,  # Would be actual user object
            "scopes": [],  # Would be actual scopes
        }

    def _authorize_request(self, request: HttpRequest, endpoint: APIEndpoint) -> bool:
        """Authorize request"""
        # Check if user has required scopes
        user_scopes = getattr(request, "auth_scopes", [])
        required_scopes = endpoint.scopes

        if required_scopes:
            if not all(scope in user_scopes for scope in required_scopes):
                return False

        # Additional authorization logic would go here
        return True

    def _forward_request(
        self, request: HttpRequest, endpoint: APIEndpoint
    ) -> HttpResponse:
        """Forward request to actual endpoint"""
        # This would forward the request to the actual API endpoint
        # For now, return a placeholder response
        return JsonResponse({"message": "Request processed"})

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR", "")

    def _not_found_response(self) -> HttpResponse:
        """Return 404 response"""
        return JsonResponse({"error": "Endpoint not found"}, status=404)

    def _unauthorized_response(self, message: str) -> HttpResponse:
        """Return 401 response"""
        return JsonResponse({"error": message}, status=401)

    def _forbidden_response(self) -> HttpResponse:
        """Return 403 response"""
        return JsonResponse({"error": "Access forbidden"}, status=403)

    def _rate_limit_response(self) -> HttpResponse:
        """Return 429 response"""
        return JsonResponse(
            {"error": "Rate limit exceeded", "retry_after": 60}, status=429
        )

    def _validation_error_response(self, validation_result: Dict) -> HttpResponse:
        """Return 400 response with validation errors"""
        return JsonResponse(
            {"error": "Validation failed", "errors": validation_result["errors"]},
            status=400,
        )

    def _error_response(self) -> HttpResponse:
        """Return 500 response"""
        return JsonResponse({"error": "Internal server error"}, status=500)


class APIGatewayMetricsView(APIView):
    """API Gateway Metrics Dashboard"""

    def get(self, request):
        """Get API gateway metrics"""
        monitor = APIMonitor()

        # Get overall metrics
        overall_metrics = monitor.get_metrics()

        # Get endpoint-specific metrics
        endpoint_metrics = {}
        for path in ["/api/patients/", "/api/ehr/records/", "/api/billing/payments/"]:
            for method in ["GET", "POST"]:
                metrics = monitor.get_metrics(path, method)
                if metrics:
                    endpoint_metrics[f"{method} {path}"] = metrics

        return Response(
            {
                "overall": overall_metrics,
                "endpoints": endpoint_metrics,
                "timestamp": datetime.now().isoformat(),
            }
        )
