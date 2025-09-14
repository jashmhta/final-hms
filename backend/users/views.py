from django.contrib.auth.hashers import make_password
<<<<<<< HEAD
from django.shortcuts import render
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status, viewsets
=======
from drf_spectacular.utils import OpenApiResponse, extend_schema
>>>>>>> transform-refactor
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
<<<<<<< HEAD
=======
from rest_framework.viewsets import ViewSet
>>>>>>> transform-refactor

from .models import User
from .serializers import UserSerializer

<<<<<<< HEAD
# Create your views here.

=======
>>>>>>> transform-refactor

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=OpenApiResponse(response=UserSerializer))
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UserViewSet(ViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.select_related("hospital").all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.is_superuser or getattr(user, "role", None) == "SUPER_ADMIN":
            return qs
        if getattr(user, "hospital_id", None):
            return qs.filter(hospital_id=user.hospital_id)
        return qs.none()

    def perform_create(self, serializer):
        actor = self.request.user
        role = serializer.validated_data.get("role")
        hospital = serializer.validated_data.get("hospital")
        if not (
            actor.is_superuser
            or getattr(actor, "role", None) in ["SUPER_ADMIN", "HOSPITAL_ADMIN"]
        ):
            raise PermissionDenied("Not allowed to create users")
        if getattr(actor, "role", None) == "HOSPITAL_ADMIN":
            if role == "SUPER_ADMIN":
                raise PermissionDenied("Hospital admin cannot create super admin")
            if hospital and hospital.id != actor.hospital_id:
                raise PermissionDenied("Cannot assign user to another hospital")
        password = (
            serializer.validated_data.get("password")
            if hasattr(serializer, "validated_data")
            else None
        )
        obj = serializer.save()
        if password:
            obj.password = make_password(password)
            obj.save(update_fields=["password"])

    def perform_update(self, serializer):
        actor = self.request.user
        role = serializer.validated_data.get("role", None)
        hospital = serializer.validated_data.get("hospital", None)
        if getattr(actor, "role", None) == "HOSPITAL_ADMIN":
            if role == "SUPER_ADMIN":
                raise PermissionDenied("Hospital admin cannot elevate to super admin")
            if hospital and hospital.id != actor.hospital_id:
                raise PermissionDenied("Cannot move user to another hospital")
        password = serializer.validated_data.get("password", None)
        obj = serializer.save()
        if password:
            obj.password = make_password(password)
            obj.save(update_fields=["password"])
