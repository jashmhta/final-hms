from rest_framework import serializers
from .models import MLModel, Prediction, Anomaly, EquipmentPrediction


class OverviewStatsSerializer(serializers.Serializer):
    patients_count = serializers.IntegerField()
    appointments_today = serializers.IntegerField()
    revenue_cents = serializers.IntegerField()


class MLModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLModel
        fields = '__all__'


class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prediction
        fields = '__all__'


class AnomalySerializer(serializers.ModelSerializer):
    class Meta:
        model = Anomaly
        fields = '__all__'


class EquipmentPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentPrediction
        fields = '__all__'
