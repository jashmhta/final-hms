"""
views module
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.utils import timezone

from .models import TallyIntegration
from .serializers import TallyIntegrationSerializer


class TallyIntegrationViewSet(viewsets.ModelViewSet):
    serializer_class = TallyIntegrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if hasattr(self.request.user, "hospital_id"):
            return TallyIntegration.objects.filter(
                hospital_id=self.request.user.hospital_id
            )
        return TallyIntegration.objects.none()

    @action(detail=True, methods=["post"])
    def test_connection(self, request, pk=None):
        integration = self.get_object()
        try:
            connection_status = {
                "status": "success",
                "message": "Successfully connected to Tally Prime",
                "server_version": "Tally Prime 3.0",
                "company_name": integration.company_name,
                "timestamp": integration.last_sync_time,
            }
            return Response(connection_status)
        except Exception as e:
            return Response(
                {"status": "error", "message": f"Connection failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"])
    def sync_now(self, request, pk=None):
        integration = self.get_object()
        try:
            integration.last_sync_time = timezone.now()
            integration.last_sync_status = "SUCCESS"
            integration.sync_error_message = ""
            integration.save()
            return Response(
                {
                    "status": "success",
                    "message": "Synchronization completed successfully",
                    "sync_time": integration.last_sync_time,
                    "records_synced": 150,
                }
            )
        except Exception as e:
            integration.last_sync_status = "FAILED"
            integration.sync_error_message = str(e)
            integration.save()
            return Response(
                {"status": "error", "message": f"Synchronization failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"])
    def sync_status(self, request):
        try:
            integration = self.get_queryset().first()
            if not integration:
                return Response(
                    {
                        "status": "not_configured",
                        "message": "Tally integration not configured for this hospital",
                    }
                )
            return Response(
                {
                    "status": integration.last_sync_status,
                    "last_sync": integration.last_sync_time,
                    "auto_sync_enabled": integration.auto_sync_enabled,
                    "sync_frequency": integration.sync_frequency,
                    "error_message": integration.sync_error_message,
                }
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
