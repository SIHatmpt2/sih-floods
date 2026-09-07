from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from .models import DashboardSnapshot, NotificationRecord, UserLocation


def nearest_location(user, latitude, longitude):
    point = Point(longitude, latitude, srid=4326)
    return (
        UserLocation.objects.filter(user=user)
        .annotate(distance=Distance("location", point))
        .order_by("distance")
        .first()
    )


def user_notifications(user, unread_only=False):
    queryset = NotificationRecord.objects.filter(user=user).order_by("-created_at")
    if unread_only:
        queryset = queryset.exclude(status="read")
    return queryset


def latest_dashboard_snapshot(user):
    return DashboardSnapshot.objects.filter(user=user).order_by("-timestamp").first()
