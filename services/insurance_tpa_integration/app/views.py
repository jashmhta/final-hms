"""Insurance TPA API Views with Security and Workflow Integration"""

import json
import logging

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

from .models import Claim, PreAuth, Reimbursement  # Assuming models exist
from .serializers import ClaimSerializer, PreAuthSerializer, ReimbursementSerializer
from .tasks import submit_tpa_request  # Assuming Celery task exists

logger = logging.getLogger(__name__)


class PreAuthCreateView(generics.CreateAPIView):
    """Create pre-authorization request and trigger Celery TPA submission"""

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
                    # Trigger Celery task for TPA submission
                    submit_tpa_request.delay(instance.id)
                    # Cache the creation event
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
                        f"PreAuth created and TPA request submitted: {instance.id} by user {request.user.id}"
                    )
                    return Response(
                        {
                            "message": "Pre-authorization request created and submitted to TPA",
                            "preauth_id": instance.id,
                            "status": "submitted",
                            "tpa_submission_id": instance.id,  # Celery task ID would be better
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
                    "message": "Failed to create pre-authorization request",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PreAuthListView(generics.ListAPIView):
    """List user's pre-authorization requests"""

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
    """Retrieve, update, or delete specific pre-authorization"""

    serializer_class = PreAuthSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PreAuth.objects.filter(created_by=self.request.user)

    def perform_update(self, serializer):
        """Update pre-auth status and clear cache"""
        instance = serializer.save()
        cache_key = f"preauth_{instance.id}"
        cache.delete(cache_key)
        logger.info(
            f"PreAuth {instance.id} updated to status: {instance.status} by user {self.request.user.id}"
        )

    def perform_destroy(self, instance):
        """Delete pre-auth and clear cache"""
        cache_key = f"preauth_{instance.id}"
        cache.delete(cache_key)
        instance.delete()
        logger.info(f"PreAuth {instance.id} deleted by user {self.request.user.id}")


class ClaimCreateView(generics.CreateAPIView):
    """Create claim and set initial processing status in cache"""

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
                    # Set cached status
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
    """List user's claims"""

    serializer_class = ClaimSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Claim.objects.filter(created_by=user).order_by("-created_at")


class ClaimRetrieveView(generics.RetrieveAPIView):
    """Retrieve specific claim with cached status check"""

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
                # Cache the status for future requests
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
    """Create reimbursement and update related claim status"""

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
                    # Update related claim status
                    try:
                        claim = Claim.objects.select_for_update().get(id=claim_id)
                        claim.status = "paid"
                        claim.tpa_transaction_id = instance.transaction_id
                        claim.save(update_fields=["status", "tpa_transaction_id"])
                        # Update cache
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
    """List user's reimbursements"""

    serializer_class = ReimbursementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Reimbursement.objects.filter(created_by=user).order_by("-created_at")


# Utility view for claim status polling
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def claim_status(request, claim_id):
    """Get claim status from cache or database with detailed response"""
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
            # Cache the status
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


# Health check endpoint
@api_view(["GET"])
def api_health_check(request):
    """API health check endpoint"""
    try:
        # Test Redis connection
        cache.set("health_check_test", "ok", 60)
        cache_health = cache.get("health_check_test") == "ok"
        cache.delete("health_check_test")

        # Test Celery connection
        celery_health = celery_app.broker_connection().ensure_connection()

        return Response(
            {
                "status": "healthy",
                "timestamp": timezone.now().isoformat(),
                "redis_cache": cache_health,
                "celery_broker": bool(celery_health),
                "endpoints_count": 8,
                "version": "1.0.0",
                "message": "Insurance TPA API is operational",
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return Response(
            {
                "status": "unhealthy",
                "error": str(e),
                "message": "API health check failed",
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
