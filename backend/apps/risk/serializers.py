from rest_framework import serializers
from .models import FloodEvent, RiskZone, RiskAssessment, RiskAlert, HotspotSnapshot


class CoordinateQuerySerializer(serializers.Serializer):
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lon = serializers.FloatField(min_value=-180, max_value=180)
    radius_km = serializers.FloatField(min_value=0.1, max_value=500, default=25)


class DaysQuerySerializer(serializers.Serializer):
    days = serializers.IntegerField(min_value=1, max_value=365, default=7)


class FloodEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = FloodEvent
        fields = "__all__"


class RiskZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskZone
        fields = "__all__"


class RiskAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskAssessment
        fields = "__all__"


class RiskAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskAlert
        fields = "__all__"


class HotspotSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotspotSnapshot
        fields = "__all__"
