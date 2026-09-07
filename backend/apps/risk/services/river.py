from __future__ import annotations

from datetime import timedelta

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.utils import timezone

from apps.weather.models import WeatherStation


def _stations(point):
    base = WeatherStation.objects.filter(
        active=True,
        location__distance_lte=(point, 75_000),
        observations__discharge_m3s__isnull=False,
    ).distinct()
    cwc = base.filter(provider="cwc").annotate(distance=Distance("location", point)).order_by("distance")
    return list(cwc[:5]) or list(base.annotate(distance=Distance("location", point)).order_by("distance")[:5])


def river_features(latitude, longitude):
    point = Point(float(longitude), float(latitude), srid=4326)
    stations = _stations(point)
    if not stations:
        return {"water_level_m": None, "discharge_m3s": None, "water_level_change": None,
                "discharge_change": None}

    now = timezone.now()
    for station in stations:
        latest = station.observations.filter(
            timestamp__lte=now,
        ).filter(discharge_m3s__isnull=False).order_by("-timestamp").first()
        if latest:
            break
    if not latest:
        return {"water_level_m": None, "discharge_m3s": None, "water_level_change": None,
                "discharge_change": None}

    previous = station.observations.filter(
        timestamp__lt=latest.timestamp,
        timestamp__gte=latest.timestamp - timedelta(hours=24),
        discharge_m3s__isnull=False,
    ).order_by("-timestamp").first()
    return {
        "water_level_m": latest.water_level_m,
        "discharge_m3s": latest.discharge_m3s,
        "water_level_change": (
            latest.water_level_m - previous.water_level_m
            if previous and latest.water_level_m is not None and previous.water_level_m is not None
            else None
        ),
        "discharge_change": (
            latest.discharge_m3s - previous.discharge_m3s
            if previous and latest.discharge_m3s is not None and previous.discharge_m3s is not None
            else None
        ),
    }
