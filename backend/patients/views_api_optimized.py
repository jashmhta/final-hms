"""
Optimized Patient API Views with High-Performance Features
Includes caching, efficient pagination, bulk operations, and streaming
"""

import logging
from datetime import datetime, timedelta

from django_filters import rest_framework as drf_filters
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.core.cache import cache
from django.db.models import Count, Prefetch, Q
from django.utils import timezone

from ..core.optimization.api_optimizer import (
    BulkOperationMixin,
    OptimizedModelViewSet,
    cache_api_response,
    calculate_query_efficiency,
)
from ..core.optimization.cache_optimizer import cache_result
from ..core.optimization.query_optimizer import QueryOptimizer
from ..models import EmergencyContact, InsuranceInformation, Patient
from .serializers_optimized import (
    BulkPatientSerializer,
    PatientCreateSerializer,
    PatientDetailSerializer,
    PatientListSerializer,
    PatientSearchSerializer,
    PatientUpdateSerializer,
)

logger = logging.getLogger(__name__)


class PatientFilter(drf_filters.FilterSet):
    """Advanced filtering for patients"""

    min_age = drf_filters.NumberFilter(method="filter_by_age")
    max_age = drf_filters.NumberFilter(method="filter_by_age")
    admission_date_after = drf_filters.DateFilter(
        field_name="admission_date", lookup_expr="gte"
    )
    admission_date_before = drf_filters.DateFilter(
        field_name="admission_date", lookup_expr="lte"
    )
    discharge_date_after = drf_filters.DateFilter(
        field_name="discharge_date", lookup_expr="gte"
    )
    discharge_date_before = drf_filters.DateFilter(
        field_name="discharge_date", lookup_expr="lte"
    )
    last_visit_after = drf_filters.DateFilter(
        field_name="last_visit_date", lookup_expr="gte"
    )
    last_visit_before = drf_filters.DateFilter(
        field_name="last_visit_date", lookup_expr="lte"
    )
    has_insurance = drf_filters.BooleanFilter(method="filter_has_insurance")
    vip_status = drf_filters.BooleanFilter(field_name="vip_status")
    confidential = drf_filters.BooleanFilter(field_name="confidential")
    patient_portal_enrolled = drf_filters.BooleanFilter(
        field_name="patient_portal_enrolled"
    )

    class Meta:
        model = Patient
        fields = {
            "hospital_id": ["exact"],
            "status": ["exact"],
            "gender": ["exact"],
            "marital_status": ["exact"],
            "race": ["exact"],
            "ethnicity": ["exact"],
            "blood_type": ["exact"],
            "city": ["exact", "icontains"],
            "state": ["exact"],
            "zip_code": ["exact"],
            "country": ["exact"],
            "primary_care_physician_id": ["exact"],
            "referring_physician_id": ["exact"],
        }

    def filter_by_age(self, queryset, name, value):
        """Filter patients by age range"""
        today = timezone.now().date()
        if name == "min_age":
            max_birth_date = today - timedelta(days=value * 365.25)
            return queryset.filter(date_of_birth__lte=max_birth_date)
        elif name == "max_age":
            min_birth_date = today - timedelta(days=value * 365.25)
            return queryset.filter(date_of_birth__gte=min_birth_date)
        return queryset

    def filter_has_insurance(self, queryset, name, value):
        """Filter patients by insurance status"""
        if value:
            return queryset.filter(insurance_plans__isnull=False).distinct()
        else:
            return queryset.filter(insurance_plans__isnull=True)


class OptimizedPatientViewSet(OptimizedModelViewSet, BulkOperationMixin):
    """High-performance patient management API"""

    serializer_class = PatientDetailSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = PatientFilter
    search_fields = [
        "first_name",
        "last_name",
        "middle_name",
        "email",
        "phone_primary",
        "phone_secondary",
        "medical_record_number",
        "uuid",
    ]
    ordering_fields = [
        "last_name",
        "first_name",
        "date_of_birth",
        "created_at",
        "updated_at",
        "last_visit_date",
        "admission_date",
        "discharge_date",
    ]
    ordering = ["-created_at"]

    # Optimization settings
    select_related_fields = [
        "hospital",
        "primary_care_physician",
        "referring_physician",
        "created_by",
        "last_updated_by",
    ]
    prefetch_related_fields = [
        "emergency_contacts",
        "insurance_plans",
        "allergies",
        "medications",
        "lab_results",
        "appointments",
    ]

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "list":
            return PatientListSerializer
        elif self.action == "create":
            return PatientCreateSerializer
        elif self.action == "update" or self.action == "partial_update":
            return PatientUpdateSerializer
        elif self.action == "search":
            return PatientSearchSerializer
        elif self.action in ["bulk_create", "bulk_update"]:
            return BulkPatientSerializer
        return PatientDetailSerializer

    def get_queryset(self):
        """Get optimized queryset with caching"""
        queryset = super().get_queryset()

        # Apply hospital filter if not admin
        user = self.request.user
        if not user.is_staff and hasattr(user, "hospital_id"):
            queryset = queryset.filter(hospital_id=user.hospital_id)

        # Optimize for list view
        if self.action == "list":
            # Use lighter queryset for list
            queryset = queryset.select_related("hospital", "primary_care_physician")

        return queryset

    @cache_api_response(timeout=60)  # Cache for 1 minute
    def list(self, request, *args, **kwargs):
        """List patients with performance optimizations"""
        # Check if statistics are requested
        if request.GET.get("stats") == "true":
            return self._get_patient_statistics()

        # Check if export is requested
        if request.GET.get("export") == "true":
            return self._export_patients()

        # Standard list with optimizations
        response = super().list(request, *args, **kwargs)

        # Add performance metrics
        if hasattr(request, "query_time"):
            response.data["performance"]["query_efficiency"] = (
                calculate_query_efficiency(self.get_queryset())
            )

        return response

    def retrieve(self, request, *args, **kwargs):
        """Get patient details with optimized related data"""
        # Use cached detailed query
        patient = self.get_object()

        # Cache key for patient details
        cache_key = f"patient_detail_{patient.id}_{patient.updated_at.timestamp()}"
        cached_data = cache.get(cache_key)

        if cached_data:
            request.cache_hit = True
            return Response(cached_data)

        # Get optimized related data
        emergency_contacts = patient.emergency_contacts.all()
        insurance_plans = patient.insurance_plans.filter(is_active=True)

        # Store for serializer
        patient._prefetched_emergency_contacts = emergency_contacts
        patient._prefetched_insurance_plans = insurance_plans

        serializer = self.get_serializer(patient)
        response_data = serializer.data

        # Cache response
        cache.set(cache_key, response_data, timeout=300)  # 5 minutes

        return Response(response_data)

    @action(detail=False, methods=["get"])
    @cache_api_response(timeout=300)  # Cache for 5 minutes
    def search(self, request):
        """Optimized patient search with full-text capabilities"""
        query = request.GET.get("q", "").strip()
        if not query or len(query) < 2:
            return Response(
                {"error": "Search query must be at least 2 characters"}, status=400
            )

        # Use optimized search
        queryset = self.filter_queryset(self.get_queryset())

        # Full-text search on name fields
        name_conditions = Q()
        for term in query.split():
            name_conditions |= Q(first_name__icontains=term)
            name_conditions |= Q(last_name__icontains=term)
            name_conditions |= Q(middle_name__icontains=term)

        # Search other fields
        other_conditions = Q(
            Q(email__icontains=query)
            | Q(phone_primary__icontains=query)
            | Q(phone_secondary__icontains=query)
            | Q(medical_record_number__icontains=query)
            | Q(uuid__icontains=query)
        )

        queryset = queryset.filter(name_conditions | other_conditions)

        # Use specialized search serializer
        page = self.paginate_queryset(queryset)
        serializer = PatientSearchSerializer(page, many=True)

        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"])
    @cache_result(timeout=600)  # Cache for 10 minutes
    def statistics(self, request):
        """Get patient statistics with caching"""
        hospital_id = request.user.hospital_id if not request.user.is_staff else None

        # Generate cache key
        cache_key = f'patient_stats_{hospital_id or "all"}'

        # Check cache
        cached_stats = cache.get(cache_key)
        if cached_stats:
            return Response(cached_stats)

        # Calculate statistics
        queryset = self.get_queryset()
        if hospital_id:
            queryset = queryset.filter(hospital_id=hospital_id)

        stats = {
            "total_patients": queryset.count(),
            "active_patients": queryset.filter(status="ACTIVE").count(),
            "inactive_patients": queryset.filter(status="INACTIVE").count(),
            "vip_count": queryset.filter(vip_status=True).count(),
            "portal_enrolled": queryset.filter(patient_portal_enrolled=True).count(),
            "confidential_count": queryset.filter(confidential=True).count(),
            "new_patients_last_30d": queryset.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count(),
            "age_distribution": self._get_age_distribution(queryset),
            "gender_distribution": self._get_gender_distribution(queryset),
            "status_distribution": self._get_status_distribution(queryset),
            "calculated_at": timezone.now().isoformat(),
        }

        # Cache results
        cache.set(cache_key, stats, timeout=600)

        return Response(stats)

    def _get_age_distribution(self, queryset):
        """Calculate age distribution"""
        age_ranges = [
            ("0-17", 0, 17),
            ("18-34", 18, 34),
            ("35-49", 35, 49),
            ("50-64", 50, 64),
            ("65+", 65, 150),
        ]

        distribution = {}
        today = timezone.now().date()

        for label, min_age, max_age in age_ranges:
            if max_age == 150:
                count = queryset.filter(
                    date_of_birth__lte=today - timedelta(days=min_age * 365.25)
                ).count()
            else:
                min_date = today - timedelta(days=max_age * 365.25)
                max_date = today - timedelta(days=min_age * 365.25)
                count = queryset.filter(
                    date_of_birth__gte=min_date, date_of_birth__lte=max_date
                ).count()

            distribution[label] = count

        return distribution

    def _get_gender_distribution(self, queryset):
        """Calculate gender distribution"""
        return dict(
            queryset.values("gender")
            .annotate(count=Count("gender"))
            .values_list("gender", "count")
        )

    def _get_status_distribution(self, queryset):
        """Calculate status distribution"""
        return dict(
            queryset.values("status")
            .annotate(count=Count("status"))
            .values_list("status", "count")
        )

    @action(detail=False, methods=["post"])
    @cache_api_response(timeout=30)  # Cache for 30 seconds
    def bulk_validate(self, request):
        """Validate multiple patients without saving"""
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        return Response({"valid": True, "count": len(serializer.validated_data)})

    @action(detail=True, methods=["get"])
    def related_patients(self, request, pk=None):
        """Find related patients (same household/family)"""
        patient = self.get_object()

        # Find patients with same address or phone
        related = (
            Patient.objects.filter(
                Q(address_line1=patient.address_line1)
                | Q(phone_primary=patient.phone_primary)
                | Q(phone_secondary=patient.phone_primary)
                | Q(email=patient.email)
            )
            .exclude(id=patient.id)
            .select_related("hospital")
        )

        page = self.paginate_queryset(related)
        serializer = PatientListSerializer(page, many=True)

        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"])
    def duplicates(self, request):
        """Find potential duplicate patients"""
        # Group by similar fields
        duplicates = []

        # Check by name and birth date
        name_dob_groups = (
            Patient.objects.values("first_name", "last_name", "date_of_birth")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )

        for group in name_dob_groups:
            patients = Patient.objects.filter(
                first_name=group["first_name"],
                last_name=group["last_name"],
                date_of_birth=group["date_of_birth"],
            ).select_related("hospital")

            duplicates.append(
                {
                    "criteria": f"Name: {group['first_name']} {group['last_name']}, DOB: {group['date_of_birth']}",
                    "count": group["count"],
                    "patients": PatientListSerializer(patients, many=True).data,
                }
            )

        return Response({"duplicates": duplicates})

    def _export_patients(self):
        """Export patient data efficiently"""
        queryset = self.get_queryset()

        # Use streaming for large exports
        from ..core.optimization.api_optimizer import stream_queryset
        from .serializers_optimized import PatientExportSerializer

        generator = stream_queryset(queryset, PatientExportSerializer)

        response = StreamingJSONResponse(generator)
        response["Content-Disposition"] = 'attachment; filename="patients_export.json"'
        return response

    def _get_patient_statistics(self):
        """Get quick patient statistics for list view"""
        hospital_id = (
            self.request.user.hospital_id if not self.request.user.is_staff else None
        )

        # Use cached statistics
        cache_key = f'quick_patient_stats_{hospital_id or "all"}'
        stats = cache.get(cache_key)

        if not stats:
            queryset = self.get_queryset()
            if hospital_id:
                queryset = queryset.filter(hospital_id=hospital_id)

            stats = {
                "total": queryset.count(),
                "active": queryset.filter(status="ACTIVE").count(),
                "new_today": queryset.filter(
                    created_at__date=timezone.now().date()
                ).count(),
            }
            cache.set(cache_key, stats, timeout=60)  # 1 minute

        return Response({"statistics": stats})

    @action(detail=False, methods=["get"])
    def recent_updates(self, request):
        """Get patients updated recently"""
        hours = int(request.GET.get("hours", 24))
        since = timezone.now() - timedelta(hours=hours)

        queryset = (
            self.get_queryset()
            .filter(updated_at__gte=since)
            .select_related("hospital", "primary_care_physician")
        )

        page = self.paginate_queryset(queryset)
        serializer = PatientListSerializer(page, many=True)

        return self.get_paginated_response(serializer.data)

    def perform_create(self, serializer):
        """Create patient with optimization"""
        patient = serializer.save()

        # Invalidate cache
        cache.delete_many(["patient_stats_*", "quick_patient_stats_*"])

        # Queue for background processing if needed
        from ..core.optimization.cache_optimizer import CacheWarmer

        CacheWarmer.warm_patient_data(patient.id)

    def perform_update(self, serializer):
        """Update patient with cache invalidation"""
        patient = serializer.save()

        # Invalidate caches
        cache_patterns = [
            f"patient_detail_{patient.id}_*",
            "patient_stats_*",
            "quick_patient_stats_*",
        ]
        for pattern in cache_patterns:
            keys = cache.keys(pattern)
            if keys:
                cache.delete_many(keys)

        # Warm cache
        from ..core.optimization.cache_optimizer import CacheWarmer

        CacheWarmer.warm_patient_data(patient.id)
