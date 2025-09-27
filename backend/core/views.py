"""
views module
"""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render

from .serializers import HealthSerializer


def root_api_view(request):
    return JsonResponse(
        {
            "message": "HMS Backend API",
            "version": "1.0.0",
            "endpoints": {
                "admin": "/admin/",
                "api_docs": "/api/docs/",
                "health": "/health/",
                "auth": "/api/auth/",
                "patients": "/api/patients/",
                "hospitals": "/api/hospitals/",
                "appointments": "/api/appointments/",
            },
        }
    )


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(responses=OpenApiResponse(response=HealthSerializer))
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                row = cursor.fetchone()
            db_ok = row == (1,)
        except Exception:
            db_ok = False
        return Response({"status": "ok", "database": db_ok})
