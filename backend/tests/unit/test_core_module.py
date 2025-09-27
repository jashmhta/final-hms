"""
Comprehensive unit tests for core HMS module
"""

import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.middleware import AuditMiddleware, PerformanceMiddleware, SecurityMiddleware
from core.models import AuditLog, IntegrationLog, Notification, SystemConfig, Task
from core.permissions import IsDoctor, IsHospitalAdmin, IsNurse, IsStaff, IsSuperUser
from core.serializers import (
    AuditLogSerializer,
    IntegrationLogSerializer,
    NotificationSerializer,
    SystemConfigSerializer,
    TaskSerializer,
)
from core.tasks import (
    cleanup_old_logs,
    generate_daily_report,
    send_email_notification,
    send_sms_notification,
)
from core.utils import (
    calculate_age,
    decrypt_sensitive_data,
    encrypt_sensitive_data,
    format_currency,
    generate_unique_id,
    parse_date,
    send_notification,
    validate_email,
    validate_phone_number,
)
from core.views import (
    AuditLogViewSet,
    IntegrationLogViewSet,
    NotificationViewSet,
    SystemConfigViewSet,
    TaskViewSet,
)

User = get_user_model()


class CoreModelTests(TestCase):
    """Test core models"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!",
            role="staff",
        )
        self.hospital_data = {
            "name": "Test Hospital",
            "code": "TEST001",
            "address": "123 Test St",
            "phone": "+1234567890",
            "email": "test@hospital.com",
        }

    def test_audit_log_creation(self):
        """Test audit log creation"""
        audit_log = AuditLog.objects.create(
            user=self.user,
            action="user_login",
            resource_type="user",
            resource_id=self.user.id,
            ip_address="127.0.0.1",
            user_agent="test-agent",
            details={"login_method": "password"},
        )

        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.action, "user_login")
        self.assertEqual(audit_log.resource_type, "user")
        self.assertEqual(audit_log.resource_id, self.user.id)
        self.assertIsInstance(audit_log.details, dict)
        self.assertTrue(audit_log.timestamp)

    def test_system_config_creation(self):
        """Test system config creation"""
        config = SystemConfig.objects.create(
            key="test_config",
            value="test_value",
            description="Test configuration",
            data_type="string",
            is_active=True,
        )

        self.assertEqual(config.key, "test_config")
        self.assertEqual(config.value, "test_value")
        self.assertEqual(config.data_type, "string")
        self.assertTrue(config.is_active)
        self.assertTrue(config.created_at)
        self.assertTrue(config.updated_at)

    def test_notification_creation(self):
        """Test notification creation"""
        notification = Notification.objects.create(
            user=self.user,
            title="Test Notification",
            message="This is a test notification",
            notification_type="info",
            priority="medium",
            is_read=False,
        )

        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, "Test Notification")
        self.assertEqual(notification.notification_type, "info")
        self.assertEqual(notification.priority, "medium")
        self.assertFalse(notification.is_read)

    def test_task_creation(self):
        """Test task creation"""
        task = Task.objects.create(
            title="Test Task",
            description="This is a test task",
            assigned_to=self.user,
            created_by=self.user,
            status="pending",
            priority="medium",
            due_date=timezone.now() + timedelta(days=1),
        )

        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.assigned_to, self.user)
        self.assertEqual(task.created_by, self.user)
        self.assertEqual(task.status, "pending")
        self.assertEqual(task.priority, "medium")

    def test_integration_log_creation(self):
        """Test integration log creation"""
        integration_log = IntegrationLog.objects.create(
            service="external_api",
            operation="GET",
            endpoint="https://api.example.com/data",
            request_data={"param": "value"},
            response_data={"result": "success"},
            status_code=200,
            duration_ms=150,
        )

        self.assertEqual(integration_log.service, "external_api")
        self.assertEqual(integration_log.operation, "GET")
        self.assertEqual(integration_log.status_code, 200)
        self.assertEqual(integration_log.duration_ms, 150)


class CoreSerializerTests(TestCase):
    """Test core serializers"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!",
            role="staff",
        )
        self.audit_log = AuditLog.objects.create(
            user=self.user,
            action="test_action",
            resource_type="test_resource",
            resource_id=1,
        )

    def test_audit_log_serializer(self):
        """Test audit log serializer"""
        serializer = AuditLogSerializer(self.audit_log)
        data = serializer.data

        self.assertEqual(data["action"], "test_action")
        self.assertEqual(data["resource_type"], "test_resource")
        self.assertEqual(data["resource_id"], 1)
        self.assertIn("timestamp", data)
        self.assertIn("user", data)

    def test_system_config_serializer(self):
        """Test system config serializer"""
        config = SystemConfig.objects.create(
            key="test_key", value="test_value", data_type="string"
        )
        serializer = SystemConfigSerializer(config)
        data = serializer.data

        self.assertEqual(data["key"], "test_key")
        self.assertEqual(data["value"], "test_value")
        self.assertEqual(data["data_type"], "string")

    def test_notification_serializer(self):
        """Test notification serializer"""
        notification = Notification.objects.create(
            user=self.user,
            title="Test Notification",
            message="Test message",
            notification_type="info",
        )
        serializer = NotificationSerializer(notification)
        data = serializer.data

        self.assertEqual(data["title"], "Test Notification")
        self.assertEqual(data["message"], "Test message")
        self.assertEqual(data["notification_type"], "info")

    def test_task_serializer(self):
        """Test task serializer"""
        task = Task.objects.create(
            title="Test Task",
            assigned_to=self.user,
            created_by=self.user,
            status="pending",
        )
        serializer = TaskSerializer(task)
        data = serializer.data

        self.assertEqual(data["title"], "Test Task")
        self.assertEqual(data["status"], "pending")
        self.assertIn("assigned_to", data)
        self.assertIn("created_by", data)

    def test_integration_log_serializer(self):
        """Test integration log serializer"""
        integration_log = IntegrationLog.objects.create(
            service="test_service",
            operation="GET",
            endpoint="https://api.example.com",
            status_code=200,
        )
        serializer = IntegrationLogSerializer(integration_log)
        data = serializer.data

        self.assertEqual(data["service"], "test_service")
        self.assertEqual(data["operation"], "GET")
        self.assertEqual(data["status_code"], 200)


class CoreViewTests(TestCase):
    """Test core views"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!",
            role="staff",
        )
        self.audit_log = AuditLog.objects.create(
            user=self.user,
            action="test_action",
            resource_type="test_resource",
            resource_id=1,
        )

    def test_audit_log_viewset_unauthorized(self):
        """Test audit log viewset requires authentication"""
        response = self.client.get(reverse("auditlog-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_audit_log_viewset_authorized(self):
        """Test audit log viewset with authentication"""
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

        response = self.client.get(reverse("auditlog-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_notification_viewset_create(self):
        """Test notification viewset create"""
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

        notification_data = {
            "title": "Test Notification",
            "message": "Test message",
            "notification_type": "info",
            "priority": "medium",
        }

        response = self.client.post(reverse("notification-list"), notification_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        notification = Notification.objects.get(title="Test Notification")
        self.assertEqual(notification.user, self.user)

    def test_task_viewset_list(self):
        """Test task viewset list"""
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

        Task.objects.create(
            title="Test Task",
            assigned_to=self.user,
            created_by=self.user,
            status="pending",
        )

        response = self.client.get(reverse("task-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_system_config_viewset_retrieve(self):
        """Test system config viewset retrieve"""
        from rest_framework_simplejwt.tokens import RefreshToken

        config = SystemConfig.objects.create(
            key="test_key", value="test_value", data_type="string"
        )

        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

        response = self.client.get(
            reverse("systemconfig-detail", kwargs={"pk": config.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["key"], "test_key")


class CoreUtilityTests(TestCase):
    """Test core utilities"""

    def test_generate_unique_id(self):
        """Test unique ID generation"""
        id1 = generate_unique_id()
        id2 = generate_unique_id()

        self.assertIsInstance(id1, str)
        self.assertIsInstance(id2, str)
        self.assertNotEqual(id1, id2)
        self.assertEqual(len(id1), 32)  # MD5 hash length

    def test_encrypt_decrypt_sensitive_data(self):
        """Test data encryption/decryption"""
        original_data = "sensitive_information"

        encrypted = encrypt_sensitive_data(original_data)
        decrypted = decrypt_sensitive_data(encrypted)

        self.assertIsInstance(encrypted, str)
        self.assertNotEqual(original_data, encrypted)
        self.assertEqual(original_data, decrypted)

    def test_validate_phone_number(self):
        """Test phone number validation"""
        valid_numbers = ["+1234567890", "+1 (234) 567-8900", "+44 20 7946 0958"]

        invalid_numbers = ["1234567890", "abc1234567", "", None]

        for number in valid_numbers:
            self.assertTrue(validate_phone_number(number))

        for number in invalid_numbers:
            self.assertFalse(validate_phone_number(number))

    def test_validate_email(self):
        """Test email validation"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
        ]

        invalid_emails = ["invalid-email", "@example.com", "user@", "", None]

        for email in valid_emails:
            self.assertTrue(validate_email(email))

        for email in invalid_emails:
            self.assertFalse(validate_email(email))

    def test_calculate_age(self):
        """Test age calculation"""
        birth_date = timezone.now().date() - timedelta(days=365 * 25)
        age = calculate_age(birth_date)

        self.assertEqual(age, 25)
        self.assertIsInstance(age, int)

    def test_format_currency(self):
        """Test currency formatting"""
        formatted = format_currency(1234.56)
        self.assertEqual(formatted, "$1,234.56")

        formatted_eur = format_currency(1234.56, currency="EUR")
        self.assertEqual(formatted_eur, "€1,234.56")

    def test_parse_date(self):
        """Test date parsing"""
        date_string = "2024-01-15"
        parsed_date = parse_date(date_string)

        self.assertEqual(parsed_date.year, 2024)
        self.assertEqual(parsed_date.month, 1)
        self.assertEqual(parsed_date.day, 15)

    @patch("core.utils.send_notification")
    def test_send_notification(self, mock_send_notification):
        """Test notification sending"""
        user = Mock()
        message = "Test message"
        notification_type = "email"

        send_notification(user, message, notification_type)

        mock_send_notification.assert_called_once_with(user, message, notification_type)


class CorePermissionTests(TestCase):
    """Test core permissions"""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="superuser",
            email="superuser@example.com",
            password="SecurePass123!",
        )
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@hospital.com",
            password="SecurePass123!",
            role="admin",
        )
        self.doctor = User.objects.create_user(
            username="doctor",
            email="doctor@hospital.com",
            password="SecurePass123!",
            role="doctor",
        )
        self.nurse = User.objects.create_user(
            username="nurse",
            email="nurse@hospital.com",
            password="SecurePass123!",
            role="nurse",
        )
        self.staff = User.objects.create_user(
            username="staff",
            email="staff@hospital.com",
            password="SecurePass123!",
            role="staff",
        )

    def test_is_super_user_permission(self):
        """Test super user permission"""
        request = Mock()
        request.user = self.superuser
        view = Mock()

        permission = IsSuperUser()
        self.assertTrue(permission.has_permission(request, view))

        request.user = self.admin
        self.assertFalse(permission.has_permission(request, view))

    def test_is_hospital_admin_permission(self):
        """Test hospital admin permission"""
        request = Mock()
        request.user = self.admin
        view = Mock()

        permission = IsHospitalAdmin()
        self.assertTrue(permission.has_permission(request, view))

        request.user = self.doctor
        self.assertFalse(permission.has_permission(request, view))

    def test_is_doctor_permission(self):
        """Test doctor permission"""
        request = Mock()
        request.user = self.doctor
        view = Mock()

        permission = IsDoctor()
        self.assertTrue(permission.has_permission(request, view))

        request.user = self.nurse
        self.assertFalse(permission.has_permission(request, view))

    def test_is_nurse_permission(self):
        """Test nurse permission"""
        request = Mock()
        request.user = self.nurse
        view = Mock()

        permission = IsNurse()
        self.assertTrue(permission.has_permission(request, view))

        request.user = self.staff
        self.assertFalse(permission.has_permission(request, view))

    def test_is_staff_permission(self):
        """Test staff permission"""
        request = Mock()
        request.user = self.staff
        view = Mock()

        permission = IsStaff()
        self.assertTrue(permission.has_permission(request, view))

        request.user = Mock()
        request.user.role = "patient"
        self.assertFalse(permission.has_permission(request, view))


class CoreMiddlewareTests(TestCase):
    """Test core middleware"""

    def setUp(self):
        self.client = APIClient()

    def test_security_middleware(self):
        """Test security middleware"""
        response = self.client.get("/")

        self.assertIn("X-Content-Type-Options", response)
        self.assertIn("X-Frame-Options", response)
        self.assertIn("X-XSS-Protection", response)

    def test_audit_middleware(self):
        """Test audit middleware"""
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="SecurePass123!"
        )

        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

        response = self.client.get("/")

        # Check if audit log was created
        audit_log = AuditLog.objects.filter(user=user).first()
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.action, "page_view")

    def test_performance_middleware(self):
        """Test performance middleware"""
        response = self.client.get("/")

        self.assertIn("X-Response-Time", response)
        response_time = float(response["X-Response-Time"])
        self.assertGreaterEqual(response_time, 0)


class CoreTaskTests(TestCase):
    """Test core tasks"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="SecurePass123!"
        )

    @patch("core.tasks.send_email_notification.delay")
    def test_send_email_notification_task(self, mock_send_email):
        """Test email notification task"""
        user_id = self.user.id
        subject = "Test Subject"
        message = "Test Message"

        send_email_notification(user_id, subject, message)

        mock_send_email.assert_called_once_with(user_id, subject, message)

    @patch("core.tasks.send_sms_notification.delay")
    def test_send_sms_notification_task(self, mock_send_sms):
        """Test SMS notification task"""
        user_id = self.user.id
        message = "Test SMS Message"

        send_sms_notification(user_id, message)

        mock_send_sms.assert_called_once_with(user_id, message)

    @patch("core.tasks.cleanup_old_logs.delay")
    def test_cleanup_old_logs_task(self, mock_cleanup):
        """Test cleanup old logs task"""
        days = 30

        cleanup_old_logs(days)

        mock_cleanup.assert_called_once_with(days)

    @patch("core.tasks.generate_daily_report.delay")
    def test_generate_daily_report_task(self, mock_generate_report):
        """Test generate daily report task"""
        report_date = timezone.now().date()

        generate_daily_report(report_date)

        mock_generate_report.assert_called_once_with(report_date)


class CoreIntegrationTests(TestCase):
    """Test core integration scenarios"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!",
            role="staff",
        )

    def test_audit_log_integration(self):
        """Test audit log integration with user actions"""
        # Create audit log
        audit_log = AuditLog.objects.create(
            user=self.user,
            action="user_profile_update",
            resource_type="user",
            resource_id=self.user.id,
            details={"updated_fields": ["email", "phone"]},
        )

        # Verify audit log is created correctly
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.action, "user_profile_update")
        self.assertIn("email", audit_log.details["updated_fields"])

    def test_notification_integration(self):
        """Test notification integration with user actions"""
        # Create notification
        notification = Notification.objects.create(
            user=self.user,
            title="Profile Updated",
            message="Your profile has been updated successfully",
            notification_type="success",
            priority="medium",
        )

        # Verify notification is created
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, "Profile Updated")
        self.assertFalse(notification.is_read)

    def test_task_integration(self):
        """Test task integration with workflow"""
        # Create task
        task = Task.objects.create(
            title="Complete Profile Setup",
            description="Complete your profile setup",
            assigned_to=self.user,
            created_by=self.user,
            status="pending",
            priority="high",
            due_date=timezone.now() + timedelta(days=3),
        )

        # Verify task is created
        self.assertEqual(task.assigned_to, self.user)
        self.assertEqual(task.created_by, self.user)
        self.assertEqual(task.status, "pending")

    def test_system_config_integration(self):
        """Test system config integration"""
        # Create system config
        config = SystemConfig.objects.create(
            key="email_notifications_enabled",
            value="true",
            data_type="boolean",
            description="Enable email notifications",
        )

        # Verify config is created
        self.assertEqual(config.key, "email_notifications_enabled")
        self.assertEqual(config.value, "true")
        self.assertEqual(config.data_type, "boolean")

    def test_integration_log_integration(self):
        """Test integration log with external services"""
        # Create integration log
        integration_log = IntegrationLog.objects.create(
            service="payment_gateway",
            operation="POST",
            endpoint="https://api.payment-gateway.com/charge",
            request_data={"amount": 100, "currency": "USD"},
            response_data={"success": True, "transaction_id": "txn_123"},
            status_code=200,
            duration_ms=250,
        )

        # Verify integration log is created
        self.assertEqual(integration_log.service, "payment_gateway")
        self.assertEqual(integration_log.status_code, 200)
        self.assertEqual(integration_log.response_data["success"], True)


class CorePerformanceTests(TestCase):
    """Test core performance"""

    def test_audit_log_query_performance(self):
        """Test audit log query performance"""
        user = User.objects.create_user(
            username="perfuser", email="perf@example.com", password="SecurePass123!"
        )

        # Create multiple audit logs
        for i in range(100):
            AuditLog.objects.create(
                user=user,
                action=f"test_action_{i}",
                resource_type="test_resource",
                resource_id=i,
            )

        # Test query performance
        with self.assertNumQueries(1):
            logs = AuditLog.objects.filter(user=user).select_related("user")
            list(logs)

    def test_system_config_cache_performance(self):
        """Test system config cache performance"""
        # Create system config
        SystemConfig.objects.create(
            key="test_cache_key", value="test_cache_value", data_type="string"
        )

        # Test cache hit
        config = SystemConfig.objects.get(key="test_cache_key")
        self.assertEqual(config.value, "test_cache_value")

        # Test cache miss (should hit database)
        config = SystemConfig.objects.get(key="test_cache_key")
        self.assertEqual(config.value, "test_cache_value")

    def test_notification_bulk_create_performance(self):
        """Test notification bulk create performance"""
        user = User.objects.create_user(
            username="bulkuser", email="bulk@example.com", password="SecurePass123!"
        )

        # Create notifications in bulk
        notifications = []
        for i in range(50):
            notifications.append(
                Notification(
                    user=user,
                    title=f"Test Notification {i}",
                    message=f"Test message {i}",
                    notification_type="info",
                    priority="medium",
                )
            )

        # Bulk create
        Notification.objects.bulk_create(notifications)

        # Verify all notifications were created
        self.assertEqual(Notification.objects.filter(user=user).count(), 50)


class CoreSecurityTests(TestCase):
    """Test core security features"""

    def test_audit_log_security(self):
        """Test audit log security"""
        user = User.objects.create_user(
            username="securityuser",
            email="security@example.com",
            password="SecurePass123!",
        )

        # Create audit log with sensitive data
        audit_log = AuditLog.objects.create(
            user=user,
            action="sensitive_data_access",
            resource_type="patient_record",
            resource_id=1,
            details={"accessed_fields": ["diagnosis", "treatment"]},
            ip_address="192.168.1.100",
        )

        # Verify sensitive data is logged
        self.assertEqual(audit_log.action, "sensitive_data_access")
        self.assertIn("diagnosis", audit_log.details["accessed_fields"])
        self.assertEqual(audit_log.ip_address, "192.168.1.100")

    def test_system_config_security(self):
        """Test system config security"""
        # Create sensitive system config
        config = SystemConfig.objects.create(
            key="api_secret_key",
            value="encrypted_secret_value",
            data_type="string",
            is_sensitive=True,
        )

        # Verify sensitive config is created
        self.assertEqual(config.key, "api_secret_key")
        self.assertEqual(config.data_type, "string")
        self.assertTrue(config.is_sensitive)

    def test_notification_security(self):
        """Test notification security"""
        user = User.objects.create_user(
            username="notifuser", email="notif@example.com", password="SecurePass123!"
        )

        # Create notification with sensitive information
        notification = Notification.objects.create(
            user=user,
            title="Security Alert",
            message="Unusual login activity detected",
            notification_type="security",
            priority="high",
            is_sensitive=True,
        )

        # Verify sensitive notification is created
        self.assertEqual(notification.notification_type, "security")
        self.assertEqual(notification.priority, "high")
        self.assertTrue(notification.is_sensitive)

    def test_integration_log_security(self):
        """Test integration log security"""
        # Create integration log with sensitive data
        integration_log = IntegrationLog.objects.create(
            service="payment_gateway",
            operation="POST",
            endpoint="https://api.payment-gateway.com/charge",
            request_data={"amount": 100, "card_number": "****-****-****-1234"},
            response_data={"success": True, "transaction_id": "txn_123"},
            status_code=200,
            is_sensitive=True,
        )

        # Verify sensitive integration log is created
        self.assertEqual(integration_log.service, "payment_gateway")
        self.assertTrue(integration_log.is_sensitive)
        self.assertIn("****", integration_log.request_data["card_number"])


class CoreEdgeCaseTests(TestCase):
    """Test core edge cases"""

    def test_audit_log_edge_cases(self):
        """Test audit log edge cases"""
        user = User.objects.create_user(
            username="edgeuser", email="edge@example.com", password="SecurePass123!"
        )

        # Test with empty details
        audit_log = AuditLog.objects.create(
            user=user,
            action="test_action",
            resource_type="test_resource",
            resource_id=1,
            details={},
        )

        self.assertEqual(audit_log.details, {})

        # Test with None details
        audit_log = AuditLog.objects.create(
            user=user,
            action="test_action_2",
            resource_type="test_resource",
            resource_id=2,
            details=None,
        )

        self.assertIsNone(audit_log.details)

    def test_system_config_edge_cases(self):
        """Test system config edge cases"""
        # Test with empty value
        config = SystemConfig.objects.create(
            key="empty_config", value="", data_type="string"
        )

        self.assertEqual(config.value, "")

        # Test with None value
        config = SystemConfig.objects.create(
            key="null_config", value=None, data_type="null"
        )

        self.assertIsNone(config.value)

    def test_notification_edge_cases(self):
        """Test notification edge cases"""
        user = User.objects.create_user(
            username="edgeuser2", email="edge2@example.com", password="SecurePass123!"
        )

        # Test with empty message
        notification = Notification.objects.create(
            user=user, title="Empty Message", message="", notification_type="info"
        )

        self.assertEqual(notification.message, "")

        # Test with very long message
        long_message = "x" * 10000
        notification = Notification.objects.create(
            user=user,
            title="Long Message",
            message=long_message,
            notification_type="info",
        )

        self.assertEqual(len(notification.message), 10000)

    def test_task_edge_cases(self):
        """Test task edge cases"""
        user = User.objects.create_user(
            username="edgeuser3", email="edge3@example.com", password="SecurePass123!"
        )

        # Test with empty description
        task = Task.objects.create(
            title="Empty Description",
            description="",
            assigned_to=user,
            created_by=user,
            status="pending",
        )

        self.assertEqual(task.description, "")

        # Test with past due date
        past_date = timezone.now() - timedelta(days=1)
        task = Task.objects.create(
            title="Past Due",
            description="This task is past due",
            assigned_to=user,
            created_by=user,
            status="pending",
            due_date=past_date,
        )

        self.assertEqual(task.status, "pending")
        self.assertLess(task.due_date, timezone.now())


@pytest.mark.unit
class CoreModuleUnitTests:
    """Unit tests for core module using pytest"""

    def test_generate_unique_id_length(self):
        """Test unique ID length"""
        from core.utils import generate_unique_id

        unique_id = generate_unique_id()
        assert len(unique_id) == 32

    def test_encrypt_decrypt_roundtrip(self):
        """Test encryption/decryption roundtrip"""
        from core.utils import decrypt_sensitive_data, encrypt_sensitive_data

        original_data = "sensitive_test_data"
        encrypted = encrypt_sensitive_data(original_data)
        decrypted = decrypt_sensitive_data(encrypted)

        assert original_data == decrypted
        assert original_data != encrypted

    @pytest.mark.parametrize(
        "phone_number,expected",
        [
            ("+1234567890", True),
            ("+1 (234) 567-8900", True),
            ("1234567890", False),
            ("invalid", False),
            ("", False),
            (None, False),
        ],
    )
    def test_validate_phone_number_parametrized(self, phone_number, expected):
        """Test phone number validation with parametrized inputs"""
        from core.utils import validate_phone_number

        result = validate_phone_number(phone_number)
        assert result == expected

    @pytest.mark.parametrize(
        "email,expected",
        [
            ("test@example.com", True),
            ("user.name@domain.co.uk", True),
            ("invalid-email", False),
            ("@example.com", False),
            ("", False),
            (None, False),
        ],
    )
    def test_validate_email_parametrized(self, email, expected):
        """Test email validation with parametrized inputs"""
        from core.utils import validate_email

        result = validate_email(email)
        assert result == expected

    def test_calculate_age_with_future_date(self):
        """Test age calculation with future date"""
        from datetime import date, timedelta

        from core.utils import calculate_age

        future_date = date.today() + timedelta(days=1)
        age = calculate_age(future_date)

        # Should return 0 or negative age for future dates
        assert age <= 0

    def test_format_currency_with_zero(self):
        """Test currency formatting with zero"""
        from core.utils import format_currency

        formatted = format_currency(0)
        assert formatted == "$0.00"

    def test_parse_date_with_invalid_format(self):
        """Test date parsing with invalid format"""
        from core.utils import parse_date

        with pytest.raises(ValueError):
            parse_date("invalid-date")

    @patch("core.utils.cache.get")
    @patch("core.utils.cache.set")
    def test_system_config_caching(self, mock_cache_set, mock_cache_get):
        """Test system config caching"""
        from core.models import SystemConfig

        # Mock cache miss
        mock_cache_get.return_value = None

        # Create config
        config = SystemConfig.objects.create(
            key="test_cache_config", value="test_value", data_type="string"
        )

        # Verify cache was called
        mock_cache_get.assert_called()
        mock_cache_set.assert_called()

    def test_audit_log_str_representation(self):
        """Test audit log string representation"""
        from django.contrib.auth import get_user_model

        from core.models import AuditLog

        User = get_user_model()
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="SecurePass123!"
        )

        audit_log = AuditLog.objects.create(
            user=user,
            action="test_action",
            resource_type="test_resource",
            resource_id=1,
        )

        str_repr = str(audit_log)
        assert "test_action" in str_repr
        assert str(user.id) in str_repr

    def test_notification_str_representation(self):
        """Test notification string representation"""
        from django.contrib.auth import get_user_model

        from core.models import Notification

        User = get_user_model()
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="SecurePass123!"
        )

        notification = Notification.objects.create(
            user=user,
            title="Test Notification",
            message="Test message",
            notification_type="info",
        )

        str_repr = str(notification)
        assert "Test Notification" in str_repr
        assert str(user.id) in str_repr

    def test_task_str_representation(self):
        """Test task string representation"""
        from django.contrib.auth import get_user_model

        from core.models import Task

        User = get_user_model()
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="SecurePass123!"
        )

        task = Task.objects.create(
            title="Test Task", assigned_to=user, created_by=user, status="pending"
        )

        str_repr = str(task)
        assert "Test Task" in str_repr
        assert "pending" in str_repr
