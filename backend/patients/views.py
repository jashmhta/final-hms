from core.permissions import ModuleEnabledPermission
from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

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
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, "role", None) == "SUPER_ADMIN":
            return qs
        if getattr(user, "hospital_id", None) is None:
            return qs.none()
        return qs.filter(hospital_id=user.hospital_id)

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
