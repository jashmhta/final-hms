from core.permissions import ModuleEnabledPermission
from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from .models import Patient
from .serializers import PatientSerializer


class IsSameHospital(permissions.BasePermission):
    """
    Custom permission to ensure users can only access patients from their hospital.

    This permission checks if the requesting user belongs to the same hospital
    as the patient being accessed. Superusers and users without hospital
    assignment have access to all patients.
    """

    def has_object_permission(self, request, view, obj):
        """
        Check object-level permission for patient access.

        Args:
            request: The HTTP request object
            view: The view being accessed
            obj: The patient object being accessed

        Returns:
            bool: True if access is granted, False otherwise
        """
        user_hospital_id = getattr(request.user, "hospital_id", None)
        return user_hospital_id is None or obj.hospital_id == user_hospital_id


class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing patient records.

    Provides CRUD operations for patients with hospital-based access control,
    caching, and performance optimizations.

    Attributes:
        serializer_class: PatientSerializer for data validation
        queryset: Base queryset of all patients
        filterset_fields: Fields available for filtering
        search_fields: Fields available for search
        ordering_fields: Fields available for ordering
        permission_classes: Authentication and module permissions
        required_module: Module that must be enabled

    Methods:
        get_queryset(): Returns filtered queryset based on user permissions
        perform_create(): Creates patient with hospital assignment
        perform_update(): Updates patient with permission checks
    """

    serializer_class = PatientSerializer
    queryset = Patient.objects.all()
    filterset_fields = ["gender", "status"]
    search_fields = ["first_name", "last_name", "phone", "email"]
    ordering_fields = ["last_name", "first_name", "created_at"]
    permission_classes = [permissions.IsAuthenticated, ModuleEnabledPermission]
    required_module = "enable_opd"

    def get_queryset(self):
        from django.core.cache import cache

        user = self.request.user
        qs = super().get_queryset()

        if user.is_superuser or getattr(user, "role", None) == "SUPER_ADMIN":
            queryset = qs
        elif getattr(user, "hospital_id", None) is None:
            queryset = qs.none()
        else:
            queryset = qs.filter(hospital_id=user.hospital_id)

        # Add select_related for performance
        queryset = queryset.select_related('primary_care_physician', 'created_by')

        # Cache expensive queries
        cache_key = f"patient_list:{user.id}:{hash(str(queryset.query))}"
        cached_data = cache.get(cache_key, version=1)

        if cached_data:
            # Return cached queryset if available
            return Patient.objects.filter(id__in=cached_data)

        # Cache patient IDs for 10 minutes
        patient_ids = list(queryset.values_list('id', flat=True)[:1000])  # Limit for performance
        cache.set(cache_key, patient_ids, timeout=600, version=1)

        return queryset

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
        serializer.save()
