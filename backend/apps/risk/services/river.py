from datetime import timedelta
from django.utils import timezone
from django.contrib.gis.geos import Point


def river_features(latitude, longitude):
    try:
        from backend.apps.weather.models import WeatherObservation
    except ImportError:
        return {"water_level_m": None, "discharge": None, "water_level_change": None}

    field_names = {field.name for field in WeatherObservation._meta.get_fields() if hasattr(field, "name")}
    required = {"location", "timestamp"}
    if not required.issubset(field_names):
        return {"water_level_m": None, "discharge": None, "water_level_change": None}

    point = Point(float(longitude), float(latitude), srid=4326)
    qs = WeatherObservation.objects.filter(location__distance_lte=(point, 75000)).order_by("-timestamp")
    latest = qs.first()
    if latest is None:
        return {"water_level_m": None, "discharge": None, "water_level_change": None}

    previous = qs.filter(
        timestamp__lt=latest.timestamp,
        timestamp__gte=latest.timestamp - timedelta(hours=24),
    ).first()
    latest_level = getattr(latest, "water_level", None)
    previous_level = getattr(previous, "water_level", None) if previous else None
    return {
        "water_level_m": latest_level,
        "discharge": getattr(latest, "discharge", None),
        "water_level_change": latest_level - previous_level if latest_level is not None and previous_level is not None else None,
    }
