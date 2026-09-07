from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from .models import UserLocation, NotificationRecord


def nearest_location(user, lat, lon):
    p = Point(float(lon), float(lat), srid=4326)
    return UserLocation.objects.filter(user=user).annotate(distance=Distance("location", p)).order_by("distance").first()


def user_notifications(user, unread_only=False):
    qs = NotificationRecord.objects.filter(user=user).order_by("-created_at")
    if unread_only:
        qs = qs.exclude(status="read")
    return qs
