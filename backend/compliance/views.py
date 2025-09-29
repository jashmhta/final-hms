"""
views module
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from rest_framework import generics, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Count, Q
from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from .authentication import MultiFactorAuthentication, RoleBasedAccessControl
from .models import (
    AccessPurpose,
    ConsentAuditLog,
    ConsentManagement,
    ConsentStatus,
    ConsentType,
    DataAccessType,
    DataSubjectRequest,
    DataSubjectRequestAudit,
)
from .serializers import (
    ConsentAuditLogSerializer,
    ConsentManagementSerializer,
    DataSubjectRequestAuditSerializer,
    DataSubjectRequestSerializer,
)
from .services import (
    AuditTrailService,
    DataAccessService,
    DataErasureService,
    DataRetentionService,
)

User = get_user_model()


class ConsentManagementViewSet(viewsets.ModelViewSet):
    """
    GDPR Article 7 compliant consent management API
    """

    serializer_class = ConsentManagementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter consents based on user permissions
        """
        user = self.request.user
        queryset = ConsentManagement.objects.all()

        # Patients can only see their own consents
        if hasattr(user, "patient_profile"):
            queryset = queryset.filter(patient=user.patient_profile)

        # Clinical staff can see consents for their patients
        elif user.has_perm("patients.view_patient"):
            # Implementation should filter by user's assigned patients
            pass

        # Administrators can see all consents
        elif user.is_staff:
            pass
        else:
            queryset = queryset.none()

        return queryset

    def perform_create(self, serializer):
        """
        Create consent with proper audit trail
        """
        serializer.save(created_by=self.request.user)

        # Create audit log
        ConsentAuditLog.objects.create(
            patient=serializer.instance.patient,
            consent=serializer.instance,
            action="CREATED",
            action_by=self.request.user,
            details="New consent created",
            ip_address=self._get_client_ip(),
            user_agent=self.request.META.get("HTTP_USER_AGENT", ""),
        )

    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        """
        Revoke consent with proper audit trail
        """
        consent = self.get_object()

        # Check if user has permission to revoke this consent
        if not self._can_revoke_consent(consent, request.user):
            raise PermissionDenied("You do not have permission to revoke this consent")

        reason = request.data.get("reason", "")
        consent.revoke(reason, request.user)

        return Response(
            {
                "message": "Consent revoked successfully",
                "consent_id": consent.id,
                "revoked_at": consent.revoked_date,
            }
        )

    @action(detail=True, methods=["post"])
    def renew(self, request, pk=None):
        """
        Renew consent with updated expiry date
        """
        consent = self.get_object()

        # Check if user has permission to renew this consent
        if not self._can_renew_consent(consent, request.user):
            raise PermissionDenied("You do not have permission to renew this consent")

        new_expiry_date = request.data.get("expiry_date")
        if not new_expiry_date:
            raise ValidationError("expiry_date is required")

        try:
            expiry_date = datetime.fromisoformat(new_expiry_date)
            if expiry_date <= timezone.now():
                raise ValidationError("Expiry date must be in the future")
        except ValueError:
            raise ValidationError("Invalid expiry date format")

        renewed_consent = consent.renew(expiry_date, request.user)

        serializer = self.get_serializer(renewed_consent)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def active_consents(self, request):
        """
        Get all active consents for a patient
        """
        patient_id = request.query_params.get("patient_id")
        if not patient_id:
            raise ValidationError("patient_id is required")

        # Check if user has permission to view patient consents
        if not self._can_view_patient_consents(patient_id, request.user):
            raise PermissionDenied("You do not have permission to view these consents")

        active_consents = ConsentManagement.get_active_consents(patient_id)
        serializer = self.get_serializer(active_consents, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def consent_types(self, request):
        """
        Get available consent types
        """
        consent_types = [
            {
                "value": consent_type[0],
                "label": consent_type[1],
                "description": self._get_consent_type_description(consent_type[0]),
            }
            for consent_type in ConsentType.choices
        ]
        return Response(consent_types)

    def _can_revoke_consent(self, consent, user) -> bool:
        """
        Check if user can revoke consent
        """
        # Patients can revoke their own consents
        if hasattr(user, "patient_profile") and consent.patient == user.patient_profile:
            return True

        # Legal guardians can revoke patient consents
        if self._is_legal_guardian(user, consent.patient):
            return True

        # Clinical staff can revoke consents for their patients
        if user.has_perm("patients.view_patient"):
            # Implementation should check if patient is assigned to user
            return True

        return False

    def _can_renew_consent(self, consent, user) -> bool:
        """
        Check if user can renew consent
        """
        # Only clinical staff can renew consents
        return user.has_perm("patients.view_patient")

    def _can_view_patient_consents(self, patient_id, user) -> bool:
        """
        Check if user can view patient consents
        """
        # Patients can view their own consents
        if hasattr(user, "patient_profile") and str(user.patient_profile.id) == str(
            patient_id
        ):
            return True

        # Clinical staff can view consents for their patients
        if user.has_perm("patients.view_patient"):
            # Implementation should check if patient is assigned to user
            return True

        # Administrators can view all consents
        if user.is_staff:
            return True

        return False

    def _is_legal_guardian(self, user, patient) -> bool:
        """
        Check if user is legal guardian of patient
        """
        # Implementation should check guardian relationship
        return False

    def _get_consent_type_description(self, consent_type) -> str:
        """
        Get description for consent type
        """
        descriptions = {
            ConsentType.GENERAL_TREATMENT: "Consent for general medical treatment and care",
            ConsentType.SPECIFIC_PROCEDURE: "Consent for specific medical procedures or treatments",
            ConsentType.RESEARCH_PARTICIPATION: "Consent to participate in medical research",
            ConsentType.MARKETING_COMMUNICATIONS: "Consent to receive marketing communications",
            ConsentType.DATA_SHARING: "Consent to share data with third parties",
            ConsentType.EMERGENCY_CONTACT: "Consent for emergency contact disclosure",
            ConsentType.INSURANCE_BILLING: "Consent for insurance billing and payment",
            ConsentType.TELEMEDICINE: "Consent for telemedicine services",
            ConsentType.MENTAL_HEALTH: "Consent for mental health treatment",
            ConsentType.SUBSTANCE_ABUSE: "Consent for substance abuse treatment",
            ConsentType.HIV_AIDS: "Consent for HIV/AIDS related information",
            ConsentType.GENETIC_INFORMATION: "Consent for genetic testing and information",
        }
        return descriptions.get(consent_type, "No description available")

    def _get_client_ip(self) -> str:
        """
        Get client IP address
        """
        x_forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = self.request.META.get("REMOTE_ADDR")
        return ip or "127.0.0.1"


class DataSubjectRequestViewSet(viewsets.ModelViewSet):
    """
    GDPR Articles 15, 16, 17, 18, 20, 21 compliant data subject requests API
    """

    serializer_class = DataSubjectRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter data subject requests based on user permissions
        """
        user = self.request.user
        queryset = DataSubjectRequest.objects.all()

        # Patients can only see their own requests
        if hasattr(user, "patient_profile"):
            queryset = queryset.filter(patient=user.patient_profile)

        # Compliance officers can see all requests
        elif user.has_perm("compliance.view_datasubjectrequest"):
            pass
        else:
            queryset = queryset.none()

        return queryset

    def perform_create(self, serializer):
        """
        Create data subject request with proper validation
        """
        patient_id = serializer.validated_data.get("patient_id")
        if not patient_id and hasattr(self.request.user, "patient_profile"):
            patient_id = self.request.user.patient_profile.id

        # Validate user can make request for this patient
        if not self._can_make_request_for_patient(patient_id, self.request.user):
            raise PermissionDenied(
                "You do not have permission to make requests for this patient"
            )

        serializer.save(
            patient_id=patient_id, received_date=timezone.now(), status="PENDING"
        )

        # Create audit log
        DataSubjectRequestAudit.objects.create(
            request=serializer.instance,
            action="CREATED",
            action_by=self.request.user,
            details="New data subject request created",
        )

    @action(detail=True, methods=["post"])
    def process_access_request(self, request, pk=None):
        """
        Process GDPR Article 15 access request
        """
        data_request = self.get_object()

        if data_request.request_type != "ACCESS":
            raise ValidationError("This is not an access request")

        if not request.user.has_perm("compliance.process_datasubjectrequest"):
            raise PermissionDenied("You do not have permission to process this request")

        try:
            response_data = data_request.process_access_request()
            return Response(
                {
                    "message": "Access request processed successfully",
                    "request_id": data_request.id,
                    "response_data": response_data,
                }
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to process access request: {str(e)}"}, status=500
            )

    @action(detail=True, methods=["post"])
    def process_erasure_request(self, request, pk=None):
        """
        Process GDPR Article 17 erasure request
        """
        data_request = self.get_object()

        if data_request.request_type != "ERASURE":
            raise ValidationError("This is not an erasure request")

        if not request.user.has_perm("compliance.process_datasubjectrequest"):
            raise PermissionDenied("You do not have permission to process this request")

        try:
            success = data_request.process_erasure_request()
            return Response(
                {
                    "message": "Erasure request processed successfully",
                    "request_id": data_request.id,
                    "success": success,
                }
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to process erasure request: {str(e)}"}, status=500
            )

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        """
        Assign data subject request to a staff member
        """
        data_request = self.get_object()

        if not request.user.has_perm("compliance.assign_datasubjectrequest"):
            raise PermissionDenied("You do not have permission to assign requests")

        assigned_to_id = request.data.get("assigned_to_id")
        if not assigned_to_id:
            raise ValidationError("assigned_to_id is required")

        try:
            assigned_to = User.objects.get(id=assigned_to_id)
        except User.DoesNotExist:
            raise ValidationError("Assigned user not found")

        data_request.assigned_to = assigned_to
        data_request.status = "IN_PROGRESS"
        data_request.save()

        # Create audit log
        DataSubjectRequestAudit.objects.create(
            request=data_request,
            action="ASSIGNED",
            action_by=request.user,
            details=f"Request assigned to {assigned_to.get_full_name()}",
        )

        return Response(
            {
                "message": "Request assigned successfully",
                "request_id": data_request.id,
                "assigned_to": assigned_to.get_full_name(),
            }
        )

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """
        Mark data subject request as completed
        """
        data_request = self.get_object()

        if data_request.assigned_to != request.user:
            raise PermissionDenied("You can only complete requests assigned to you")

        response_message = request.data.get("response_message", "")
        data_request.status = "COMPLETED"
        data_request.completed_date = timezone.now()
        data_request.completed_by = request.user
        data_request.response_message = response_message
        data_request.save()

        # Create audit log
        DataSubjectRequestAudit.objects.create(
            request=data_request,
            action="COMPLETED",
            action_by=request.user,
            details=f"Request completed: {response_message}",
        )

        return Response(
            {
                "message": "Request completed successfully",
                "request_id": data_request.id,
                "completed_at": data_request.completed_date,
            }
        )

    def _can_make_request_for_patient(self, patient_id, user) -> bool:
        """
        Check if user can make request for patient
        """
        # Patients can make requests for themselves
        if hasattr(user, "patient_profile") and str(user.patient_profile.id) == str(
            patient_id
        ):
            return True

        # Legal guardians can make requests for their wards
        if self._is_legal_guardian(user, patient_id):
            return True

        return False

    def _is_legal_guardian(self, user, patient_id) -> bool:
        """
        Check if user is legal guardian of patient
        """
        # Implementation should check guardian relationship
        return False


class MultiFactorAuthenticationView(View):
    """
    Multi-Factor Authentication setup and verification
    """

    mfa_auth = MultiFactorAuthentication()

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        """
        Handle MFA-related requests
        """
        action = request.POST.get("action")

        if action == "setup_mfa":
            return self._setup_mfa(request)
        elif action == "verify_totp":
            return self._verify_totp(request)
        elif action == "verify_backup_code":
            return self._verify_backup_code(request)
        elif action == "generate_backup_codes":
            return self._generate_backup_cocryptography.fernet.Fernet(request)
        else:
            return JsonResponse({"error": "Invalid action"}, status=400)

    def _setup_mfa(self, request):
        """
        Setup MFA for user
        """
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)

        user = request.user

        # Generate TOTP secret
        secret = self.mfa_auth.generate_totp_secret(user)

        # Generate QR code provisioning URI
        provisioning_uri = self.mfa_auth.generate_totp_qr_code(user, secret)

        # Store secret temporarily (in production, store securely)
        cache.set(f"mfa_setup_secret_{user.id}", secret, 300)  # 5 minutes

        return JsonResponse(
            {
                "secret": secret,
                "provisioning_uri": provisioning_uri,
                "message": "MFA setup initiated",
            }
        )

    def _verify_totp(self, request):
        """
        Verify TOTP token
        """
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)

        user = request.user
        token = request.POST.get("token")

        if not token:
            return JsonResponse({"error": "Token is required"}, status=400)

        # Check if user is in MFA setup flow
        setup_secret = cache.get(f"mfa_setup_secret_{user.id}")
        if setup_secret:
            # Setup flow - verify with temporary secret
            totp = pyotp.TOTP(setup_secret)
            if totp.verify(token, valid_window=1):
                user.mfa_secret = setup_secret
                user.mfa_enabled = True
                user.save()

                # Clear temporary secret
                cache.delete(f"mfa_setup_secret_{user.id}")

                return JsonResponse(
                    {"message": "MFA setup completed successfully", "mfa_enabled": True}
                )

        # Normal verification flow
        if self.mfa_auth.verify_totp_token(user, token):
            return JsonResponse(
                {"message": "MFA verification successful", "verified": True}
            )

        return JsonResponse({"error": "Invalid token"}, status=400)

    def _verify_backup_code(self, request):
        """
        Verify backup code
        """
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)

        user = request.user
        code = request.POST.get("code")

        if not code:
            return JsonResponse({"error": "Backup code is required"}, status=400)

        if self.mfa_auth.verify_backup_code(user, code):
            return JsonResponse(
                {"message": "Backup code verified successfully", "verified": True}
            )

        return JsonResponse({"error": "Invalid backup code"}, status=400)

    def _generate_backup_codes(self, request):
        """
        Generate new backup codes
        """
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)

        user = request.user
        backup_codes = self.mfa_auth.generate_backup_codes(user, 10)

        return JsonResponse(
            {
                "message": "Backup codes generated successfully",
                "backup_codes": backup_codes,
                "count": len(backup_codes),
            }
        )


class ComplianceDashboardView(View):
    """
    Compliance monitoring dashboard
    """

    def get(self, request):
        """
        Get compliance dashboard data
        """
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)

        if not request.user.has_perm("compliance.view_compliance_dashboard"):
            return JsonResponse({"error": "Insufficient permissions"}, status=403)

        # Get compliance metrics
        dashboard_data = self._get_compliance_metrics()

        return JsonResponse(dashboard_data)

    def _get_compliance_metrics(self) -> Dict:
        """
        Get comprehensive compliance metrics
        """
        # Consent management metrics
        total_consents = ConsentManagement.objects.count()
        active_consents = ConsentManagement.objects.filter(
            status=ConsentStatus.ACTIVE
        ).count()
        expired_consents = ConsentManagement.objects.filter(
            status=ConsentStatus.EXPIRED
        ).count()
        revoked_consents = ConsentManagement.objects.filter(
            status=ConsentStatus.REVOKED
        ).count()

        # Data subject request metrics
        total_requests = DataSubjectRequest.objects.count()
        pending_requests = DataSubjectRequest.objects.filter(status="PENDING").count()
        in_progress_requests = DataSubjectRequest.objects.filter(
            status="IN_PROGRESS"
        ).count()
        completed_requests = DataSubjectRequest.objects.filter(
            status="COMPLETED"
        ).count()

        # Request type breakdown
        request_types = (
            DataSubjectRequest.objects.values("request_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # Recent activity
        recent_activity = ConsentAuditLog.objects.order_by("-action_date")[:10]

        return {
            "consent_management": {
                "total": total_consents,
                "active": active_consents,
                "expired": expired_consents,
                "revoked": revoked_consents,
                "compliance_rate": round(
                    (
                        (active_consents / total_consents * 100)
                        if total_consents > 0
                        else 0
                    ),
                    2,
                ),
            },
            "data_subject_requests": {
                "total": total_requests,
                "pending": pending_requests,
                "in_progress": in_progress_requests,
                "completed": completed_requests,
                "completion_rate": round(
                    (
                        (completed_requests / total_requests * 100)
                        if total_requests > 0
                        else 0
                    ),
                    2,
                ),
            },
            "request_types": list(request_types),
            "recent_activity": [
                {
                    "id": activity.id,
                    "action": activity.action,
                    "action_by": (
                        activity.action_by.get_full_name()
                        if activity.action_by
                        else "System"
                    ),
                    "action_date": activity.action_date.isoformat(),
                    "patient_name": str(activity.patient),
                }
                for activity in recent_activity
            ],
            "generated_at": timezone.now().isoformat(),
        }


class DataRetentionView(View):
    """
    Data retention policy management
    """

    def post(self, request):
        """
        Apply data retention policies
        """
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)

        if not request.user.has_perm("compliance.manage_data_retention"):
            return JsonResponse({"error": "Insufficient permissions"}, status=403)

        dry_run = request.POST.get("dry_run", "false").lower() == "true"

        retention_service = DataRetentionService()
        results = retention_service.apply_retention_policies(dry_run=dry_run)

        return JsonResponse(
            {
                "message": "Data retention policies applied successfully",
                "results": results,
                "dry_run": dry_run,
            }
        )


class ComplianceReportView(View):
    """
    Generate compliance reports
    """

    def get(self, request):
        """
        Generate compliance report
        """
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)

        if not request.user.has_perm("compliance.generate_compliance_report"):
            return JsonResponse({"error": "Insufficient permissions"}, status=403)

        # Get report parameters
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        report_type = request.GET.get("report_type", "comprehensive")

        try:
            if start_date:
                start_date = datetime.fromisoformat(start_date)
            else:
                start_date = timezone.now() - timedelta(days=30)

            if end_date:
                end_date = datetime.fromisoformat(end_date)
            else:
                end_date = timezone.now()
        except ValueError:
            return JsonResponse({"error": "Invalid date format"}, status=400)

        # Generate report
        report_data = self._generate_report(start_date, end_date, report_type)

        return JsonResponse(report_data)

    def _generate_report(self, start_date, end_date, report_type) -> Dict:
        """
        Generate compliance report based on type
        """
        if report_type == "consent":
            return self._generate_consent_report(start_date, end_date)
        elif report_type == "data_requests":
            return self._generate_data_requests_report(start_date, end_date)
        elif report_type == "comprehensive":
            return self._generate_comprehensive_report(start_date, end_date)
        else:
            raise ValueError(f"Unknown report type: {report_type}")

    def _generate_consent_report(self, start_date, end_date) -> Dict:
        """
        Generate consent compliance report
        """
        consents = ConsentManagement.objects.filter(
            created_at__gte=start_date, created_at__lte=end_date
        )

        return {
            "report_type": "consent_compliance",
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "summary": {
                "total_consents": consents.count(),
                "active_consents": consents.filter(status=ConsentStatus.ACTIVE).count(),
                "expired_consents": consents.filter(
                    status=ConsentStatus.EXPIRED
                ).count(),
                "revoked_consents": consents.filter(
                    status=ConsentStatus.REVOKED
                ).count(),
            },
            "consent_types": list(
                consents.values("consent_type")
                .annotate(count=Count("id"))
                .order_by("-count")
            ),
            "generated_at": timezone.now().isoformat(),
        }

    def _generate_data_requests_report(self, start_date, end_date) -> Dict:
        """
        Generate data subject requests report
        """
        requests = DataSubjectRequest.objects.filter(
            received_date__gte=start_date, received_date__lte=end_date
        )

        return {
            "report_type": "data_subject_requests",
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "summary": {
                "total_requests": requests.count(),
                "pending_requests": requests.filter(status="PENDING").count(),
                "in_progress_requests": requests.filter(status="IN_PROGRESS").count(),
                "completed_requests": requests.filter(status="COMPLETED").count(),
                "rejected_requests": requests.filter(status="REJECTED").count(),
            },
            "request_types": list(
                requests.values("request_type")
                .annotate(count=Count("id"))
                .order_by("-count")
            ),
            "processing_times": self._calculate_processing_times(requests),
            "generated_at": timezone.now().isoformat(),
        }

    def _generate_comprehensive_report(self, start_date, end_date) -> Dict:
        """
        Generate comprehensive compliance report
        """
        consent_report = self._generate_consent_report(start_date, end_date)
        data_requests_report = self._generate_data_requests_report(start_date, end_date)

        return {
            "report_type": "comprehensive_compliance",
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "consent_management": consent_report,
            "data_subject_requests": data_requests_report,
            "compliance_score": self._calculate_compliance_score(
                consent_report, data_requests_report
            ),
            "recommendations": self._generate_recommendations(
                consent_report, data_requests_report
            ),
            "generated_at": timezone.now().isoformat(),
        }

    def _calculate_processing_times(self, requests) -> Dict:
        """
        Calculate request processing time metrics
        """
        completed_requests = requests.filter(status="COMPLETED")

        if not completed_requests.exists():
            return {"average": 0, "median": 0, "max": 0}

        processing_times = []
        for request in completed_requests:
            if request.completed_date and request.received_date:
                processing_time = (
                    request.completed_date - request.received_date
                ).total_seconds()
                processing_times.append(processing_time)

        if not processing_times:
            return {"average": 0, "median": 0, "max": 0}

        processing_times.sort()
        return {
            "average": sum(processing_times) / len(processing_times),
            "median": processing_times[len(processing_times) // 2],
            "max": max(processing_times),
        }

    def _calculate_compliance_score(
        self, consent_report, data_requests_report
    ) -> float:
        """
        Calculate overall compliance score
        """
        # Consent compliance score (60% weight)
        consent_score = 0
        if consent_report["summary"]["total_consents"] > 0:
            consent_score = (
                consent_report["summary"]["active_consents"]
                / consent_report["summary"]["total_consents"]
            ) * 100

        # Data requests compliance score (40% weight)
        requests_score = 0
        if data_requests_report["summary"]["total_requests"] > 0:
            requests_score = (
                data_requests_report["summary"]["completed_requests"]
                / data_requests_report["summary"]["total_requests"]
            ) * 100

        # Weighted average
        return round((consent_score * 0.6) + (requests_score * 0.4), 2)

    def _generate_recommendations(
        self, consent_report, data_requests_report
    ) -> List[str]:
        """
        Generate compliance recommendations
        """
        recommendations = []

        # Consent recommendations
        if consent_report["summary"]["expired_consents"] > 0:
            recommendations.append(
                "Consider implementing automatic consent renewal reminders"
            )

        if (
            consent_report["summary"]["revoked_consents"]
            > consent_report["summary"]["total_consents"] * 0.1
        ):
            recommendations.append(
                "High consent revocation rate detected. Review consent process"
            )

        # Data requests recommendations
        if data_requests_report["summary"]["pending_requests"] > 0:
            recommendations.append(
                "Address pending data subject requests to maintain GDPR compliance"
            )

        if (
            data_requests_report["processing_times"]["average"] > 259200
        ):  # 3 days in seconds
            recommendations.append("Improve data subject request processing time")

        return recommendations
