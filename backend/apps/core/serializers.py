from rest_framework import serializers
from .models import UserLocation, DashboardSnapshot, NotificationRecord


class CoordinateQuerySerializer(serializers.Serializer):
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lon = serializers.FloatField(min_value=-180, max_value=180)


class UserLocationSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True, required=True, min_value=-90, max_value=90)
    longitude = serializers.FloatField(write_only=True, required=True, min_value=-180, max_value=180)

    class Meta:
        model = UserLocation
        fields = ["id", "name", "location", "latitude", "longitude", "is_primary", "created_at"]
        read_only_fields = ["id", "location", "created_at"]


class DashboardSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardSnapshot
        fields = "__all__"


class NotificationRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationRecord
        fields = "__all__"
        read_only_fields = ["user", "created_at", "read_at"]
