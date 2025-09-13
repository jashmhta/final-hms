import json
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from insurance_tpa.models import InsuranceProvider, Patient, TPAAuthorization, TPAClaim

User = get_user_model()


class TestTPAMockIntegration:
    """
    Test suite for TPA integration with mocked external dependencies.
    Tests claim creation, authorization processing, and API integration.
    """

    @pytest.fixture(autouse=True)
    def setup_test_data(
        self, db, mock_tpa_api, mock_celery_task, mock_redis_connection
    ):
        """Setup test data and mocks for all tests."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

        # Create insurance provider
        self.insurance_provider = InsuranceProvider.objects.create(
            name="Test Insurance",
            provider_code="TEST001",
            contact_email="test@insurance.com",
            is_active=True,
        )

        # Create mock patient
        self.patient = Patient.objects.create(
            patient_id="PAT001",
            first_name="John",
            last_name="Doe",
            date_of_birth="1990-01-01",
            insurance_number="INS123456",
        )

    def test_create_tpa_claim(self, db, mock_tpa_api):
        """Test TPA claim creation with mock patient."""
        # Create claim data
        claim_data = {
            "claim_id": "CLAIM001",
            "patient_id": self.patient.patient_id,
            "insurance_provider": self.insurance_provider.id,
            "amount": 1500.00,
            "description": "Emergency medical treatment",
            "status": "pending",
        }

        # Test model creation
        claim = TPAClaim.objects.create(**claim_data, created_by=self.user)

        # Verify claim was created correctly
        assert claim.claim_id == "CLAIM001"
        assert claim.patient == self.patient
        assert claim.amount == 1500.00
        assert claim.status == "pending"
        assert claim.created_by == self.user

        # Verify foreign key relationships
        assert claim.insurance_provider == self.insurance_provider

    def test_tpa_authorization_creation(self, db):
        """Test TPA authorization creation linked to claim."""
        # Create claim first
        claim = TPAClaim.objects.create(
            claim_id="AUTHCLAIM001",
            patient=self.patient,
            insurance_provider=self.insurance_provider,
            amount=2000.00,
            status="pending",
            created_by=self.user,
        )

        # Create authorization
        auth = TPAAuthorization.objects.create(
            auth_id="AUTH001",
            claim=claim,
            authorized_amount=1800.00,
            approval_status="approved",
            approved_by=self.user,
        )

        # Verify authorization
        assert auth.auth_id == "AUTH001"
        assert auth.claim == claim
        assert auth.authorized_amount == 1800.00
        assert auth.approval_status == "approved"
        assert auth.approved_by == self.user

        # Verify claim status updated
        claim.refresh_from_db()
        assert claim.status == "approved"

    @patch("requests.post")
    def test_tpa_api_integration(self, mock_post, db):
        """Test integration with external TPA API."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "data": {
                "claim_id": "API001",
                "approved_amount": 1200.00,
                "approval_status": "approved",
            },
        }
        mock_post.return_value = mock_response

        # Create claim and send to TPA
        claim = TPAClaim.objects.create(
            claim_id="API001",
            patient=self.patient,
            insurance_provider=self.insurance_provider,
            amount=1500.00,
            status="pending",
            created_by=self.user,
        )

        # Mock the TPA integration service call
        with patch(
            "insurance_tpa.services.tpa_integration.submit_claim_to_tpa"
        ) as mock_submit:
            mock_submit.return_value = {
                "success": True,
                "data": mock_response.json.return_value["data"],
            }

            result = mock_submit(claim=claim)

        # Verify API was called
        mock_post.assert_called_once()

        # Verify response processing
        assert result["success"] is True
        assert result["data"]["claim_id"] == "API001"
        assert result["data"]["approved_amount"] == 1200.00

        # Verify claim status updated
        claim.refresh_from_db()
        assert claim.status == "approved"

    def test_insurance_provider_validation(self, db):
        """Test insurance provider validation and creation."""
        # Test provider creation
        provider_data = {
            "name": "Valid Insurance Co",
            "provider_code": "VAL001",
            "contact_email": "valid@insurance.com",
            "is_active": True,
        }

        provider = InsuranceProvider.objects.create(**provider_data)

        # Verify provider
        assert provider.name == "Valid Insurance Co"
        assert provider.provider_code == "VAL001"
        assert provider.contact_email == "valid@insurance.com"
        assert provider.is_active is True

        # Test inactive provider
        inactive_provider = InsuranceProvider.objects.create(
            name="Inactive Insurance",
            provider_code="INACT001",
            contact_email="inactive@insurance.com",
            is_active=False,
        )

        assert inactive_provider.is_active is False

    def test_patient_integration(self, db):
        """Test patient model integration with TPA claims."""
        # Create multiple patients
        patients = [
            Patient.objects.create(
                patient_id=f"PAT{i:03d}",
                first_name=f"Patient{i}",
                last_name="Test",
                date_of_birth="1990-01-01",
                insurance_number=f"INS{i:06d}",
            )
            for i in range(1, 4)
        ]

        # Create claims for each patient
        claims = []
        for patient in patients:
            claim = TPAClaim.objects.create(
                claim_id=f"PATCLAIM{patient.patient_id}",
                patient=patient,
                insurance_provider=self.insurance_provider,
                amount=1000.00 + len(patients) * 100,
                status="pending",
                created_by=self.user,
            )
            claims.append(claim)

        # Verify relationships
        for claim, patient in zip(claims, patients):
            assert claim.patient == patient
            assert patient.patient_id in claim.claim_id

        # Test patient info retrieval
        for patient in patients:
            patient_info = patient.get_insurance_info()
            assert patient_info["patient_id"] == patient.patient_id
            assert patient_info["insurance_number"] == patient.insurance_number
            assert (
                patient_info["full_name"] == f"{patient.first_name} {patient.last_name}"
            )

    @patch("celery.task.base.Task.apply_async")
    def test_celery_task_integration(self, mock_celery, db):
        """Test Celery task integration for background processing."""
        # Create claim that should trigger Celery task
        claim = TPAClaim.objects.create(
            claim_id="CELERY001",
            patient=self.patient,
            insurance_provider=self.insurance_provider,
            amount=2500.00,
            status="pending",
            created_by=self.user,
        )

        # Mock the task that processes claims
        with patch("insurance_tpa.tasks.process_tpa_claim") as mock_process:
            mock_process.delay.return_value = Mock()

            # Trigger task
            mock_process.delay(claim_id=claim.claim_id)

        # Verify Celery task was called
        mock_celery.assert_called()
        mock_process.delay.assert_called_once_with(claim.claim_id)

        # Verify task result
        result = mock_process.delay.return_value
        assert result.get() is not None

    def test_redis_cache_integration(self, db, mock_redis_connection):
        """Test Redis cache integration for claim data."""
        # Create claim
        claim = TPAClaim.objects.create(
            claim_id="CACHE001",
            patient=self.patient,
            insurance_provider=self.insurance_provider,
            amount=1800.00,
            status="approved",
            created_by=self.user,
        )

        # Cache claim data
        cache_key = f"tpa:claim:{claim.claim_id}"
        cache_data = {
            "claim_id": claim.claim_id,
            "patient_id": claim.patient.patient_id,
            "amount": float(claim.amount),
            "status": claim.status,
        }

        # Test cache set/get
        cache.set(cache_key, cache_data, timeout=3600)
        retrieved_data = cache.get(cache_key)

        # Verify cache functionality
        assert retrieved_data["claim_id"] == claim.claim_id
        assert retrieved_data["patient_id"] == claim.patient.patient_id
        assert retrieved_data["amount"] == float(claim.amount)
        assert retrieved_data["status"] == claim.status

        # Verify Redis mock
        mock_redis_connection.set.assert_called()
        mock_redis_connection.get.assert_called()

    def test_error_handling(self, db, mock_tpa_api):
        """Test error handling for failed TPA integrations."""
        # Mock API failure
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {
            "error": "TPA service unavailable",
            "status": "error",
        }

        with patch("requests.post") as mock_post:
            mock_post.return_value = mock_response

            # Create claim that should fail
            claim_data = {
                "claim_id": "ERROR001",
                "patient_id": self.patient.patient_id,
                "insurance_provider": self.insurance_provider.id,
                "amount": 1000.00,
                "description": "Test error handling",
                "status": "pending",
            }

            # Test that claim can still be created even if API fails
            claim = TPAClaim.objects.create(**claim_data, created_by=self.user)
            assert (
                claim.status == "pending"
            )  # Status should not change on creation failure

        # Verify API error was received
        mock_post.assert_called_once()

    def test_database_transaction_rollback(self, db):
        """Test database transaction rollback on test failure."""
        # Create initial count
        initial_claim_count = TPAClaim.objects.count()
        initial_patient_count = Patient.objects.count()

        # Create objects
        TPAClaim.objects.create(
            claim_id="TXN001",
            patient=self.patient,
            insurance_provider=self.insurance_provider,
            amount=500.00,
            status="pending",
            created_by=self.user,
        )

        # Verify objects created
        assert TPAClaim.objects.count() == initial_claim_count + 1
        assert Patient.objects.count() == initial_patient_count

        # After test, database should be rolled back
        # This is handled by pytest-django automatically
        # But verify that we can create again
        TPAClaim.objects.create(
            claim_id="TXN002",
            patient=self.patient,
            insurance_provider=self.insurance_provider,
            amount=600.00,
            status="pending",
            created_by=self.user,
        )

        assert (
            TPAClaim.objects.count() == initial_claim_count + 1
        )  # Should still be +1 from first creation
