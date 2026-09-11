from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.utils import timezone

from apps.weather.models import WeatherObservation, WeatherStation
from apps.weather.services.live import fetch_current


class WeatherService:
    """Provide normalized current weather, refreshing from live providers first."""

    def _nearest_station(self, latitude: float, longitude: float):
        point = Point(float(longitude), float(latitude), srid=4326)
        return (
            WeatherStation.objects.filter(active=True, location__distance_lte=(point, 100_000))
            .annotate(distance=Distance("location", point))
            .order_by("distance")
            .first()
        )

    def _format_live(self, row: dict) -> dict:
        """Return provider data directly without requiring DB persistence."""
        timestamp = row["timestamp"]
        max_age = timedelta(minutes=int(getattr(settings, "WEATHER_MAX_AGE_MINUTES", 180)))
        age_minutes = (timezone.now() - timestamp).total_seconds() / 60
        return {
            "station": {
                "id": None,
                "station_id": row["station_id"],
                "name": row["station_name"],
                "provider": row["provider"],
            },
            "observed_at": timestamp,
            "temperature_c": row.get("temperature_c"),
            "rainfall_mm": row.get("rainfall_mm"),
            "rainfall_24h_mm": row.get("rainfall_mm"),
            "humidity": row.get("humidity"),
            "water_level_m": row.get("water_level_m"),
            "discharge_m3s": row.get("discharge_m3s"),
            "data_quality": {
                "available": True,
                "stale": timezone.now() - timestamp > max_age,
                "age_minutes": round(age_minutes, 1),
                "source": row["provider"],
                "persisted": False,
            },
        }

    def _store_live(self, row: dict) -> dict:
        station, _ = WeatherStation.objects.update_or_create(
            provider=row["provider"], station_id=row["station_id"],
            defaults={
                "name": row["station_name"], "state": row.get("state", ""),
                "district": row.get("district", ""),
                "location": Point(row["longitude"], row["latitude"], srid=4326),
                "active": True,
            },
        )
        observation, _ = WeatherObservation.objects.update_or_create(
            station=station, timestamp=row["timestamp"],
            defaults={
                "rainfall_mm": row.get("rainfall_mm"),
                "temperature_c": row.get("temperature_c"),
                "humidity": row.get("humidity"),
                "water_level_m": row.get("water_level_m"),
                "discharge_m3s": row.get("discharge_m3s"),
            },
        )
        return self._format(station, observation)

    def _format(self, station, observation) -> dict:
        max_age = timedelta(minutes=int(getattr(settings, "WEATHER_MAX_AGE_MINUTES", 180)))
        age_minutes = (timezone.now() - observation.timestamp).total_seconds() / 60
        return {
            "station": {"id": station.id, "station_id": station.station_id,
                        "name": station.name, "provider": station.provider},
            "observed_at": observation.timestamp,
            "temperature_c": observation.temperature_c,
            "rainfall_mm": observation.rainfall_mm,
            "rainfall_24h_mm": observation.rainfall_mm,
            "humidity": observation.humidity,
            "water_level_m": observation.water_level_m,
            "discharge_m3s": observation.discharge_m3s,
            "data_quality": {"available": True, "stale": timezone.now() - observation.timestamp > max_age,
                             "age_minutes": round(age_minutes, 1), "source": station.provider},
        }

    def current(self, latitude: float, longitude: float) -> dict:
        try:
            row = fetch_current(latitude, longitude)
            try:
                return self._store_live(row)
            except Exception:
                # Persistence must never hide a successful live provider response.
                return self._format_live(row)
        except Exception:
            pass

        station = self._nearest_station(latitude, longitude)
        if station is None:
            return {"station": None, "observed_at": None, "temperature_c": None,
                    "rainfall_mm": None, "rainfall_24h_mm": None, "humidity": None,
                    "water_level_m": None, "discharge_m3s": None,
                    "data_quality": {"available": False, "reason": "no_live_provider_or_nearby_station"}}
        observation = station.observations.order_by("-timestamp").first()
        if observation is None:
            return {"station": {"id": station.id, "station_id": station.station_id,
                                 "name": station.name, "provider": station.provider},
                    "observed_at": None, "temperature_c": None, "rainfall_mm": None,
                    "rainfall_24h_mm": None, "humidity": None, "water_level_m": None,
                    "discharge_m3s": None,
                    "data_quality": {"available": False, "reason": "no_observation"}}
        return self._format(station, observation)

    def history(self, latitude: float, longitude: float, days: int = 7) -> list[dict]:
        station = self._nearest_station(latitude, longitude)
        if station is None:
            return []
        since = timezone.now() - timedelta(days=days)
        rows = station.observations.filter(timestamp__gte=since).order_by("-timestamp")[:2000]
        return [{"observed_at": row.timestamp, "rainfall_mm": row.rainfall_mm,
                 "temperature_c": row.temperature_c, "humidity": row.humidity,
                 "water_level_m": row.water_level_m, "discharge_m3s": row.discharge_m3s} for row in rows]
