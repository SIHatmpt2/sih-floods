from __future__ import annotations

from datetime import timedelta

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db.models import Sum
from django.utils import timezone

from apps.weather.models import WeatherStation


def rainfall_features(latitude, longitude):
    point = Point(float(longitude), float(latitude), srid=4326)
    stations = (
        WeatherStation.objects.filter(
            active=True,
            observations__rainfall_mm__isnull=False,
            location__distance_lte=(point, 50_000),
        )
        .annotate(distance=Distance("location", point))
        .order_by("distance")
        .distinct()[:5]
    )
    stations = list(stations)
    now = timezone.now()
    result = {}
    for label, hours in (("24h", 24), ("3d", 72), ("7d", 168), ("30d", 720)):
        since = now - timedelta(hours=hours)
        weighted_total = 0.0
        weight_total = 0.0
        for station in stations:
            total = station.observations.filter(
                timestamp__gte=since,
                timestamp__lte=now,
                rainfall_mm__isnull=False,
            ).aggregate(total=Sum("rainfall_mm"))["total"]
            if total is None:
                continue
            distance_km = max(float(station.distance.m) / 1000.0, 0.0)
            weight = 1.0 / (1.0 + distance_km)
            weighted_total += float(total) * weight
            weight_total += weight
        result[f"rainfall_{label}_mm"] = round(weighted_total / weight_total, 3) if weight_total else None
    return result
