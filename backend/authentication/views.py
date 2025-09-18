import logging
import secrets
from datetime import timedelta
try:
    import pyotp
    PYOTP_AVAILABLE = True
except ImportError:
    PYOTP_AVAILABLE = False
    pyotp = None
from django.contrib.auth import authenticate, get_user_model
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from django.utils.html import escape
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from core.permissions import RolePermission
from users.models import UserLoginHistory, UserSession
from .models import (
    LoginSession,
    MFADevice,
    PasswordPolicy,
    SecurityEvent,
    TrustedDevice,
)
from .serializers import (
    LoginSerializer,
    MFASetupSerializer,
    MFASerializer,
    PasswordChangeSerializer,
    SecurityEventSerializer,
    TrustedDeviceSerializer,
    LoginSessionSerializer,
    PasswordPolicySerializer,
    UserSecurityProfileSerializer,
)
User = get_user_model()
logger = logging.getLogger(__name__)
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = LoginSerializer
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            SecurityEvent.objects.create(
                event_type="LOGIN_FAILED",
                severity="LOW",
                description=f"Login failed: invalid username {username}",
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                metadata={"username": username},
            )
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )
        if user.is_account_locked():
            SecurityEvent.objects.create(
                user=user,
                event_type="ACCOUNT_LOCKED",
                severity="MEDIUM",
                description="Login attempt on locked account",
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
            return Response(
                {"error": "Account is temporarily locked"},
                status=status.HTTP_423_LOCKED,
            )
        user = authenticate(username=username, password=password)
        if not user:
            user.failed_login_attempts += 1
            user.save()
            policy = PasswordPolicy.objects.filter(
                is_active=True, is_default=True
            ).first()
            max_attempts = policy.max_failed_attempts if policy else 5
            if user.failed_login_attempts >= max_attempts:
                lock_duration = policy.lockout_duration_minutes if policy else 30
                user.lock_account(lock_duration)
                SecurityEvent.objects.create(
                    user=user,
                    event_type="ACCOUNT_LOCKED",
                    severity="HIGH",
                    description=f"Account locked after {max_attempts} failed attempts",
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get("HTTP_USER_AGENT", ""),
                )
            UserLoginHistory.objects.create(
                user=user,
                username_attempted=username,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                success=False,
                failure_reason="Invalid password",
            )
            SecurityEvent.objects.create(
                user=user,
                event_type="LOGIN_FAILED",
                severity="LOW",
                description="Login failed: invalid password",
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                metadata={"attempts": user.failed_login_attempts},
            )
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )
        user.failed_login_attempts = 0
        user.save()
        if user.mfa_enabled:
            return Response(
                {
                    "mfa_required": True,
                    "user_id": user.id,
                    "mfa_devices": [
                        {
                            "id": device.id,
                            "name": device.name,
                            "type": device.device_type,
                        }
                        for device in user.mfa_devices.filter(is_active=True)
                    ],
                }
            )
        return self.create_session_and_tokens(request, user)
    def create_session_and_tokens(self, request, user):
        session = LoginSession.objects.create(
            user=user,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            device_info=self.get_device_info(request),
            login_method="PASSWORD",
            mfa_verified=user.mfa_enabled,
        )
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        UserSession.objects.create(
            user=user,
            session_key=secrets.token_urlsafe(32),
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            is_active=True,
        )
        UserLoginHistory.objects.create(
            user=user,
            username_attempted=user.username,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            success=True,
        )
        SecurityEvent.objects.create(
            user=user,
            event_type="LOGIN_SUCCESS",
            severity="LOW",
            description="User logged in successfully",
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            session_id=session.session_id,
        )
        return Response(
            {
                "refresh": str(refresh),
                "access": access_token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.get_full_name(),
                    "role": user.role,
                    "hospital": user.hospital.name if user.hospital else None,
                },
                "session_id": session.session_id,
            }
        )
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
    def get_device_info(self, request):
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        return {
            "user_agent": user_agent,
            "platform": "web",  
        }
class MFAAuthenticationView(APIView):
    def post(self, request):
        serializer = MFASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data["user_id"]
        token = serializer.validated_data["token"]
        device_id = serializer.validated_data.get("device_id")
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid user"}, status=status.HTTP_400_BAD_REQUEST
            )
        device = None
        if device_id:
            try:
                device = MFADevice.objects.get(id=device_id, user=user, is_active=True)
            except MFADevice.DoesNotExist:
                pass
        if device:
            if device.verify_token(token):
                return self.create_session_and_tokens(request, user, device)
            else:
                SecurityEvent.objects.create(
                    user=user,
                    event_type="MFA_FAILED",
                    severity="MEDIUM",
                    description=f"MFA verification failed for device {device.name}",
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get("HTTP_USER_AGENT", ""),
                )
                return Response(
                    {"error": "Invalid MFA token"}, status=status.HTTP_401_UNAUTHORIZED
                )
        for mfa_device in user.mfa_devices.filter(is_active=True):
            if mfa_device.verify_token(token):
                return self.create_session_and_tokens(request, user, mfa_device)
        SecurityEvent.objects.create(
            user=user,
            event_type="MFA_FAILED",
            severity="MEDIUM",
            description="MFA verification failed for all devices",
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        return Response(
            {"error": "Invalid MFA token"}, status=status.HTTP_401_UNAUTHORIZED
        )
    def create_session_and_tokens(self, request, user, mfa_device):
        session = (
            LoginSession.objects.filter(user=user, is_active=True)
            .order_by("-created_at")
            .first()
        )
        if session:
            session.mfa_verified = True
            session.mfa_device_used = mfa_device
            session.save()
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        SecurityEvent.objects.create(
            user=user,
            event_type="MFA_SUCCESS",
            severity="LOW",
            description=f"MFA verification successful with {mfa_device.device_type}",
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            session_id=session.session_id if session else None,
        )
        return Response(
            {
                "refresh": str(refresh),
                "access": access_token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.get_full_name(),
                    "role": user.role,
                    "hospital": user.hospital.name if user.hospital else None,
                },
                "session_id": session.session_id if session else None,
            }
        )
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
class MFASetupViewSet(ModelViewSet):
    serializer_class = MFASetupSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return MFADevice.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    @action(detail=True, methods=["post"])
    def verify_setup(self, request, pk=None):
        device = self.get_object()
        token = request.data.get("token")
        if not token:
            return Response(
                {"error": "Token required"}, status=status.HTTP_400_BAD_REQUEST
            )
        if device.verify_token(token):
            device.is_active = True
            device.save()
            SecurityEvent.objects.create(
                user=request.user,
                event_type="MFA_SETUP",
                severity="LOW",
                description=f"MFA device {device.name} setup completed",
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                metadata={"device_type": device.device_type},
            )
            return Response({"message": "MFA setup verified successfully"})
        else:
            return Response(
                {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
            )
    @action(detail=True, methods=["post"])
    def generate_backup_codes(self, request, pk=None):
        device = self.get_object()
        codes = device.generate_backup_codes()
        SecurityEvent.objects.create(
            user=request.user,
            event_type="MFA_SETUP",
            severity="LOW",
            description=f"Backup codes generated for MFA device {device.name}",
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        return Response(
            {
                "backup_codes": codes,
                "message": "Backup codes generated. Store them securely.",
            }
        )
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]
        if not user.check_password(old_password):
            SecurityEvent.objects.create(
                user=user,
                event_type="PASSWORD_CHANGE",
                severity="MEDIUM",
                description="Password change failed: incorrect old password",
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
            return Response(
                {"error": "Current password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        policy = PasswordPolicy.objects.filter(is_active=True, is_default=True).first()
        if policy:
            self.validate_password_policy(new_password, policy)
        with transaction.atomic():
            user.set_password(new_password)
            user.password_changed_at = timezone.now()
            user.must_change_password = False
            user.save()
            cache.delete_pattern(f"user_sessions_{user.id}_*")
        SecurityEvent.objects.create(
            user=user,
            event_type="PASSWORD_CHANGE",
            severity="LOW",
            description="Password changed successfully",
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        return Response({"message": "Password changed successfully"})
    def validate_password_policy(self, password, policy):
        errors = []
        if len(password) < policy.min_length:
            errors.append(f"Password must be at least {policy.min_length} characters")
        if policy.require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain uppercase letters")
        if policy.require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain lowercase letters")
        if policy.require_digits and not any(c.isdigit() for c in password):
            errors.append("Password must contain digits")
        if policy.require_special_chars:
            special_chars = set(policy.special_chars)
            if not any(c in special_chars for c in password):
                errors.append("Password must contain special characters")
        if errors:
            from rest_framework import serializers
            raise serializers.ValidationError({"password": errors})
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass  
        user_sessions = UserSession.objects.filter(user=request.user, is_active=True)
        user_sessions.update(is_active=False, logout_time=timezone.now())
        login_sessions = LoginSession.objects.filter(user=request.user, is_active=True)
        for session in login_sessions:
            session.is_active = False
            session.logout_time = timezone.now()
            session.save()
        SecurityEvent.objects.create(
            user=request.user,
            event_type="LOGOUT",
            severity="LOW",
            description="User logged out",
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        return Response({"message": "Logged out successfully"})
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
class TrustedDeviceViewSet(ModelViewSet):
    serializer_class = TrustedDeviceSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return TrustedDevice.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        fingerprint = self.generate_device_fingerprint(self.request)
        serializer.save(
            user=self.request.user,
            device_fingerprint=fingerprint,
            user_agent=self.request.META.get("HTTP_USER_AGENT", ""),
            ip_address=self.get_client_ip(self.request),
            trust_expires_at=timezone.now() + timedelta(days=30),  
        )
    def generate_device_fingerprint(self, request):
        components = [
            request.META.get("HTTP_USER_AGENT", ""),
            self.get_client_ip(request),
            request.META.get("HTTP_ACCEPT_LANGUAGE", ""),
            request.META.get("HTTP_ACCEPT_ENCODING", ""),
        ]
        fingerprint_string = "|".join(components)
        return secrets.token_hex(16)  
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
class SecurityEventViewSet(ModelViewSet):
    serializer_class = SecurityEventSerializer
    permission_classes = [IsAuthenticated, RolePermission]
    allowed_roles = ["SUPER_ADMIN", "IT_ADMIN", "SECURITY"]
    def get_queryset(self):
        queryset = SecurityEvent.objects.all()
        user_id = self.request.query_params.get("user")
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        event_type = self.request.query_params.get("event_type")
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        severity = self.request.query_params.get("severity")
        if severity:
            queryset = queryset.filter(severity=severity)
        start_date = self.request.query_params.get("start_date")
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        end_date = self.request.query_params.get("end_date")
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        return queryset.order_by("-created_at")
    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        event = self.get_object()
        event.resolved_at = timezone.now()
        event.resolved_by = request.user
        event.action_taken = request.data.get("action_taken", "")
        event.requires_action = False
        event.save()
        return Response({"message": "Event marked as resolved"})
class SessionManagementView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        sessions = LoginSession.objects.filter(
            user=request.user, is_active=True
        ).order_by("-last_activity")
        session_data = []
        for session in sessions:
            session_data.append(
                {
                    "id": session.id,
                    "session_id": session.session_id,
                    "ip_address": session.ip_address,
                    "user_agent": session.user_agent,
                    "device_info": session.device_info,
                    "created_at": session.created_at,
                    "last_activity": session.last_activity,
                    "expires_at": session.expires_at,
                }
            )
        return Response({"sessions": session_data})
    @action(detail=True, methods=["post"])
    def terminate(self, request, session_id):
        try:
            session = LoginSession.objects.get(
                session_id=session_id, user=request.user, is_active=True
            )
            session.is_active = False
            session.logout_time = timezone.now()
            session.save()
            SecurityEvent.objects.create(
                user=request.user,
                event_type="SYSTEM_ADMIN",
                severity="LOW",
                description=f"User terminated session {session_id}",
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                affected_resource=f"session:{session_id}",
            )
            return Response({"message": "Session terminated"})
        except LoginSession.DoesNotExist:
            return Response(
                {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
            )
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip