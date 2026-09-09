from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.utils import timezone

from apps.weather.models import WeatherObservation, WeatherStation


class WeatherService:
    """Read normalized weather observations; external refresh runs in Celery."""

    def _nearest_station(self, latitude: float, longitude: float):
        point = Point(float(longitude), float(latitude), srid=4326)
        return (
            WeatherStation.objects.filter(active=True, location__distance_lte=(point, 100_000))
            .annotate(distance=Distance("location", point))
            .order_by("distance")
            .first()
        )

    def current(self, latitude: float, longitude: float) -> dict:
        station = self._nearest_station(latitude, longitude)
        if station is None:
            return {
                "station": None,
                "observed_at": None,
                "temperature_c": None,
                "rainfall_mm": None,
                "humidity": None,
                "water_level_m": None,
                "discharge_m3s": None,
                "data_quality": {"available": False, "reason": "no_nearby_station"},
            }

        station_data = {
            "id": station.id,
            "station_id": station.station_id,
            "name": station.name,
            "provider": station.provider,
            "state": station.state,
            "district": station.district,
        }
        observation = station.observations.order_by("-timestamp").first()
        if observation is None:
            return {
                "station": station_data,
                "observed_at": None,
                "temperature_c": None,
                "rainfall_mm": None,
                "humidity": None,
                "water_level_m": None,
                "discharge_m3s": None,
                "data_quality": {"available": False, "reason": "no_observation"},
            }

        max_age = timedelta(minutes=int(getattr(settings, "WEATHER_MAX_AGE_MINUTES", 180)))
        age = timezone.now() - observation.timestamp
        stale = age > max_age
        return {
            "station": station_data,
            "observed_at": observation.timestamp,
            "temperature_c": observation.temperature_c,
            "rainfall_mm": observation.rainfall_mm,
            "humidity": observation.humidity,
            "water_level_m": observation.water_level_m,
            "discharge_m3s": observation.discharge_m3s,
            "data_quality": {
                "available": True,
                "stale": stale,
                "age_minutes": round(age.total_seconds() / 60, 1),
            },
        }

    def history(self, latitude: float, longitude: float, days: int = 7) -> list[dict]:
        station = self._nearest_station(latitude, longitude)
        if station is None:
            return []
        since = timezone.now() - timedelta(days=days)
        rows = station.observations.filter(timestamp__gte=since).order_by("-timestamp")[:2000]
        return [
            {
                "observed_at": row.timestamp,
                "rainfall_mm": row.rainfall_mm,
                "temperature_c": row.temperature_c,
                "humidity": row.humidity,
                "water_level_m": row.water_level_m,
                "discharge_m3s": row.discharge_m3s,
            }
            for row in rows
        ]
