from __future__ import annotations

from django.contrib.gis.geos import Point

from ..models import WeatherObservation, WeatherStation
from .live import fetch_current


class WeatherIngestionService:
    """Persist live weather observations for explicit coordinates."""

    def refresh_location(self, latitude: float, longitude: float) -> dict:
        row = fetch_current(latitude, longitude)
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
        return {"provider": row["provider"], "station_id": station.station_id, "observation_id": observation.id}

    def refresh(self) -> dict:
        """Keep the scheduled task safe when no coordinates are supplied."""
        return {
            "accuweather": {"status": "ready"},
            "imd": {"status": "ready"},
            "detail": "Live refresh is performed for the coordinates selected by the user.",
        }
