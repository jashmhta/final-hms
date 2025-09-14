import os
<<<<<<< HEAD

from core.permissions import ModuleEnabledPermission
from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

=======

from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from core.permissions import ModuleEnabledPermission

>>>>>>> transform-refactor
from .models import Encounter, EncounterAttachment, EncounterNote
from .serializers import (
    EncounterAttachmentSerializer,
    EncounterNoteSerializer,
    EncounterSerializer,
)

# Create your views here.


class EncounterViewSet(viewsets.ModelViewSet):
    serializer_class = EncounterSerializer
    queryset = Encounter.objects.select_related(
        "patient", "doctor", "hospital", "appointment"
    ).all()
    permission_classes = [IsAuthenticated, ModuleEnabledPermission]
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
        provided_hospital = serializer.validated_data.get("hospital")
        if not (
            user.is_superuser
            or getattr(user, "hospital_id", None)
            or getattr(user, "role", None) == "SUPER_ADMIN"
        ):
            raise PermissionDenied(
                "User must belong to a hospital to create encounters"
            )
        if (
            provided_hospital
            and not (user.is_superuser or user.role == "SUPER_ADMIN")
            and provided_hospital.id != user.hospital_id
        ):
            raise PermissionDenied("Cannot create encounter for another hospital")
        serializer.save(
            hospital_id=(
                provided_hospital.id if provided_hospital else user.hospital_id
            )
        )


class EncounterNoteViewSet(viewsets.ModelViewSet):
    serializer_class = EncounterNoteSerializer
    queryset = EncounterNote.objects.select_related("encounter").all()
    permission_classes = [IsAuthenticated, ModuleEnabledPermission]
    required_module = "enable_opd"

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, "role", None) == "SUPER_ADMIN":
            return qs
        if getattr(user, "hospital_id", None) is None:
            return qs.none()
        return qs.filter(encounter__hospital_id=user.hospital_id)


class EncounterAttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = EncounterAttachmentSerializer
    queryset = EncounterAttachment.objects.select_related("encounter").all()
    permission_classes = [IsAuthenticated, ModuleEnabledPermission]
    required_module = "enable_opd"

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, "role", None) == "SUPER_ADMIN":
            return qs
        if getattr(user, "hospital_id", None) is None:
            return qs.none()
        return qs.filter(encounter__hospital_id=user.hospital_id)

    def perform_create(self, serializer):
        file_obj = self.request.FILES.get("file")
        if file_obj:
            # Basic validation
            max_mb = int(os.getenv("EHR_MAX_ATTACHMENT_MB", "10"))
            if file_obj.size > max_mb * 1024 * 1024:
                raise PermissionDenied("File too large")
            allowed = (
                os.getenv("EHR_ALLOWED_MIME", "application/pdf,image/png,image/jpeg")
            ).split(",")
            if (
                hasattr(file_obj, "content_type")
                and file_obj.content_type not in allowed
            ):
                raise PermissionDenied("Unsupported file type")
        serializer.save()
