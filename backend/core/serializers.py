from rest_framework import serializers


class HealthSerializer(serializers.Serializer):
    status = serializers.CharField()
    database = serializers.BooleanField()
