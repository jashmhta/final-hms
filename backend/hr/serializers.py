from rest_framework import serializers
from .models import DutyRoster, LeaveRequest, Shift
class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ["id", "hospital", "name", "start_time", "end_time"]
class DutyRosterSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutyRoster
        fields = ["id", "hospital", "user", "date", "shift"]
class LeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = [
            "id",
            "hospital",
            "user",
            "start_date",
            "end_date",
            "reason",
            "status",
        ]