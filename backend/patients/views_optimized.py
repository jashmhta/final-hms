"""
Optimized Patient Views with Performance Enhancements
"""

from datetime import datetime, timedelta

from rest_framework import decorators, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.db.models import Count, Prefetch, Q
from django.utils import timezone

from core.enhanced_cache import enhanced_cache
from core.optimization.cache_optimizer import cache_optimizer, cache_result
from core.optimization.query_optimizer import (
    QueryOptimizer,
    SmartPaginator,
    profile_queries,
)
from core.permissions import ModuleEnabledPermission

from .models import EmergencyContact, InsuranceInformation, Patient
from .serializers import (
    EmergencyContactSerializer,
    InsuranceInformationSerializer,
    PatientListSerializer,
    PatientSerializer,
)


class OptimizedPatientViewSet(viewsets.ModelViewSet):
    """High-performance patient management viewset"""

    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated, ModuleEnabledPermission]
    required_module = "enable_opd"

    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == "list":
            return PatientListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return PatientSerializer
        return PatientSerializer

    def get_queryset(self):
        """Get optimized queryset with caching"""
        user = self.request.user

        if user.is_superuser or getattr(user, "role", None) == "SUPER_ADMIN":
            return Patient.get_optimized_queryset()
        elif getattr(user, "hospital_id", None) is None:
            return Patient.objects.none()
        else:
            return Patient.get_optimized_queryset(user.hospital_id)

    @profile_queries
    def list(self, request, *args, **kwargs):
        """Optimized list with pagination and caching"""
        # Get filter parameters
        filters = {}

        # Apply hospital filter
        user = request.user
        if not (user.is_superuser or getattr(user, "role", None) == "SUPER_ADMIN"):
            filters["hospital_id"] = user.hospital_id

        # Apply other filters
        if status := request.query_params.get("status"):
            filters["status"] = status

        if search := request.query_params.get("search"):
            # Use optimized search
            return self._search_patients(search, filters)

        # Build queryset
        queryset = self.get_queryset().filter(**filters)

        # Apply ordering
        ordering = request.query_params.get("ordering", "-created_at")
        queryset = queryset.order_by(ordering)

        # Use smart pagination
        page_size = min(int(request.query_params.get("page_size", 20)), 100)
        paginator = SmartPaginator(queryset, page_size)

        try:
            page = int(request.query_params.get("page", 1))
            results, meta = paginator.get_page(page)
        except ValueError:
            page = 1
            results, meta = paginator.get_page(page)

        serializer = self.get_serializer(results, many=True)

        return Response({"results": serializer.data, "meta": meta})

    def _search_patients(self, search_query, filters):
        """Optimized patient search with caching"""
        user = self.request.user
        hospital_id = user.hospital_id if not user.is_superuser else None

        cache_key = f"patient_search:{hospital_id}:{hash(search_query)}"

        results = cache_optimizer.smart_cache(
            cache_key, lambda: self._execute_search(search_query, hospital_id, filters), timeout=180, tier="redis"
        )

        # Serialize results
        serializer = self.get_serializer(results, many=True)

        return Response(
            {"results": serializer.data, "meta": {"total_items": len(results), "search_query": search_query}}
        )

    def _execute_search(self, search_query, hospital_id, filters):
        """Execute optimized search query"""
        search_conditions = (
            Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
            | Q(medical_record_number__icontains=search_query)
            | Q(phone_primary__icontains=search_query)
            | Q(email__icontains=search_query)
        )

        if hospital_id:
            search_conditions &= Q(hospital_id=hospital_id)

        if "status" in filters:
            search_conditions &= Q(status=filters["status"])

        return list(
            Patient.get_optimized_queryset(hospital_id=hospital_id).filter(search_conditions)[:100]
        )  # Limit results

    @profile_queries
    def retrieve(self, request, *args, **kwargs):
        """Optimized retrieve with caching"""
        patient_id = kwargs.get("pk")

        # Try cache first
        cache_key = f"patient_detail:{patient_id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        # Get patient with optimized relationships
        patient = self.get_object()

        # Use optimized serializer with all relationships
        serializer = self.get_serializer(patient)

        # Cache the result
        cache.set(cache_key, serializer.data, 300)

        return Response(serializer.data)

    def perform_create(self, serializer):
        """Optimized create with caching invalidation"""
        user = self.request.user

        if not (user.is_superuser or getattr(user, "hospital_id", None)):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("User must belong to a hospital to create patients")

        # Save patient
        patient = serializer.save(hospital_id=user.hospital_id, created_by=user)

        # Invalidate cache
        enhanced_cache.invalidate_by_tag(f"patient_list_hospital_{user.hospital_id}")
        enhanced_cache.invalidate_by_tag("patient_stats")

    def perform_update(self, serializer):
        """Optimized update with caching invalidation"""
        patient = self.get_object()

        # Check permissions
        user = self.request.user
        if not (
            user.is_superuser
            or getattr(user, "hospital_id", None) == patient.hospital_id
            or getattr(user, "role", None) == "SUPER_ADMIN"
        ):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Cannot modify patient from another hospital")

        # Update patient
        serializer.save(last_updated_by=user)

        # Invalidate cache
        enhanced_cache.invalidate_by_tag(f"patient_{patient.id}")
        enhanced_cache.invalidate_by_tag(f"patient_list_hospital_{patient.hospital_id}")

    @decorators.action(detail=False, methods=["get"])
    @cache_result(timeout=300, key_prefix="patient_stats")
    def stats(self, request):
        """Cached patient statistics"""
        user = request.user
        hospital_id = user.hospital_id if not user.is_superuser else None

        # Use aggregated query with caching
        cache_key = f"patient_stats:{hospital_id}"

        stats_data = cache_optimizer.smart_cache(
            cache_key, lambda: self._calculate_patient_stats(hospital_id), timeout=600, tier="redis"
        )

        return Response(stats_data)

    def _calculate_patient_stats(self, hospital_id):
        """Calculate patient statistics efficiently"""
        from django.db.models import Count, Q
        from django.utils import timezone

        queryset = Patient.objects
        if hospital_id:
            queryset = queryset.filter(hospital_id=hospital_id)

        # Single query for all statistics
        stats = queryset.aggregate(
            total_patients=Count("id"),
            active_patients=Count("id", filter=Q(status="ACTIVE")),
            inactive_patients=Count("id", filter=Q(status="INACTIVE")),
            vip_count=Count("id", filter=Q(vip_status=True)),
            portal_enrolled=Count("id", filter=Q(patient_portal_enrolled=True)),
            confidential_count=Count("id", filter=Q(confidential=True)),
        )

        # Calculate new patients in last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        new_patients = queryset.filter(created_at__gte=thirty_days_ago).count()

        # Age distribution (optimized with single query)
        age_groups = self._calculate_age_distribution(queryset)

        return {
            **stats,
            "new_patients_last_30d": new_patients,
            "age_distribution": age_groups,
            "calculated_at": timezone.now().isoformat(),
        }

    def _calculate_age_distribution(self, queryset):
        """Calculate age distribution efficiently"""
        from django.db.models import Count, F
        from django.utils import timezone

        today = timezone.now().date()

        # Calculate ages and group
        age_groups = {"0-18": 0, "19-35": 0, "36-50": 0, "51-65": 0, "65+": 0}

        # Use database calculation for better performance
        for age_range, condition in [
            ("0-18", Q(date_of_birth__gte=today.replace(year=today.year - 18))),
            (
                "19-35",
                Q(
                    date_of_birth__gte=today.replace(year=today.year - 35),
                    date_of_birth__lt=today.replace(year=today.year - 18),
                ),
            ),
            (
                "36-50",
                Q(
                    date_of_birth__gte=today.replace(year=today.year - 50),
                    date_of_birth__lt=today.replace(year=today.year - 36),
                ),
            ),
            (
                "51-65",
                Q(
                    date_of_birth__gte=today.replace(year=today.year - 65),
                    date_of_birth__lt=today.replace(year=today.year - 51),
                ),
            ),
            ("65+", Q(date_of_birth__lt=today.replace(year=today.year - 65))),
        ]:
            age_groups[age_range] = queryset.filter(condition).count()

        return age_groups

    @decorators.action(detail=False, methods=["get"])
    def export(self, request):
        """Optimized patient data export"""
        user = request.user
        hospital_id = user.hospital_id if not user.is_superuser else None

        # Use streaming for large datasets
        import csv
        import io

        from django.http import StreamingHttpResponse

        def generate_csv():
            """Generate CSV row by row to avoid memory issues"""
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(
                [
                    "ID",
                    "Medical Record Number",
                    "Name",
                    "Date of Birth",
                    "Gender",
                    "Status",
                    "Phone",
                    "Email",
                    "City",
                    "State",
                ]
            )
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

            # Stream patient data
            queryset = Patient.get_optimized_queryset(hospital_id).only(
                "id",
                "medical_record_number",
                "first_name",
                "last_name",
                "date_of_birth",
                "gender",
                "status",
                "phone_primary",
                "email",
                "city",
                "state",
            )

            for patient in queryset.iterator(chunk_size=1000):
                writer.writerow(
                    [
                        patient.id,
                        patient.medical_record_number,
                        f"{patient.first_name} {patient.last_name}",
                        patient.date_of_birth,
                        patient.gender,
                        patient.status,
                        patient.phone_primary,
                        patient.email,
                        patient.city,
                        patient.state,
                    ]
                )
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)

        response = StreamingHttpResponse(generate_csv(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="patients.csv"'
        return response


class OptimizedEmergencyContactViewSet(viewsets.ModelViewSet):
    """Optimized emergency contact management"""

    serializer_class = EmergencyContactSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get optimized queryset"""
        patient_id = self.kwargs.get("patient_pk")
        return EmergencyContact.objects.filter(patient_id=patient_id).select_related("patient")

    def perform_create(self, serializer):
        """Create with caching invalidation"""
        patient_id = self.kwargs.get("patient_pk")
        serializer.save(patient_id=patient_id)
        enhanced_cache.invalidate_by_tag(f"patient_{patient_id}")

    def perform_update(self, serializer):
        """Update with caching invalidation"""
        contact = self.get_object()
        serializer.save()
        enhanced_cache.invalidate_by_tag(f"patient_{contact.patient_id}")

    def perform_destroy(self, instance):
        """Delete with caching invalidation"""
        patient_id = instance.patient_id
        instance.delete()
        enhanced_cache.invalidate_by_tag(f"patient_{patient_id}")


class OptimizedInsuranceViewSet(viewsets.ModelViewSet):
    """Optimized insurance information management"""

    serializer_class = InsuranceInformationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get optimized queryset"""
        patient_id = self.kwargs.get("patient_pk")
        return (
            InsuranceInformation.objects.filter(patient_id=patient_id)
            .select_related("patient")
            .order_by("insurance_type")
        )

    def perform_create(self, serializer):
        """Create with caching invalidation"""
        patient_id = self.kwargs.get("patient_pk")
        serializer.save(patient_id=patient_id)
        enhanced_cache.invalidate_by_tag(f"patient_{patient_id}")

    def perform_update(self, serializer):
        """Update with caching invalidation"""
        insurance = self.get_object()
        serializer.save()
        enhanced_cache.invalidate_by_tag(f"patient_{insurance.patient_id}")

    def perform_destroy(self, instance):
        """Delete with caching invalidation"""
        patient_id = instance.patient_id
        instance.delete()
        enhanced_cache.invalidate_by_tag(f"patient_{patient_id}")
