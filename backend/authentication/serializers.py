import logging
from datetime import timedelta

import pyotp
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import (
    LoginSession,
    MFADevice,
    PasswordPolicy,
    SecurityEvent,
    TrustedDevice,
)

logger = logging.getLogger(__name__)


class LoginSerializer(TokenObtainPairSerializer):
    """Enhanced login serializer with MFA support"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'] = serializers.CharField()
        self.fields['password'] = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )

            if not user:
                raise serializers.ValidationError(
                    'No active account found with the given credentials'
                )

            # Check if account is locked
            if user.is_account_locked():
                raise serializers.ValidationError(
                    'Account is temporarily locked due to too many failed attempts'
                )

            # Check if user must change password
            if user.must_change_password:
                raise serializers.ValidationError(
                    'Password change required before login'
                )

            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                'Must include username and password'
            )


class MFASerializer(serializers.Serializer):
    """Serializer for MFA token verification"""
    user_id = serializers.IntegerField()
    token = serializers.CharField(max_length=10)
    device_id = serializers.IntegerField(required=False)

    def validate_token(self, value):
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError('Token must be 6 digits')
        return value


class MFASetupSerializer(serializers.ModelSerializer):
    """Serializer for MFA device setup"""
    qr_code_url = serializers.SerializerMethodField()
    backup_codes = serializers.SerializerMethodField()

    class Meta:
        model = MFADevice
        fields = [
            'id', 'device_type', 'name', 'is_active', 'is_primary',
            'phone_number', 'email_address', 'qr_code_url', 'backup_codes',
            'created_at', 'last_used'
        ]
        read_only_fields = ['id', 'qr_code_url', 'backup_codes', 'created_at', 'last_used']
        extra_kwargs = {
            'phone_number': {'required': False},
            'email_address': {'required': False},
        }

    def get_qr_code_url(self, obj):
        return obj.get_totp_uri()

    def get_backup_codes(self, obj):
        # Only return backup codes during initial setup
        if obj.device_type == 'BACKUP' and not obj.backup_codes:
            return obj.generate_backup_codes()
        return None

    def validate(self, attrs):
        device_type = attrs.get('device_type')
        if device_type == 'TOTP':
            # TOTP doesn't need phone/email
            pass
        elif device_type == 'SMS':
            if not attrs.get('phone_number'):
                raise serializers.ValidationError(
                    {'phone_number': 'Phone number required for SMS MFA'}
                )
        elif device_type == 'EMAIL':
            if not attrs.get('email_address'):
                raise serializers.ValidationError(
                    {'email_address': 'Email address required for Email MFA'}
                )
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password changes"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate_new_password_confirm(self, value):
        new_password = self.initial_data.get('new_password')
        if new_password != value:
            raise serializers.ValidationError("Password confirmation doesn't match")
        return value

    def validate_new_password(self, value):
        # Additional policy validation
        policy = PasswordPolicy.objects.filter(is_active=True, is_default=True).first()
        if policy:
            errors = []

            if len(value) < policy.min_length:
                errors.append(f'Password must be at least {policy.min_length} characters')

            if policy.require_uppercase and not any(c.isupper() for c in value):
                errors.append('Password must contain uppercase letters')

            if policy.require_lowercase and not any(c.islower() for c in value):
                errors.append('Password must contain lowercase letters')

            if policy.require_digits and not any(c.isdigit() for c in value):
                errors.append('Password must contain digits')

            if policy.require_special_chars:
                special_chars = set(policy.special_chars)
                if not any(c in special_chars for c in value):
                    errors.append('Password must contain special characters')

            if errors:
                raise serializers.ValidationError(errors)

        return value


class TrustedDeviceSerializer(serializers.ModelSerializer):
    """Serializer for trusted devices"""
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = TrustedDevice
        fields = [
            'id', 'device_id', 'name', 'user_agent', 'ip_address',
            'device_info', 'is_active', 'trust_expires_at', 'last_used',
            'is_expired', 'created_at'
        ]
        read_only_fields = ['id', 'device_id', 'is_expired', 'created_at']

    def get_is_expired(self, obj):
        return obj.is_expired()


class SecurityEventSerializer(serializers.ModelSerializer):
    """Serializer for security events"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    resolved_by_name = serializers.CharField(
        source='resolved_by.get_full_name',
        read_only=True
    )

    class Meta:
        model = SecurityEvent
        fields = [
            'id', 'user', 'user_name', 'event_type', 'severity',
            'description', 'ip_address', 'user_agent', 'session_id',
            'metadata', 'affected_resource', 'requires_action',
            'action_taken', 'resolved_at', 'resolved_by', 'resolved_by_name',
            'created_at'
        ]
        read_only_fields = [
            'id', 'user_name', 'resolved_by_name', 'created_at'
        ]


class LoginSessionSerializer(serializers.ModelSerializer):
    """Serializer for login sessions"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    is_expired = serializers.SerializerMethodField()
    time_since_activity = serializers.SerializerMethodField()

    class Meta:
        model = LoginSession
        fields = [
            'id', 'user', 'user_name', 'session_id', 'ip_address',
            'user_agent', 'device_info', 'login_method', 'mfa_verified',
            'mfa_device_used', 'is_active', 'last_activity', 'expires_at',
            'logout_time', 'is_suspicious', 'risk_score', 'is_expired',
            'time_since_activity', 'created_at'
        ]
        read_only_fields = ['id', 'session_id', 'is_expired', 'time_since_activity', 'created_at']

    def get_is_expired(self, obj):
        return obj.is_expired()

    def get_time_since_activity(self, obj):
        if obj.last_activity:
            return (timezone.now() - obj.last_activity).total_seconds()
        return None


class PasswordPolicySerializer(serializers.ModelSerializer):
    """Serializer for password policies"""

    class Meta:
        model = PasswordPolicy
        fields = [
            'id', 'name', 'description', 'min_length', 'max_length',
            'require_uppercase', 'require_lowercase', 'require_digits',
            'require_special_chars', 'special_chars', 'password_history_count',
            'max_age_days', 'min_age_hours', 'max_failed_attempts',
            'lockout_duration_minutes', 'session_timeout_minutes',
            'max_concurrent_sessions', 'is_active', 'is_default',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSecurityProfileSerializer(serializers.Serializer):
    """Serializer for user security profile information"""
    mfa_enabled = serializers.BooleanField(read_only=True)
    mfa_devices_count = serializers.IntegerField(read_only=True)
    trusted_devices_count = serializers.IntegerField(read_only=True)
    failed_login_attempts = serializers.IntegerField(read_only=True)
    account_locked_until = serializers.DateTimeField(read_only=True)
    password_changed_at = serializers.DateTimeField(read_only=True)
    must_change_password = serializers.BooleanField(read_only=True)
    active_sessions_count = serializers.IntegerField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)
    security_events_count = serializers.IntegerField(read_only=True)
    recent_security_events = SecurityEventSerializer(many=True, read_only=True)