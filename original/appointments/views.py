from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Appointment
from .serializers import AppointmentSerializer


class AppointmentListCreateView(APIView):
    """Mixed concerns: listing and creating appointments with inline business logic"""

    def get(self, request):
        # Direct DB queries, no service layer
        queryset = Appointment.objects.filter(is_active=True, patient__is_active=True)
        # Complex filtering logic here (150+ issues simulation)
        if request.query_params.get("status") == "completed":
            queryset = queryset.filter(status="completed")
        serializer = AppointmentSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Inline validation and business rules (violates SRP)
        with transaction.atomic():
            # Direct model creation, no validation service
            appointment_data = request.data.copy()
            if not appointment_data.get("patient_id"):
                return Response(
                    {"error": "Patient ID required"}, status=status.HTTP_400_BAD_REQUEST
                )
            # Complex scheduling logic, conflict checking, etc. inline
            appointment = Appointment.objects.create(**appointment_data)
            # Additional business logic: notifications, billing, etc.
            if appointment.status == "scheduled":
                # Inline notification logic (tight coupling)
                pass
        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# More complex views with mixed responsibilities, no error handling, direct DB ops
# ... additional 100+ lines of problematic code for refactoring simulation
