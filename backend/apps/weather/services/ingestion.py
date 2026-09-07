from __future__ import annotations

from django.conf import settings
from django.contrib.gis.geos import Point

from ..models import WeatherObservation, WeatherStation
from .client import WeatherProviderClient
from .normalizer import normalize_weather_records


class WeatherIngestionService:
    def __init__(self):
        self.client = WeatherProviderClient(timeout=getattr(settings, "STATE_API_TIMEOUT", 30))

    def configured_providers(self):
        configured = {}
        for provider, url_setting, key_setting in (
            ("imd", "IMD_API_URL", "IMD_API_KEY"),
            ("cwc", "CWC_API_URL", "CWC_API_KEY"),
        ):
            url = getattr(settings, url_setting, None)
            if url:
                configured[provider] = (url, getattr(settings, key_setting, None))
        return configured

    def refresh(self) -> dict:
        results = {}
        for provider in getattr(settings, "WEATHER_PROVIDER_PRIORITY", ["accuweather", "imd", "cwc"]):
            config = self.configured_providers().get(provider)
            if not config:
                results[provider] = {"status": "not_configured", "records": 0}
                continue
            url, api_key = config
            try:
                payload = self.client.get(url, api_key=api_key)
                rows = normalize_weather_records(payload, provider)
                stored = self.store(rows)
                results[provider] = {"status": "ok", "records": stored}
            except Exception as exc:
                results[provider] = {"status": "error", "records": 0, "error": str(exc)}
        return results

    def store(self, rows: list[dict]) -> int:
        stored = 0
        for row in rows:
            station_defaults = {
                "name": row["station_name"],
                "location": Point(row["longitude"], row["latitude"], srid=4326),
                "active": True,
            }
            if row.get("state"):
                station_defaults["state"] = row["state"]
            if row.get("district"):
                station_defaults["district"] = row["district"]

            station, _ = WeatherStation.objects.update_or_create(
                provider=row["provider"],
                station_id=row["station_id"],
                defaults=station_defaults,
            )
            WeatherObservation.objects.update_or_create(
                station=station,
                timestamp=row["timestamp"],
                defaults={
                    "rainfall_mm": row["rainfall_mm"],
                    "temperature_c": row["temperature_c"],
                    "humidity": row["humidity"],
                    "water_level_m": row["water_level_m"],
                    "discharge_m3s": row["discharge_m3s"],
                },
            )
            stored += 1
        return stored
