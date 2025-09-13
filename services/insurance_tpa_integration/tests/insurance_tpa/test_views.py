from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from fakeredis import FakeStrictRedis
from insurance_tpa.factories.factories import *
from insurance_tpa.models import Claim, PreAuth
from insurance_tpa.views import ClaimViewSet, PreAuthViewSet
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

User = get_user_model()


@pytest.mark.django_db
class TestPreAuthViews(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.patient = PatientFactory()
        self.client.force_authenticate(user=self.user)
        self.url = reverse("preauth-list")
        self.redis_mock = FakeStrictRedis()

    @mock.patch("insurance_tpa.tasks.submit_tpa_request.delay")
    def test_create_preauth_success(self, mock_celery_task):
        """Test successful pre-auth creation with Celery task trigger."""
        data = {
            "patient_id": self.patient.patient_id,
            "claim_amount": 50000.00,
            "procedures": "Procedure1,Procedure2",
        }

        response = self.client.post(self.url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert PreAuth.objects.count() == 1
        preauth = PreAuth.objects.first()
        assert preauth.claim_amount == 50000.00
        assert preauth.status == "pending"
        mock_celery_task.assert_called_once_with(preauth.id)

    def test_create_preauth_rate_limit_exceeded(self):
        """Test rate limiting for pre-auth creation (5/min)."""
        data = {
            "patient_id": self.patient.patient_id,
            "claim_amount": 50000.00,
            "procedures": "Procedure1",
        }

        # Make 6 requests to exceed 5/min limit
        for i in range(6):
            response = self.client.post(self.url, data, format="json")
            if i >= 5:
                assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
                assert "Rate limit exceeded" in response.data["detail"]
            else:
                assert response.status_code == status.HTTP_201_CREATED

    def test_list_preauth_unauthenticated(self):
        """Test pre-auth list requires authentication."""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_preauth_invalid_amount(self):
        """Test validation for invalid amounts (negative, over 1M)."""
        data = {
            "patient_id": self.patient.patient_id,
            "claim_amount": -100.00,
            "procedures": "Procedure1",
        }
        response = self.client.post(self.url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "claim_amount" in response.data

        # Test amount over 1M limit
        data["claim_amount"] = 2000000.00
        response = self.client.post(self.url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @mock.patch("redis.Redis")
    def test_preauth_list_caching(self, mock_redis):
        """Test Redis caching for pre-auth list."""
        mock_redis_instance = mock_redis.return_value
        mock_redis_instance.get.return_value = None

        response1 = self.client.get(self.url)

        # First request should cache
        mock_redis_instance.set.assert_called()

        # Second request should use cache
        mock_redis_instance.get.return_value = b"cached_response"
        response2 = self.client.get(self.url)
        assert response1.data == response2.data


@pytest.mark.django_db
class TestClaimViews(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.patient = PatientFactory()
        self.client.force_authenticate(user=self.user)
        self.create_url = reverse("claim-list")
        self.status_url = reverse("claim-status", kwargs={"pk": 1})

    @mock.patch("insurance_tpa.tasks.submit_tpa_request.delay")
    def test_create_claim_success(self, mock_celery_task):
        """Test successful claim creation with Celery task."""
        data = {
            "patient_id": self.patient.patient_id,
            "billed_amount": 25000.00,
            "procedures": "Proc1,Proc2,Proc3",
            "diagnosis": "Test diagnosis",
        }

        response = self.client.post(self.create_url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Claim.objects.count() == 1
        claim = Claim.objects.first()
        assert claim.billed_amount == 25000.00
        assert claim.status == "pending"
        mock_celery_task.assert_called_once_with(claim.id)

    def test_create_claim_rate_limit_exceeded(self):
        """Test rate limiting for claim creation (3/min)."""
        data = {
            "patient_id": self.patient.patient_id,
            "billed_amount": 25000.00,
            "procedures": "Proc1",
            "diagnosis": "Test",
        }

        # Make 4 requests to exceed 3/min limit
        for i in range(4):
            response = self.client.post(self.create_url, data, format="json")
            if i >= 3:
                assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            else:
                assert response.status_code == status.HTTP_201_CREATED

    def test_claim_status_caching(self):
        """Test Redis caching for claim status endpoint."""
        claim = ClaimFactory(patient=self.patient, created_by=self.user)
        url = reverse("claim-status", kwargs={"pk": claim.id})

        with mock.patch("redis.Redis") as mock_redis:
            mock_redis_instance = mock_redis.return_value
            mock_redis_instance.get.return_value = None

            # First request caches
            response1 = self.client.get(url)
            mock_redis_instance.set.assert_called()

            # Second request uses cache
            mock_redis_instance.get.return_value = b'{"status": "pending"}'
            response2 = self.client.get(url)
            assert response1.data["status"] == response2.data["status"]

    def test_create_claim_too_many_procedures(self):
        """Test validation for too many procedures (max 10)."""
        procedures = ", ".join([f"Proc{i}" for i in range(11)])
        data = {
            "patient_id": self.patient.patient_id,
            "billed_amount": 25000.00,
            "procedures": procedures,
            "diagnosis": "Test",
        }

        response = self.client.post(self.create_url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "procedures" in response.data

    def test_claim_sql_injection_protection(self):
        """Test SQL injection protection through ORM."""
        malicious_data = {
            "patient_id": self.patient.patient_id,
            "billed_amount": 25000.00,
            "procedures": "' OR '1'='1",
            "diagnosis": "'; DROP TABLE claims; --",
        }

        response = self.client.post(self.create_url, malicious_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        # Verify no actual SQL injection occurred
        assert Claim.objects.filter(procedures="' OR '1'='1").exists()
        # Database should still be intact


@pytest.mark.django_db
class TestReimbursementViews(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.patient = PatientFactory()
        self.claim = ClaimFactory(patient=self.patient, created_by=self.user)
        self.client.force_authenticate(user=self.user)
        self.url = reverse("reimbursement-list")

    def test_create_reimbursement_success(self):
        """Test successful reimbursement creation."""
        data = {
            "claim_id": self.claim.id,
            "paid_amount": 20000.00,
            "transaction_id": "TXN123456789",
            "payment_date": "2025-01-15",
        }

        response = self.client.post(self.url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert self.claim.reimbursement_set.count() == 1
        reimbursement = self.claim.reimbursement_set.first()
        assert reimbursement.paid_amount == 20000.00
        assert reimbursement.status == "paid"
        assert self.claim.status == "paid"  # Claim status should update

    def test_reimbursement_rate_limiting(self):
        """Test rate limiting for reimbursement creation (2/min)."""
        data = {
            "claim_id": self.claim.id,
            "paid_amount": 20000.00,
            "transaction_id": f"TXN{i}",
            "payment_date": "2025-01-15",
        }

        # Make 3 requests to exceed 2/min limit
        for i in range(3):
            data["transaction_id"] = f"TXN{i}"
            response = self.client.post(self.url, data, format="json")
            if i >= 2:
                assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            else:
                assert response.status_code == status.HTTP_201_CREATED

    def test_duplicate_transaction_id(self):
        """Test duplicate transaction_id validation."""
        data = {
            "claim_id": self.claim.id,
            "paid_amount": 20000.00,
            "transaction_id": "TXN_DUPLICATE",
            "payment_date": "2025-01-15",
        }

        # First creation succeeds
        response1 = self.client.post(self.url, data, format="json")
        assert response1.status_code == status.HTTP_201_CREATED

        # Second creation with same transaction_id fails
        response2 = self.client.post(self.url, data, format="json")
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert "transaction_id" in response2.data
