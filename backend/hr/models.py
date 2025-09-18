from core.models import TenantModel, TimeStampedModel
from django.db import models
class Shift(TenantModel):
    name = models.CharField(max_length=64)
    start_time = models.TimeField()
    end_time = models.TimeField()
    class Meta:
        unique_together = (("hospital", "name"),)
        ordering = ["start_time"]
class DutyRoster(TenantModel):
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="duty_rosters"
    )
    date = models.DateField()
    shift = models.ForeignKey(
        Shift, on_delete=models.PROTECT, related_name="roster_entries"
    )
    class Meta:
        unique_together = (("hospital", "user", "date"),)
        ordering = ["date"]
class LeaveRequest(TenantModel):
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="leave_requests"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        default="PENDING",
        choices=[
            ("PENDING", "Pending"),
            ("APPROVED", "Approved"),
            ("REJECTED", "Rejected"),
        ],
    )
    class Meta:
        ordering = ["-start_date"]