from datetime import timedelta
from unittest import mock

import pytest
import responses
from celery import current_app
from django.utils import timezone
from fakeredis import FakeStrictRedis
from insurance_tpa.factories.factories import *
from insurance_tpa.models import Claim, PreAuth, Reimbursement
from insurance_tpa.tasks import (
    cleanup_old_records,
    poll_tpa_status,
    send_notification,
    submit_tpa_request,
)


@pytest.mark.django_db
class TestSubmitTPATask:
    def test_submit_tpa_request_success(self):
        """Test successful TPA request submission with mock response."""
        preauth = PreAuthFactory(status="pending")

        with responses.RequestsMock() as rsps:
            # Mock TPA endpoint response
            rsps.add(
                rsps.POST,
                "http://localhost:5000/api/tpa/pre-auth/",
                json={
                    "status": "approved",
                    "approval_id": "APRV123456",
                    "approval_amount": 50000.00,
                },
                status=200,
            )

            result = submit_tpa_request.delay(preauth.id)
            result.get()  # Wait for task completion

            # Verify preauth status updated
            preauth.refresh_from_db()
            assert preauth.status == "approved"
            assert preauth.approval_id == "APRV123456"

    @responses.activate
    def test_submit_tpa_request_failure(self):
        """Test TPA request failure handling with retry logic."""
        preauth = PreAuthFactory(status="pending")

        # Mock TPA endpoint failure
        responses.add(
            responses.POST,
            "http://localhost:5000/api/tpa/pre-auth/",
            json={"error": "Insufficient funds"},
            status=400,
        )

        with pytest.raises(Exception):
            result = submit_tpa_request.delay(preauth.id)
            result.get()

        # Verify status updated to rejected
        preauth.refresh_from_db()
        assert preauth.status == "rejected"

    @mock.patch("redis.Redis")
    def test_submit_tpa_request_caching(self, mock_redis):
        """Test Redis caching during TPA request submission."""
        preauth = PreAuthFactory(status="pending")
        mock_redis_instance = mock_redis.return_value

        result = submit_tpa_request.delay(preauth.id)
        result.get()

        # Verify cache set for status
        mock_redis_instance.set.assert_called_with(
            f"preauth_status:{preauth.id}", mock.ANY, ex=3600  # 1 hour TTL
        )

    def test_submit_tpa_request_network_error(self):
        """Test network error handling with exponential backoff."""
        preauth = PreAuthFactory(status="pending")

        with responses.RequestsMock() as rsps:
            # Mock network error
            rsps.add(
                rsps.POST,
                "http://localhost:5000/api/tpa/pre-auth/",
                exc=requests.exceptions.ConnectionError,
            )

            # Task should retry with backoff
            with mock.patch("celery.app.task.Task.retry") as mock_retry:
                result = submit_tpa_request.delay(preauth.id)
                with pytest.raises(Exception):
                    result.get()
                mock_retry.assert_called_once()


@pytest.mark.django_db
class TestPollTPAStatusTask:
    def test_poll_tpa_status_success(self):
        """Test successful status polling with mock TPA response."""
        preauth = PreAuthFactory(status="pending", approval_id="APRV123456")

        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                "http://localhost:5000/api/tpa/pre-auth/APRV123456/status",
                json={"status": "approved", "processed_amount": 50000.00},
                status=200,
            )

            result = poll_tpa_status.delay(preauth.id)
            result.get()

            preauth.refresh_from_db()
            assert preauth.status == "approved"

    def test_poll_tpa_status_still_pending(self):
        """Test when TPA status is still pending (continue polling)."""
        preauth = PreAuthFactory(status="pending", approval_id="APRV123456")

        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                "http://localhost:5000/api/tpa/pre-auth/APRV123456/status",
                json={"status": "pending"},
                status=200,
            )

            with mock.patch("celery.app.task.Task.retry") as mock_retry:
                result = poll_tpa_status.delay(preauth.id)
                with pytest.raises(Exception):
                    result.get()
                mock_retry.assert_called_once()

    @mock.patch("time.sleep")
    def test_poll_tpa_status_max_retries_exceeded(self, mock_sleep):
        """Test max retry limit exceeded scenario."""
        preauth = PreAuthFactory(status="pending", approval_id="APRV123456")

        with responses.RequestsMock() as rsps:
            # Mock consistent failure
            rsps.add(
                rsps.GET,
                "http://localhost:5000/api/tpa/pre-auth/APRV123456/status",
                json={"error": "Service unavailable"},
                status=503,
            )

            with mock.patch("celery.app.task.Task.retry") as mock_retry:
                mock_retry.side_effect = Exception("Max retries exceeded")

                with pytest.raises(Exception):
                    result = poll_tpa_status.delay(preauth.id)
                    result.get()

                # Verify status set to failed
                preauth.refresh_from_db()
                assert preauth.status == "failed"


@pytest.mark.django_db
class TestSendNotificationTask:
    def test_send_notification_success(self):
        """Test successful notification sending."""
        preauth = PreAuthFactory(status="approved")

        with mock.patch("smtplib.SMTP") as mock_smtp:
            result = send_notification.delay(preauth.id, "approved")
            result.get()

            mock_smtp.return_value.sendmail.assert_called_once()

    def test_send_notification_email_failure(self):
        """Test email sending failure handling."""
        preauth = PreAuthFactory(status="rejected")

        with mock.patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.sendmail.side_effect = Exception("SMTP error")

            result = send_notification.delay(preauth.id, "rejected")
            result.get()  # Should not raise exception (handled gracefully)

            # Verify error logged but task completes
            preauth.refresh_from_db()
            assert preauth.status == "rejected"  # Status unchanged

    def test_send_notification_sms_success(self):
        """Test SMS notification sending (mock Twilio)."""
        preauth = PreAuthFactory(status="approved")

        with mock.patch("twilio.rest.Client") as mock_twilio:
            result = send_notification.delay(preauth.id, "approved", method="sms")
            result.get()

            mock_twilio.return_value.messages.create.assert_called_once()


@pytest.mark.django_db
class TestCleanupOldRecordsTask:
    @pytest.fixture
    def setup_records(self):
        """Create mix of old and recent records for cleanup testing."""
        patient = PatientFactory()
        user = UserFactory()
        claim = ClaimFactory(patient=patient, created_by=user)

        # Old records (>365 days)
        old_date = timezone.now() - timedelta(days=366)
        old_preauth = PreAuthFactory(
            patient=patient, created_by=user, created_at=old_date
        )
        old_claim = ClaimFactory(patient=patient, created_by=user, created_at=old_date)
        old_reimbursement = ReimbursementFactory(claim=old_claim, created_at=old_date)

        # Recent records (<365 days)
        recent_preauth = PreAuthFactory(patient=patient, created_by=user)
        recent_claim = ClaimFactory(patient=patient, created_by=user)
        recent_reimbursement = ReimbursementFactory(claim=recent_claim)

        return {
            "old": {
                "preauth": old_preauth,
                "claim": old_claim,
                "reimbursement": old_reimbursement,
            },
            "recent": {
                "preauth": recent_preauth,
                "claim": recent_claim,
                "reimbursement": recent_reimbursement,
            },
        }

    def test_cleanup_old_records(self, setup_records):
        """Test cleanup removes records older than 365 days."""
        records = setup_records

        # Run cleanup task
        result = cleanup_old_records.delay()
        result.get()

        # Verify old records deleted
        assert not PreAuth.objects.filter(id=records["old"]["preauth"].id).exists()
        assert not Claim.objects.filter(id=records["old"]["claim"].id).exists()
        assert not Reimbursement.objects.filter(
            id=records["old"]["reimbursement"].id
        ).exists()

        # Verify recent records preserved
        assert PreAuth.objects.filter(id=records["recent"]["preauth"].id).exists()
        assert Claim.objects.filter(id=records["recent"]["claim"].id).exists()
        assert Reimbursement.objects.filter(
            id=records["recent"]["reimbursement"].id
        ).exists()

    def test_cleanup_no_old_records(self, setup_records):
        """Test cleanup when no old records exist."""
        # Delete old records manually first
        PreAuth.objects.filter(id=setup_records["old"]["preauth"].id).delete()
        Claim.objects.filter(id=setup_records["old"]["claim"].id).delete()
        Reimbursement.objects.filter(
            id=setup_records["old"]["reimbursement"].id
        ).delete()

        # Run cleanup
        result = cleanup_old_records.delay()
        result.get()

        # Verify recent records still exist
        assert PreAuth.objects.filter(id=setup_records["recent"]["preauth"].id).exists()
        assert Claim.objects.filter(id=setup_records["recent"]["claim"].id).exists()
        assert Reimbursement.objects.filter(
            id=setup_records["recent"]["reimbursement"].id
        ).exists()

    def test_cleanup_edge_case_boundary_date(self):
        """Test cleanup boundary case (exactly 365 days)."""
        patient = PatientFactory()
        user = UserFactory()
        claim = ClaimFactory(patient=patient, created_by=user)

        # Exactly 365 days old - should NOT be deleted
        boundary_date = timezone.now() - timedelta(days=365)
        boundary_preauth = PreAuthFactory(
            patient=patient, created_by=user, created_at=boundary_date
        )

        # Run cleanup
        result = cleanup_old_records.delay()
        result.get()

        # Verify boundary record preserved
        assert PreAuth.objects.filter(id=boundary_preauth.id).exists()


@pytest.mark.django_db
class TestTaskErrorHandling:
    """Test various error scenarios in tasks."""

    def test_task_invalid_object_id(self):
        """Test task handling when object ID is invalid."""
        # Invalid preauth ID
        with pytest.raises(PreAuth.DoesNotExist):
            result = submit_tpa_request.delay(999999)
            result.get()

    def test_task_database_connection_error(self):
        """Test database connection error handling."""
        preauth = PreAuthFactory(status="pending")

        with mock.patch("django.db.transaction.atomic") as mock_atomic:
            mock_atomic.side_effect = Exception("Database connection failed")

            result = submit_tpa_request.delay(preauth.id)
            with pytest.raises(Exception):
                result.get()

            # Verify task marked as failed
            preauth.refresh_from_db()
            assert (
                preauth.status != "pending"
            )  # Should be updated to failed or error state

    def test_task_celery_broker_failure(self):
        """Test Celery broker connection failure."""
        with mock.patch("celery.current_app") as mock_celery:
            mock_celery.send_task.side_effect = Exception("Broker unavailable")

            with pytest.raises(Exception):
                submit_tpa_request.delay(1)

    @mock.patch("logging.Logger.error")
    def test_task_logging_integration(self, mock_logger):
        """Test proper logging integration in tasks."""
        preauth = PreAuthFactory(status="pending")

        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.POST,
                "http://localhost:5000/api/tpa/pre-auth/",
                json={"error": "Validation failed"},
                status=400,
            )

            result = submit_tpa_request.delay(preauth.id)
            result.get()

            # Verify error logged
            mock_logger.assert_called()
            assert "TPA request failed" in mock_logger.call_args[0][0]
