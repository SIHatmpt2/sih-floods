from datetime import timedelta
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.utils import timezone
from .models import FloodEvent, RiskAssessment, RiskAlert, RiskZone


def to_point(latitude, longitude):
    return Point(float(longitude), float(latitude), srid=4326)


def nearest_zone(latitude, longitude, radius_km=25.0):
    p = to_point(latitude, longitude)
    return (RiskZone.objects.filter(is_active=True, geometry__distance_lte=(p, radius_km * 1000))
            .annotate(distance=Distance("geometry", p)).order_by("distance").first())


def nearest_safe_zone(latitude, longitude, radius_km=50.0):
    p = to_point(latitude, longitude)
    return (RiskZone.objects.filter(
                is_active=True,
                risk_level__in=["low", "moderate"],
                geometry__distance_lte=(p, radius_km * 1000),
            )
            .annotate(distance=Distance("geometry", p))
            .order_by("latest_score", "distance")
            .first())


def nearby_zones(latitude, longitude, radius_km=25.0):
    p = to_point(latitude, longitude)
    return (RiskZone.objects.filter(is_active=True, geometry__distance_lte=(p, radius_km * 1000))
            .annotate(distance=Distance("geometry", p)).order_by("distance"))


def high_risk_zones():
    return RiskZone.objects.filter(is_active=True, risk_level__in=["high", "severe"]).order_by("-latest_score")


def latest_assessment(latitude, longitude):
    p = to_point(latitude, longitude)
    return (RiskAssessment.objects.filter(location__distance_lte=(p, 50000))
            .annotate(distance=Distance("location", p)).order_by("distance", "-observed_at").first())


def assessment_history(latitude, longitude, days=7):
    p = to_point(latitude, longitude)
    since = timezone.now() - timedelta(days=days)
    return (RiskAssessment.objects.filter(location__distance_lte=(p, 50000), observed_at__gte=since)
            .annotate(distance=Distance("location", p)).order_by("-observed_at"))


def recent_flood_events(latitude, longitude, radius_km=50.0, days=3650):
    p = to_point(latitude, longitude)
    since = timezone.now().date() - timedelta(days=days)
    return (FloodEvent.objects.filter(location__distance_lte=(p, radius_km * 1000), event_date__gte=since)
            .annotate(distance=Distance("location", p)).order_by("distance", "-event_date"))


def open_alerts():
    return RiskAlert.objects.filter(status__in=["open", "read"]).select_related("zone")


def active_zones():
    return RiskZone.objects.filter(is_active=True)
