from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.test import TestCase

from ..app.tasks import check_expiry_alerts, purge_old_audit_logs, send_sms_expiry_alert


@pytest.mark.django_db
class TestCeleryTasks(TestCase):
    def setUp(self):
        from ..app.models import BloodInventory, Donor

        self.donor = Donor.objects.create(
            name="Test Donor",
            dob="01/01/1980",
            ssn="123-45-6789",
            address="123 Test St",
            contact="1234567890",
            blood_type="O+",
            is_active=True,
        )

    @patch("django.core.mail.send_mail")
    @patch("..app.tasks.send_sms_expiry_alert")
    def test_check_expiry_alerts(self, mock_sms, mock_email):
        # Create expiring inventory
        BloodInventory.objects.create(
            donor=self.donor,
            blood_type="O+",
            unit_id="EXP-001",
            expiry_date=date.today() + timedelta(days=5),
            status="AVAILABLE",
            quantity=1,
        )

        # Run task
        result = check_expiry_alerts.delay()

        # Verify email was sent
        mock_email.assert_called_once()

        # Verify SMS was sent
        mock_sms.assert_called_once()

    @patch("django.core.mail.send_mail")
    def test_purge_old_audit_logs(self, mock_email):
        from auditlog.models import LogEntry
        from django.utils import timezone

        # Create old audit log (older than 365 days)
        old_log = LogEntry.objects.create(
            timestamp=timezone.now() - timedelta(days=400),
            actor="test_user",
            action="TEST_ACTION",
            object_id=1,
            object_repr="Test object",
            content_type_id=1,
            changes={},
        )

        # Run purge task
        result = purge_old_audit_logs.delay()

        # Verify old log was deleted
        assert not LogEntry.objects.filter(pk=old_log.pk).exists()

        # Verify email was sent
        mock_email.assert_called_once()

    def test_send_sms_expiry_alert(self):
        # Test SMS alert function
        with patch("logging.getLogger") as mock_logger:
            result = send_sms_expiry_alert(5)
            assert result is True
            mock_logger().info.assert_called()
