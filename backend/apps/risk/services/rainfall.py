from datetime import timedelta
from django.contrib.gis.geos import Point
from django.utils import timezone
from apps.weather.models import WeatherObservation


def rainfall_features(latitude, longitude):
    p = Point(float(longitude), float(latitude), srid=4326)
    qs = WeatherObservation.objects.filter(
        station__active=True,
        station__location__distance_lte=(p, 50000),
    )
    now = timezone.now()
    result = {}
    for label, hours in (("24h", 24), ("3d", 72), ("7d", 168)):
        values = qs.filter(timestamp__gte=now - timedelta(hours=hours)).values_list("rainfall_mm", flat=True)
        result[f"rainfall_{label}_mm"] = sum(v for v in values if v is not None)
    return result
