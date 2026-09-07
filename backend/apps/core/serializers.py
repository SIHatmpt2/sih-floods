from rest_framework import serializers
from .models import UserLocation, DashboardSnapshot, NotificationRecord


class CoordinateQuerySerializer(serializers.Serializer):
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lon = serializers.FloatField(min_value=-180, max_value=180)


class UserLocationSerializer(serializers.ModelSerializer):
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = UserLocation
        fields = ["id", "name", "location", "latitude", "longitude", "is_primary"]
        read_only_fields = ["id", "location", "latitude", "longitude"]

    def get_latitude(self, obj):
        return obj.location.y

    def get_longitude(self, obj):
        return obj.location.x


class DashboardSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardSnapshot
        fields = "__all__"


class NotificationRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationRecord
        fields = "__all__"
        read_only_fields = ["user", "created_at", "read_at"]
