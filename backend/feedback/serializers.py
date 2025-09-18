from rest_framework import serializers
from .models import Feedback
class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ["id", "hospital", "patient", "rating", "comments", "submitted_at"]
        read_only_fields = ["id", "submitted_at"]