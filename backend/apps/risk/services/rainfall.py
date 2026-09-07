from datetime import timedelta
from django.utils import timezone


def _latest_observation_model():
    try:
        from backend.apps.weather.models import WeatherObservation
        return WeatherObservation
    except ImportError:
        return None


def rainfall_features(latitude, longitude):
    model = _latest_observation_model()
    if model is None:
        return {"rainfall_24h_mm": None, "rainfall_3d_mm": None, "rainfall_7d_mm": None}

    field_names = {field.name for field in model._meta.get_fields() if hasattr(field, "name")}
    required = {"location", "timestamp", "rainfall"}
    if not required.issubset(field_names):
        return {"rainfall_24h_mm": None, "rainfall_3d_mm": None, "rainfall_7d_mm": None}

    from django.contrib.gis.geos import Point
    qs = model.objects.filter(
        location__distance_lte=(Point(float(longitude), float(latitude), srid=4326), 50000)
    )
    now = timezone.now()

    def total_since(hours):
        since = now - timedelta(hours=hours)
        values = qs.filter(timestamp__gte=since).values_list("rainfall", flat=True)
        return sum(v for v in values if v is not None)

    return {
        "rainfall_24h_mm": total_since(24),
        "rainfall_3d_mm": total_since(72),
        "rainfall_7d_mm": total_since(168),
    }
