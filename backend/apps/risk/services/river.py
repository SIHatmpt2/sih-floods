from datetime import timedelta
from django.contrib.gis.geos import Point
from apps.weather.models import WeatherObservation


def river_features(latitude, longitude):
    p = Point(float(longitude), float(latitude), srid=4326)
    qs = WeatherObservation.objects.filter(
        station__active=True,
        station__location__distance_lte=(p, 75000),
    ).order_by("-timestamp")
    latest = qs.first()
    if not latest:
        return {"water_level_m": None, "discharge_m3s": None, "water_level_change": None}
    previous = qs.filter(
        timestamp__lt=latest.timestamp,
        timestamp__gte=latest.timestamp - timedelta(hours=24),
    ).first()
    return {
        "water_level_m": latest.water_level_m,
        "discharge_m3s": latest.discharge_m3s,
        "water_level_change": (
            latest.water_level_m - previous.water_level_m
            if previous and latest.water_level_m is not None and previous.water_level_m is not None
            else None
        ),
    }
