from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Feedback
from .serializers import FeedbackSerializer
class FeedbackViewSet(viewsets.ModelViewSet):
    serializer_class = FeedbackSerializer
    queryset = Feedback.objects.select_related("patient").all()
    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [IsAuthenticated()]
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        if user.is_superuser or getattr(user, "role", None) == "SUPER_ADMIN":
            return qs
        if getattr(user, "hospital_id", None) is None:
            return qs.none()
        return qs.filter(hospital_id=user.hospital_id)
    def perform_create(self, serializer):
        user = self.request.user
        hospital = serializer.validated_data.get("hospital")
        if user.is_authenticated and not (
            user.is_superuser or getattr(user, "role", None) == "SUPER_ADMIN"
        ):
            if hospital and hospital.id != getattr(user, "hospital_id", None):
                raise PermissionDenied("Cannot submit feedback for another hospital")
        serializer.save()