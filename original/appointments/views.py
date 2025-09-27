"""
views module
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import Appointment
from .serializers import AppointmentSerializer


class AppointmentListCreateView(APIView):
    def get(self, request):
        queryset = Appointment.objects.filter(is_active=True, patient__is_active=True)
        if request.query_params.get("status") == "completed":
            queryset = queryset.filter(status="completed")
        serializer = AppointmentSerializer(queryset, many=True)
        return Response(serializer.data)
    def post(self, request):
        with transaction.atomic():
            appointment_data = request.data.copy()
            if not appointment_data.get("patient_id"):
                return Response(
                    {"error": "Patient ID required"}, status=status.HTTP_400_BAD_REQUEST
                )
            appointment = Appointment.objects.create(**appointment_data)
            if appointment.status == "scheduled":
                pass
        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)