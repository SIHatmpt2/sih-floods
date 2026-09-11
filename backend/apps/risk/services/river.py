from __future__ import annotations

from datetime import datetime, timedelta

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db.models import Q
from django.utils import timezone

from apps.weather.models import WeatherStation


def _stations(point):
    """
    Return up to five nearest stations with usable river observations.

    CWC stations are preferred when available; otherwise stations from
    other providers are returned.
    """
    base = (
        WeatherStation.objects.filter(
            Q(observations__discharge_m3s__isnull=False)
            | Q(observations__water_level_m__isnull=False),
            active=True,
            location__distance_lte=(point, 75_000),
        )
        .distinct()
    )

    cwc = (
        base.filter(provider="cwc")
        .annotate(distance=Distance("location", point))
        .order_by("distance")
    )

    stations = list(cwc[:5])
    if stations:
        return stations

    return list(
        base.annotate(distance=Distance("location", point))
        .order_by("distance")[:5]
    )


def river_features(latitude, longitude):
    point = Point(float(longitude), float(latitude), srid=4326)
    stations = _stations(point)

    empty = {
        "water_level_m": None,
        "discharge_m3s": None,
        "water_level_change": None,
        "discharge_change": None,
    }

    if not stations:
        return empty

    now = timezone.now()
    latest = None
    station = None

    for candidate in stations:
        observation = (
            candidate.observations.filter(timestamp__lte=now)
            .filter()
            .order_by("-timestamp")
            .first()
        )
        if observation is not None:
            latest = observation
            station = candidate
            break

    if latest is None:
        return empty

    previous = None
    if isinstance(latest.timestamp, datetime):
        previous = (
            station.observations.filter(timestamp__lt=latest.timestamp)
            .filter(
                timestamp__gte=latest.timestamp - timedelta(hours=24)
            )
            .order_by("-timestamp")
            .first()
        )

    return {
        "water_level_m": latest.water_level_m,
        "discharge_m3s": latest.discharge_m3s,
        "water_level_change": (
            latest.water_level_m - previous.water_level_m
            if previous
            and latest.water_level_m is not None
            and previous.water_level_m is not None
            else None
        ),
        "discharge_change": (
            latest.discharge_m3s - previous.discharge_m3s
            if previous
            and latest.discharge_m3s is not None
            and previous.discharge_m3s is not None
            else None
        ),
    }
