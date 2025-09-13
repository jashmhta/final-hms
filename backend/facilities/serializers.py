from rest_framework import serializers

from .models import Bed, Ward


class WardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ward
        fields = ["id", "hospital", "name", "floor"]


class BedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bed
        fields = ["id", "hospital", "ward", "number", "is_occupied", "occupant"]
