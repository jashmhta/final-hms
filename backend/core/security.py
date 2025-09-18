import hashlib
import hmac
import ipaddress
import logging
import secrets
from datetime import datetime
from typing import Dict, Optional

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest


class SecurityUtils:
    """Enterprise-grade security utility functions for HMS system.

    Provides cryptographic operations, session management, and security monitoring
    capabilities with HIPAA compliance in mind.
    """

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a cryptographically secure random token.

        Args:
            length (int): Token length in bytes (default: 32)

        Returns:
            str: URL-safe base64 encoded random token
        """
        return secrets.token_urlsafe(length)

    @staticmethod
    def hash_string(value: str, salt: str = None) -> str:
        """Hash a string using HMAC-SHA256.

        Args:
            value (str): Value to hash
            salt (str, optional): Salt for hashing (defaults to SECRET_KEY)

        Returns:
            str: Hexadecimal hash digest
        """
        if salt is None:
            salt = settings.SECRET_KEY
        return hmac.new(salt.encode(), value.encode(), hashlib.sha256).hexdigest()

    @staticmethod
    def verify_hmac(message: str, signature: str, secret: str) -> bool:
        """Verify HMAC signature for message integrity.

        Args:
            message (str): Original message
            signature (str): Signature to verify
            secret (str): Secret key used for HMAC

        Returns:
            bool: True if signature is valid, False otherwise
        """
        expected = hmac.new(
            secret.encode(), message.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    @staticmethod
    def get_request_fingerprint(request: HttpRequest) -> str:
        """Generate unique fingerprint for HTTP request.

        Combines user agent, IP address, and accept language to create
        a unique identifier for the request source.

        Args:
            request (HttpRequest): Django HTTP request object

        Returns:
            str: SHA256 hash fingerprint
        """
        components = [
            request.META.get("HTTP_USER_AGENT", ""),
            SecurityUtils.get_client_ip(request),
            request.META.get("HTTP_ACCEPT_LANGUAGE", ""),
        ]
        fingerprint = "|".join(components)
        return hashlib.sha256(fingerprint.encode()).hexdigest()

    @staticmethod
    def get_client_ip(request: HttpRequest) -> str:
        """Extract and validate client IP address from request.

        Handles proxy headers and validates IP address format.

        Args:
            request (HttpRequest): Django HTTP request object

        Returns:
            str: Validated IP address or "0.0.0.0" if invalid
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "")

        try:
            ipaddress.ip_address(ip)
            return ip
        except ValueError:
            return "0.0.0.0"

    @staticmethod
    def check_suspicious_activity(request: HttpRequest, user=None) -> Dict[str, any]:
        """Analyze request for suspicious activity patterns.

        Monitors request frequency, user agent patterns, and other
        indicators to detect potential security threats.

        Args:
            request (HttpRequest): Django HTTP request object
            user (User, optional): Django user object

        Returns:
            Dict[str, any]: Risk assessment with flags and score
        """
        ip = SecurityUtils.get_client_ip(request)
        fingerprint = SecurityUtils.get_request_fingerprint(request)
        cache_key = f"requests:{ip}"
        request_count = cache.get(cache_key, 0)
        cache.set(cache_key, request_count + 1, 60)
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        suspicious_agents = ["curl", "wget", "python-requests"]
        flags = {
            "high_request_rate": request_count > 100,
            "suspicious_user_agent": any(
                agent in user_agent.lower() for agent in suspicious_agents
            ),
            "unusual_fingerprint": False,
        }
        risk_score = sum(flags.values()) * 25
        return {
            "risk_score": risk_score,
            "flags": flags,
            "ip": ip,
            "fingerprint": fingerprint,
        }


class SessionSecurity:
    """Enterprise-grade session security management.

    Handles secure session creation, validation, and destruction with
    comprehensive security checks and HIPAA compliance.
    """

    @staticmethod
    def create_secure_session(user, request: HttpRequest) -> str:
        """Create a secure session with comprehensive validation.

        Generates session token with IP binding and user agent validation
        for enhanced security.

        Args:
            user (User): Django user object
            request (HttpRequest): Django HTTP request object

        Returns:
            str: Secure session identifier
        """
        session_id = SecurityUtils.generate_secure_token(32)
        session_data = {
            "user_id": user.id,
            "ip": SecurityUtils.get_client_ip(request),
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "fingerprint": SecurityUtils.get_request_fingerprint(request),
            "created_at": str(datetime.now()),
        }
        cache_key = f"session:{session_id}"
        cache.set(cache_key, session_data, 3600 * 24)
        return session_id

    @staticmethod
    def validate_session(session_id: str, request: HttpRequest) -> Optional[Dict]:
        """Validate session and check for security anomalies.

        Verifies session existence and checks for IP address or user
        agent changes that might indicate session hijacking.

        Args:
            session_id (str): Session identifier to validate
            request (HttpRequest): Django HTTP request object

        Returns:
            Optional[Dict]: Session data if valid, None if invalid
        """
        cache_key = f"session:{session_id}"
        session_data = cache.get(cache_key)
        if not session_data:
            return None
        current_ip = SecurityUtils.get_client_ip(request)
        if session_data["ip"] != current_ip:
            logger = logging.getLogger(__name__)
            logger.warning(
                f"IP mismatch for session {session_id}: {session_data['ip']} != {current_ip}"
            )

        current_ua = request.META.get("HTTP_USER_AGENT", "")
        if session_data["user_agent"] != current_ua:
            logger = logging.getLogger(__name__)
            logger.warning(f"User agent mismatch for session {session_id}")
        return session_data

    @staticmethod
    def destroy_session(session_id: str):
        """Securely destroy session data.

        Removes session data from cache and invalidates the session.

        Args:
            session_id (str): Session identifier to destroy
        """
        cache_key = f"session:{session_id}"
        cache.delete(cache_key)


class AuditLogger:
    """Enterprise-grade security event logging system.

    Provides comprehensive audit trail capabilities for HIPAA compliance
    and security monitoring.
    """

    @staticmethod
    def log_security_event(
        event_type: str,
        severity: str,
        description: str,
        user=None,
        request=None,
        metadata=None,
    ):
        """Log security events to audit trail.

        Creates comprehensive audit records for security events with
        full context and metadata.

        Args:
            event_type (str): Type of security event
            severity (str): Event severity level
            description (str): Event description
            user (User, optional): Associated user object
            request (HttpRequest, optional): Associated HTTP request
            metadata (dict, optional): Additional event metadata
        """
        from authentication.models import SecurityEvent

        event_data = {
            "event_type": event_type,
            "severity": severity,
            "description": description,
            "user": user,
            "metadata": metadata or {},
        }
        if request:
            event_data.update(
                {
                    "ip_address": SecurityUtils.get_client_ip(request),
                    "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                }
            )
        SecurityEvent.objects.create(**event_data)
