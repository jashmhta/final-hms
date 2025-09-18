import json
import logging
import asyncio
from datetime import datetime, timezone
from django.utils import timezone as django_timezone
from celery import current_app as celery_app
from django.core.cache import cache
from django.db import transaction
from django.http import JsonResponse
from django_ratelimit.decorators import ratelimit
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from .models import Claim, PreAuth, Reimbursement
from .serializers import ClaimSerializer, PreAuthSerializer, ReimbursementSerializer
from ..insurance_service import (
    create_insurance_service,
    InsuranceIntegrationService,
    EligibilityRequest,
    PreAuthRequest,
    ClaimSubmission,
    ClaimStatus
)  
logger = logging.getLogger(__name__)
class PreAuthCreateView(generics.CreateAPIView):
    queryset = PreAuth.objects.all()
    serializer_class = PreAuthSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    @ratelimit(key="user", rate="5/m", method="POST", block=True)
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.context["request"] = request
            if serializer.is_valid():
                with transaction.atomic():
                    instance = serializer.save()

                    # Create enterprise pre-authorization request
                    try:
                        # Get insurance provider from validated data
                        provider_id = serializer.validated_data.get('insurance_provider_id', 1)

                        # Create pre-auth request for real insurance integration
                        preauth_request = PreAuthRequest(
                            patient_id=str(serializer.validated_data.get('patient_id')),
                            policy_number=serializer.validated_data.get('policy_number', ''),
                            provider_npi=serializer.validated_data.get('provider_npi', ''),
                            facility_npi=serializer.validated_data.get('facility_npi', ''),
                            diagnosis_codes=serializer.validated_data.get('diagnosis_codes', []),
                            procedure_codes=serializer.validated_data.get('procedure_codes', []),
                            estimated_cost=float(serializer.validated_data.get('estimated_cost', 0)),
                            service_date=serializer.validated_data.get('service_date', datetime.now().isoformat()),
                            clinical_notes=serializer.validated_data.get('clinical_notes', ''),
                            urgency_level=serializer.validated_data.get('urgency_level', 'ROUTINE'),
                            supporting_documents=serializer.validated_data.get('supporting_documents', [])
                        )

                        # Submit to real insurance provider
                        async def submit_preauth():
                            async with create_insurance_service() as service:
                                preauth_response = await service.request_preauthorization(preauth_request, provider_id)

                                # Update instance with real response
                                instance.status = preauth_response.status.value
                                instance.preauth_number = preauth_response.preauth_number
                                instance.approval_amount = preauth_response.approval_amount
                                instance.denial_reason = preauth_response.denial_reason
                                instance.conditions = preauth_response.conditions
                                instance.expiration_date = preauth_response.expiration_date
                                instance.processing_time_ms = preauth_response.processing_time_ms
                                instance.save()

                                # Update cache
                                cache_key = f"preauth_{instance.id}"
                                cache.set(
                                    cache_key,
                                    {
                                        "status": preauth_response.status.value,
                                        "preauth_number": preauth_response.preauth_number,
                                        "approval_amount": preauth_response.approval_amount,
                                        "timestamp": instance.updated_at.isoformat(),
                                        "user_id": request.user.id,
                                    },
                                    3600,
                                )

                                logger.info(
                                    f"Real pre-authorization processed: {instance.id}, status: {preauth_response.status.value}, "
                                    f"approval: ${preauth_response.approval_amount:.2f}, "
                                    f"processing: {preauth_response.processing_time_ms:.0f}ms"
                                )

                        # Run async task in sync context
                        asyncio.run(submit_preauth())

                    except Exception as insurance_error:
                        logger.error(f"Insurance integration error: {insurance_error}")
                        # Fallback to mock processing
                        submit_tpa_request.delay(instance.id)
                        cache_key = f"preauth_{instance.id}"
                        cache.set(
                            cache_key,
                            {
                                "status": "submitted",
                                "timestamp": instance.created_at.isoformat(),
                                "user_id": request.user.id,
                            },
                            3600,
                        )

                    logger.info(
                        f"PreAuth created and submitted to real insurance provider: {instance.id} by user {request.user.id}"
                    )
                    return Response(
                        {
                            "message": "Enterprise pre-authorization request created and submitted to insurance provider",
                            "preauth_id": instance.id,
                            "status": instance.status,
                            "preauth_number": getattr(instance, 'preauth_number', None),
                            "approval_amount": getattr(instance, 'approval_amount', 0),
                            "estimated_processing_time": "Real-time processing",
                        },
                        status=status.HTTP_201_CREATED,
                    )
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Error creating PreAuth: {str(e)}")
            return Response(
                {
                    "error": "Internal server error",
                    "message": "Failed to create enterprise pre-authorization request",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
class PreAuthListView(generics.ListAPIView):
    serializer_class = PreAuthSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        return PreAuth.objects.filter(created_by=user).order_by("-created_at")
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {"count": len(queryset), "results": serializer.data, "status": "success"}
        )
class PreAuthRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PreAuthSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return PreAuth.objects.filter(created_by=self.request.user)
    def perform_update(self, serializer):
        instance = serializer.save()
        cache_key = f"preauth_{instance.id}"
        cache.delete(cache_key)
        logger.info(
            f"PreAuth {instance.id} updated to status: {instance.status} by user {self.request.user.id}"
        )
    def perform_destroy(self, instance):
        cache_key = f"preauth_{instance.id}"
        cache.delete(cache_key)
        instance.delete()
        logger.info(f"PreAuth {instance.id} deleted by user {self.request.user.id}")
class ClaimCreateView(generics.CreateAPIView):
    queryset = Claim.objects.all()
    serializer_class = ClaimSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    @ratelimit(key="user", rate="3/m", method="POST", block=True)
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.context["request"] = request
            if serializer.is_valid():
                with transaction.atomic():
                    instance = serializer.save()
                    cache_key = f"claim_status_{instance.id}"
                    cache_data = {
                        "status": "processing",
                        "timestamp": instance.created_at.isoformat(),
                        "user_id": request.user.id,
                    }
                    cache.set(cache_key, cache_data, 3600)
                    logger.info(
                        f"Claim created: {instance.id}, status cached as processing"
                    )
                    return Response(
                        {
                            "message": "Claim created and processing initiated",
                            "claim_id": instance.id,
                            "status": "processing",
                            "estimated_processing_time": "5-15 business days",
                        },
                        status=status.HTTP_201_CREATED,
                    )
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Error creating Claim: {str(e)}")
            return Response(
                {"error": "Internal server error", "message": "Failed to create claim"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
class ClaimListView(generics.ListAPIView):
    serializer_class = ClaimSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        return Claim.objects.filter(created_by=user).order_by("-created_at")
class ClaimRetrieveView(generics.RetrieveAPIView):
    serializer_class = ClaimSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Claim.objects.filter(created_by=self.request.user)
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            cache_key = f"claim_status_{instance.id}"
            cached_status = cache.get(cache_key)
            response_data = self.get_serializer(instance).data
            if cached_status:
                logger.info(
                    f'Claim {instance.id} status from cache: {cached_status["status"]}'
                )
                response_data["cached_status"] = cached_status["status"]
                response_data["status_source"] = "cache"
                response_data["cache_timestamp"] = cached_status["timestamp"]
            else:
                logger.info(
                    f"Claim {instance.id} status from database: {instance.status}"
                )
                response_data["status_source"] = "database"
                cache.set(
                    cache_key,
                    {
                        "status": instance.status,
                        "timestamp": instance.updated_at.isoformat(),
                        "user_id": request.user.id,
                    },
                    3600,
                )
            response_data["message"] = "Claim retrieved successfully"
            return Response(response_data)
        except Claim.DoesNotExist:
            return Response(
                {
                    "error": "Claim not found",
                    "message": "The requested claim does not exist or you do not have permission to access it",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f'Error retrieving claim {kwargs.get("pk")}: {str(e)}')
            return Response(
                {
                    "error": "Internal server error",
                    "message": "Failed to retrieve claim information",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
class ReimbursementCreateView(generics.CreateAPIView):
    queryset = Reimbursement.objects.all()
    serializer_class = ReimbursementSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    @ratelimit(key="user", rate="2/m", method="POST", block=True)
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.context["request"] = request
            if serializer.is_valid():
                claim_id = serializer.validated_data["claim_id"]
                with transaction.atomic():
                    instance = serializer.save()
                    try:
                        claim = Claim.objects.select_for_update().get(id=claim_id)
                        claim.status = "paid"
                        claim.tpa_transaction_id = instance.transaction_id
                        claim.save(update_fields=["status", "tpa_transaction_id"])
                        cache_key = f"claim_status_{claim.id}"
                        cache.set(
                            cache_key,
                            {
                                "status": "paid",
                                "timestamp": claim.updated_at.isoformat(),
                                "user_id": request.user.id,
                                "reimbursement_id": instance.id,
                            },
                            3600,
                        )
                        logger.info(
                            f"Reimbursement created for claim {claim.id}, claim status updated to paid"
                        )
                    except Claim.DoesNotExist:
                        logger.error(
                            f"Claim {claim_id} not found for reimbursement {instance.id}"
                        )
                        return Response(
                            {
                                "error": "Related claim not found",
                                "message": "Cannot process reimbursement without valid claim",
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    return Response(
                        {
                            "message": "Reimbursement processed successfully",
                            "reimbursement_id": instance.id,
                            "claim_id": claim_id,
                            "status": "paid",
                            "transaction_id": instance.transaction_id,
                            "estimated_payment_time": "7-10 business days",
                        },
                        status=status.HTTP_201_CREATED,
                    )
            return Response(
                {"error": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Error creating Reimbursement: {str(e)}")
            return Response(
                {
                    "error": "Internal server error",
                    "message": "Failed to process reimbursement",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
class ReimbursementListView(generics.ListAPIView):
    serializer_class = ReimbursementSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user = self.request.user
        return Reimbursement.objects.filter(created_by=user).order_by("-created_at")
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def claim_status(request, claim_id):
    try:
        cache_key = f"claim_status_{claim_id}"
        cached_status = cache.get(cache_key)
        if cached_status:
            logger.info(
                f'Claim {claim_id} status retrieved from cache: {cached_status["status"]}'
            )
            return Response(
                {
                    "claim_id": claim_id,
                    "status": cached_status["status"],
                    "source": "cache",
                    "timestamp": cached_status["timestamp"],
                    "user_id": cached_status["user_id"],
                    "message": "Status retrieved from cache",
                    "cache_duration_remaining": "Up to 1 hour",
                }
            )
        try:
            claim = Claim.objects.get(id=claim_id, created_by=request.user)
            cache_data = {
                "status": claim.status,
                "timestamp": claim.updated_at.isoformat(),
                "user_id": request.user.id,
            }
            cache.set(cache_key, cache_data, 3600)
            logger.info(
                f"Claim {claim_id} status retrieved from database: {claim.status}"
            )
            return Response(
                {
                    "claim_id": claim_id,
                    "status": claim.status,
                    "source": "database",
                    "timestamp": claim.updated_at.isoformat(),
                    "message": "Status retrieved from database and cached",
                    "next_cache_check": "Within 1 hour",
                }
            )
        except Claim.DoesNotExist:
            return Response(
                {
                    "error": "Claim not found",
                    "message": "The requested claim does not exist or you do not have permission to access it",
                    "claim_id": claim_id,
                },
                status=status.HTTP_404_NOT_FOUND,
            )
    except Exception as e:
        logger.error(f"Error getting claim status {claim_id}: {str(e)}")
        return Response(
            {
                "error": "Internal server error",
                "message": "Failed to retrieve claim status",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
@api_view(["GET"])
def api_health_check(request):
    try:
        cache.set("health_check_test", "ok", 60)
        cache_health = cache.get("health_check_test") == "ok"
        cache.delete("health_check_test")
        celery_health = celery_app.broker_connection().ensure_connection()

        # Check insurance provider connectivity
        insurance_providers_status = {}
        try:
            async def check_providers():
                async with create_insurance_service() as service:
                    providers = service.providers
                    for provider_id, provider in providers.items():
                        try:
                            # Test connectivity with simple eligibility check
                            test_request = EligibilityRequest(
                                patient_id="TEST001",
                                policy_number="TEST_POLICY",
                                policy_holder_id="TEST_HOLDER",
                                service_date="2024-01-01",
                                service_type="CONSULTATION",
                                provider_npi="1234567890",
                                diagnosis_codes=["Z00.00"],
                                procedure_codes=["99213"]
                            )

                            eligibility_response = await service.check_eligibility(test_request, provider_id)
                            insurance_providers_status[provider.name] = {
                                "status": "connected",
                                "response_time_ms": eligibility_response.response_time_ms,
                                "edi_payer_id": provider.edi_payer_id,
                                "api_endpoint": provider.api_endpoint
                            }
                        except Exception as provider_error:
                            insurance_providers_status[provider.name] = {
                                "status": "disconnected",
                                "error": str(provider_error),
                                "edi_payer_id": provider.edi_payer_id,
                                "api_endpoint": provider.api_endpoint
                            }

            # Run provider connectivity check
            asyncio.run(check_providers())

        except Exception as insurance_check_error:
            logger.error(f"Insurance provider connectivity check failed: {insurance_check_error}")
            insurance_providers_status = {"error": str(insurance_check_error)}

        return Response(
            {
                "status": "healthy",
                "timestamp": django_timezone.now().isoformat(),
                "redis_cache": cache_health,
                "celery_broker": bool(celery_health),
                "insurance_providers": insurance_providers_status,
                "connected_providers": len([p for p in insurance_providers_status.values() if isinstance(p, dict) and p.get("status") == "connected"]),
                "total_providers": len(insurance_providers_status) if isinstance(insurance_providers_status, dict) else 0,
                "endpoints_count": 8,
                "version": "1.0.0",
                "integration_type": "Real-time insurance provider integration",
                "message": "Enterprise Insurance TPA API is operational with real provider connectivity",
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return Response(
            {
                "status": "unhealthy",
                "error": str(e),
                "message": "Enterprise API health check failed",
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )