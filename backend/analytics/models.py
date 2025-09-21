from django.db import models


class MLModel(models.Model):
    name = models.CharField(max_length=255)
    model_file = models.FileField(upload_to="ml_models/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Prediction(models.Model):
    model = models.ForeignKey(MLModel, on_delete=models.CASCADE)
    input_data = models.JSONField()
    prediction = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)


class Anomaly(models.Model):
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE)
    anomaly_score = models.FloatField()
    detected_at = models.DateTimeField(auto_now_add=True)
    details = models.TextField()


class EquipmentPrediction(models.Model):
    equipment_id = models.CharField(max_length=255)
    failure_probability = models.FloatField()
    predicted_at = models.DateTimeField(auto_now_add=True)
