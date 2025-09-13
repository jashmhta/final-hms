from rest_framework import serializers


class OverviewStatsSerializer(serializers.Serializer):
    patients_count = serializers.IntegerField()
    appointments_today = serializers.IntegerField()
    revenue_cents = serializers.IntegerField()
