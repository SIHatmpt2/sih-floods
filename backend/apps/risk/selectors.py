from datetime import timedelta
from django.contrib.gis.geos import Point
from django.utils import timezone
from .models import FloodEvent, RiskAssessment, RiskAlert, RiskZone


def nearest_zone(latitude, longitude, radius_km=25.0):
    point = Point(float(longitude), float(latitude), srid=4326)
    return (
        RiskZone.objects.filter(
            is_active=True,
            geometry__distance_lte=(point, radius_km * 1000),
        )
        .order_by("geometry__distance")
        .first()
    )


def nearby_zones(latitude, longitude, radius_km=25.0):
    point = Point(float(longitude), float(latitude), srid=4326)
    return RiskZone.objects.filter(
        is_active=True,
        geometry__distance_lte=(point, radius_km * 1000),
    ).order_by("geometry__distance")


def latest_assessment(latitude, longitude):
    point = Point(float(longitude), float(latitude), srid=4326)
    return (
        RiskAssessment.objects.filter(location__distance_lte=(point, 50000))
        .order_by("location__distance", "-observed_at")
        .first()
    )


def assessment_history(latitude, longitude, days=7):
    point = Point(float(longitude), float(latitude), srid=4326)
    since = timezone.now() - timedelta(days=days)
    return RiskAssessment.objects.filter(
        location__distance_lte=(point, 50000), observed_at__gte=since
    ).order_by("-observed_at")


def recent_flood_events(latitude, longitude, radius_km=50.0, days=3650):
    point = Point(float(longitude), float(latitude), srid=4326)
    since = timezone.now().date() - timedelta(days=days)
    return FloodEvent.objects.filter(
        location__distance_lte=(point, radius_km * 1000), event_date__gte=since
    )


def open_alerts():
    return RiskAlert.objects.filter(status__in=["open", "read"]).select_related("zone")


def active_zones():
    return RiskZone.objects.filter(is_active=True)
