from core.permissions import ModuleEnabledPermission
from core.enhanced_cache import enhanced_cache, cache_result
from rest_framework import permissions, viewsets, decorators
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from .models import Patient
from .serializers import PatientSerializer
class IsSameHospital(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user_hospital_id = getattr(request.user, "hospital_id", None)
        return user_hospital_id is None or obj.hospital_id == user_hospital_id
class PatientViewSet(viewsets.ModelViewSet):
    serializer_class = PatientSerializer
    queryset = Patient.objects.all()
    filterset_fields = ["gender", "status"]
    search_fields = ["first_name", "last_name", "phone", "email"]
    ordering_fields = ["last_name", "first_name", "created_at"]
    permission_classes = [permissions.IsAuthenticated, ModuleEnabledPermission]
    required_module = "enable_opd"
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or getattr(user, "role", None) == "SUPER_ADMIN":
            return Patient.get_optimized_queryset()
        elif getattr(user, "hospital_id", None) is None:
            return Patient.objects.none()
        else:
            return Patient.get_optimized_queryset(user.hospital_id)
    def perform_create(self, serializer):
        user = self.request.user
        if not (user.is_superuser or getattr(user, "hospital_id", None)):
            raise PermissionDenied("User must belong to a hospital to create patients")
        provided_hospital = serializer.validated_data.get("hospital")
        if provided_hospital and (
            not (user.is_superuser or user.role == "SUPER_ADMIN")
            and provided_hospital.id != user.hospital_id
        ):
            raise PermissionDenied("Cannot create patient for another hospital")
        serializer.save(
            hospital_id=(
                provided_hospital.id if provided_hospital else user.hospital_id
            )
        )
    def perform_update(self, serializer):
        instance = self.get_object()
        user = self.request.user
        if not (
            user.is_superuser
            or getattr(user, "hospital_id", None) == instance.hospital_id
            or getattr(user, "role", None) == "SUPER_ADMIN"
        ):
            raise PermissionDenied("Cannot modify patient from another hospital")
        patient = serializer.save()
        enhanced_cache.invalidate_by_tag(f"patient_{patient.id}")
        enhanced_cache.invalidate_by_tag(f"patient_{patient.hospital_id}")
        return patient
    @decorators.action(detail=False, methods=["get"])
    @cache_result(
        timeout=300, key_prefix="patient_search", tags=["patient_data"]
    )
    def search(self, request):
        query = request.GET.get("q", "").strip()
        if len(query) < 2:
            return Response(
                {"error": "Search query must be at least 2 characters"}, status=400
            )
        user = request.user
        hospital_id = user.hospital_id if not user.is_superuser else None
        results = Patient.search_patients(hospital_id, query, limit=100)
        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)
    @decorators.action(detail=False, methods=["get"])
    @cache_result(
        timeout=180, key_prefix="patient_stats", tags=["analytics_data"]
    )
    def stats(self, request):
        from django.db.models import Count, Q
        from datetime import datetime, timedelta
        user = request.user
        hospital_id = user.hospital_id if not user.is_superuser else None
        queryset = (
            Patient.objects.filter(hospital_id=hospital_id)
            if hospital_id
            else Patient.objects.all()
        )
        total_patients = queryset.count()
        active_patients = queryset.filter(status="ACTIVE").count()
        new_patients_last_30d = queryset.filter(
            created_at__gte=datetime.now() - timedelta(days=30)
        ).count()
        age_groups = {
            "0-18": queryset.filter(
                date_of_birth__gte=datetime.now().replace(year=datetime.now().year - 18)
            ).count(),
            "19-35": queryset.filter(
                date_of_birth__gte=datetime.now().replace(
                    year=datetime.now().year - 35
                ),
                date_of_birth__lt=datetime.now().replace(year=datetime.now().year - 18),
            ).count(),
            "36-50": queryset.filter(
                date_of_birth__gte=datetime.now().replace(
                    year=datetime.now().year - 50
                ),
                date_of_birth__lt=datetime.now().replace(year=datetime.now().year - 36),
            ).count(),
            "51+": queryset.filter(
                date_of_birth__lt=datetime.now().replace(year=datetime.now().year - 50)
            ).count(),
        }
        return Response(
            {
                "total_patients": total_patients,
                "active_patients": active_patients,
                "new_patients_last_30d": new_patients_last_30d,
                "age_distribution": age_groups,
            }
        )