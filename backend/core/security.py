import hashlib
import hmac
import secrets
from typing import Dict, Optional

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest


class SecurityUtils:
    """Security utility functions"""

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a cryptographically secure random token"""
        return secrets.token_urlsafe(length)

    @staticmethod
    def hash_string(value: str, salt: str = None) -> str:
        """Create a secure hash of a string"""
        if salt is None:
            salt = settings.SECRET_KEY

        # Use HMAC for additional security
        return hmac.new(
            salt.encode(),
            value.encode(),
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    def verify_hmac(message: str, signature: str, secret: str) -> bool:
        """Verify HMAC signature"""
        expected = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    @staticmethod
    def get_request_fingerprint(request: HttpRequest) -> str:
        """Generate a fingerprint for the request"""
        components = [
            request.META.get('HTTP_USER_AGENT', ''),
            SecurityUtils.get_client_ip(request),
            request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
        ]
        fingerprint = '|'.join(components)
        return hashlib.sha256(fingerprint.encode()).hexdigest()

    @staticmethod
    def get_client_ip(request: HttpRequest) -> str:
        """Get the real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')

        # Validate IP address format
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return ip
        except ValueError:
            return '0.0.0.0'

    @staticmethod
    def check_suspicious_activity(request: HttpRequest, user=None) -> Dict[str, any]:
        """Check for suspicious activity patterns"""
        ip = SecurityUtils.get_client_ip(request)
        fingerprint = SecurityUtils.get_request_fingerprint(request)

        # Check for rapid requests from same IP
        cache_key = f"requests:{ip}"
        request_count = cache.get(cache_key, 0)
        cache.set(cache_key, request_count + 1, 60)  # 1 minute window

        # Check for unusual user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        suspicious_agents = ['curl', 'wget', 'python-requests']

        flags = {
            'high_request_rate': request_count > 100,
            'suspicious_user_agent': any(agent in user_agent.lower() for agent in suspicious_agents),
            'unusual_fingerprint': False,  # Could implement ML-based detection
        }

        risk_score = sum(flags.values()) * 25  # Simple risk scoring

        return {
            'risk_score': risk_score,
            'flags': flags,
            'ip': ip,
            'fingerprint': fingerprint,
        }


class SessionSecurity:
    """Session security management"""

    @staticmethod
    def create_secure_session(user, request: HttpRequest) -> str:
        """Create a secure session with metadata"""
        session_id = SecurityUtils.generate_secure_token(32)

        session_data = {
            'user_id': user.id,
            'ip': SecurityUtils.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'fingerprint': SecurityUtils.get_request_fingerprint(request),
            'created_at': str(timezone.now()),
        }

        # Store session data securely
        cache_key = f"session:{session_id}"
        cache.set(cache_key, session_data, 3600 * 24)  # 24 hours

        return session_id

    @staticmethod
    def validate_session(session_id: str, request: HttpRequest) -> Optional[Dict]:
        """Validate session and check for anomalies"""
        cache_key = f"session:{session_id}"
        session_data = cache.get(cache_key)

        if not session_data:
            return None

        # Check IP consistency
        current_ip = SecurityUtils.get_client_ip(request)
        if session_data['ip'] != current_ip:
            # Log potential session hijacking
            logger.warning(f"IP mismatch for session {session_id}: {session_data['ip']} != {current_ip}")

        # Check user agent consistency
        current_ua = request.META.get('HTTP_USER_AGENT', '')
        if session_data['user_agent'] != current_ua:
            # Log potential session hijacking
            logger.warning(f"User agent mismatch for session {session_id}")

        return session_data

    @staticmethod
    def destroy_session(session_id: str):
        """Securely destroy a session"""
        cache_key = f"session:{session_id}"
        cache.delete(cache_key)


class AuditLogger:
    """Security audit logging"""

    @staticmethod
    def log_security_event(
        event_type: str,
        severity: str,
        description: str,
        user=None,
        request=None,
        metadata=None
    ):
        """Log security events"""
        from authentication.models import SecurityEvent

        event_data = {
            'event_type': event_type,
            'severity': severity,
            'description': description,
            'user': user,
            'metadata': metadata or {},
        }

        if request:
            event_data.update({
                'ip_address': SecurityUtils.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            })

        SecurityEvent.objects.create(**event_data)