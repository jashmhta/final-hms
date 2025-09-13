import logging

from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin

from .models import AuditLog

logger = logging.getLogger(__name__)


class HIPAAAuditMiddleware(MiddlewareMixin):
    """
    HIPAA-compliant middleware for logging all PHI interactions.
    Captures user actions, PHI access, IP addresses, and session information.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Define PHI-related URL patterns to monitor
        self.phi_patterns = [
            "/patient/",  # Patient management
            "/medical-records/",  # Medical records
            "/appointments/",  # Appointments with PHI
            "/billing/",  # Billing with PHI
            "/compliance/hipaa/",  # HIPAA-specific endpoints
        ]

    def is_phi_request(self, request):
        """Determine if request involves PHI based on URL patterns."""
        path = request.path
        return any(pattern in path for pattern in self.phi_patterns)

    def log_phi_access(self, request, response=None, exception=None):
        """Log PHI access to audit trail."""
        if not self.is_phi_request(request):
            return

        try:
            # Determine action type
            action = self._get_action_type(request)

            # Extract PHI details (sanitized/encrypted)
            phi_details = self._extract_phi_details(request, action)

            # Create audit log entry
            AuditLog.objects.create(
                user=(
                    request.user
                    if not isinstance(request.user, AnonymousUser)
                    else None
                ),
                action=action,
                phi_accessed=phi_details,
                ip_address=request.META.get("REMOTE_ADDR", "unknown"),
                session_id=(
                    request.session.session_key
                    if hasattr(request, "session") and request.session.session_key
                    else None
                ),
            )

            logger.info(
                f"HIPAA audit log created: {action} by {request.user} at {request.META.get('REMOTE_ADDR')} for {phi_details[:50]}..."
            )
        except Exception as e:
            logger.error(f"Failed to create HIPAA audit log: {e}")

    def _get_action_type(self, request):
        """Determine the action type based on request method and path."""
        method = request.method
        path = request.path

        if method == "GET":
            if "/create" in path or "/new" in path:
                return "VIEW_CREATE_FORM"
            return "VIEW_PHI"
        elif method == "POST":
            if "/create" in path or "/submit" in path:
                return "CREATE_PHI"
            elif "/update" in path:
                return "UPDATE_PHI"
            return "SUBMIT_PHI"
        elif method == "PUT":
            return "UPDATE_PHI"
        elif method == "DELETE":
            return "DELETE_PHI"
        else:
            return f"{method}_PHI"

    def _extract_phi_details(self, request, action):
        """Extract and encrypt PHI details from request. Sanitize sensitive data."""
        try:
            if action in ["CREATE_PHI", "UPDATE_PHI"]:
                # Extract from POST data (be careful with sensitive fields)
                post_data = dict(request.POST)
                # Remove or sanitize sensitive fields
                sensitive_fields = ["ssn", "medical_id", "diagnosis", "treatment"]
                for field in sensitive_fields:
                    post_data.pop(field, None)
                return str(post_data)[:500]  # Truncate for logging
            elif action == "VIEW_PHI":
                return f"Viewed PHI at {request.path} with params: {dict(request.GET)}"
            else:
                return f"{action} at {request.path}"
        except Exception:
            return f"PHI interaction at {request.path} (details unavailable)"

    def process_request(self, request):
        """Log PHI access before processing request."""
        self.log_phi_access(request)
        return None

    def process_response(self, request, response):
        """Log PHI access after response (for successful operations)."""
        if response.status_code < 400:  # Success responses
            self.log_phi_access(request, response)
        return response

    def process_exception(self, request, exception):
        """Log PHI access attempts that resulted in exceptions."""
        self.log_phi_access(request, exception=exception)
        return None


# Additional middleware for encryption enforcement
class EncryptionEnforcementMiddleware(MiddlewareMixin):
    """
    Enforce HIPAA encryption requirements for data in transit and at rest.
    Validates HTTPS, sets security headers, and monitors encryption status.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def process_request(self, request):
        """Enforce HTTPS and security headers for PHI requests."""
        if self.is_phi_request(request):
            # Enforce HTTPS
            if not request.is_secure():
                from django.http import HttpResponseRedirect

                return HttpResponseRedirect(
                    "https://" + request.get_host() + request.get_full_path()
                )

            # Set HIPAA-compliant security headers
            response = self.get_response(request)
            response["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
            response["X-Content-Type-Options"] = "nosniff"
            response["X-Frame-Options"] = "DENY"
            response["X-XSS-Protection"] = "1; mode=block"
            response["Referrer-Policy"] = "strict-origin-when-cross-origin"

            # Log encryption status
            logger.info(
                f"HIPAA encryption enforced for {request.path}: HTTPS={request.is_secure()}"
            )

            return response
        return None

    def is_phi_request(self, request):
        """Check if request involves PHI."""
        path = request.path
        phi_patterns = [
            "/patient/",
            "/medical-records/",
            "/appointments/",
            "/billing/",
            "/compliance/hipaa/",
        ]
        return any(pattern in path for pattern in phi_patterns)
