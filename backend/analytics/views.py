from appointments.models import Appointment
from billing.models import Bill
from django.db.models import Sum
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema
from patients.models import Patient
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import OverviewStatsSerializer

# Create your views here.


class OverviewStatsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=OpenApiResponse(response=OverviewStatsSerializer))
    def get(self, request):
        user = request.user
        filters = {}
        if not (user.is_superuser or getattr(user, "role", None) == "SUPER_ADMIN"):
            filters["hospital_id"] = getattr(user, "hospital_id", None)
        patients_count = Patient.objects.filter(**filters).count()
        today = timezone.localdate()
        appointments_today = Appointment.objects.filter(
            **filters, start_at__date=today
        ).count()
        revenue_cents = (
            Bill.objects.filter(**filters).aggregate(total=Sum("paid_cents"))["total"]
            or 0
        )
        return Response(
            {
                "patients_count": patients_count,
                "appointments_today": appointments_today,
                "revenue_cents": revenue_cents,
            }
        )
