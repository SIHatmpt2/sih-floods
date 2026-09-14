from __future__ import annotations

import json
from datetime import date, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.cache import cache


OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"


class HistoricalWeatherService:
    """Fetch and normalize reanalysis weather for a requested historical date."""

    @staticmethod
    def analysis_window(analysis_date: date) -> tuple[date, date]:
        return analysis_date - timedelta(days=6), analysis_date

    def for_date(self, latitude: float, longitude: float, analysis_date: date) -> dict:
        cache_key = f"floodintel:historical-weather:{float(latitude):.4f}:{float(longitude):.4f}:{analysis_date.isoformat()}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        start_date, end_date = self.analysis_window(analysis_date)
        params = urlencode({
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "hourly": "temperature_2m,relative_humidity_2m,precipitation,rain,wind_speed_10m,pressure_msl",
            "timezone": "Asia/Kolkata",
        })
        request = Request(
            f"{OPEN_METEO_ARCHIVE}?{params}",
            headers={"User-Agent": "FloodIntel/1.0"},
        )
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))

        hourly = payload.get("hourly") or {}
        times = hourly.get("time") or []
        precipitation = hourly.get("precipitation") or []
        rainfall = hourly.get("rain") or precipitation
        temperatures = hourly.get("temperature_2m") or []
        humidity = hourly.get("relative_humidity_2m") or []
        wind = hourly.get("wind_speed_10m") or []
        pressure = hourly.get("pressure_msl") or []

        rows = []
        for index, timestamp in enumerate(times):
            if not timestamp.startswith(analysis_date.isoformat()):
                continue
            rows.append({
                "time": timestamp,
                "precipitation": self._number(precipitation, index),
                "rain": self._number(rainfall, index),
                "temperature_c": self._number(temperatures, index),
                "humidity": self._number(humidity, index),
                "wind_speed_kmh": self._number(wind, index),
                "pressure_hpa": self._number(pressure, index),
            })

        all_rain = [self._number(value) for value in precipitation if value is not None]
        selected_rain = [row["precipitation"] for row in rows if row["precipitation"] is not None]
        recent_rain = all_rain[-72:] if all_rain else []
        last = rows[-1] if rows else {}
        result = {
            "analysis_date": analysis_date.isoformat(),
            "rainfall_24h_mm": round(sum(selected_rain), 2),
            "rainfall_3d_mm": round(sum(recent_rain), 2),
            "rainfall_7d_mm": round(sum(all_rain), 2),
            "rainfall_48h_mm": round(sum(all_rain[-48:]), 2),
            "temperature_c": last.get("temperature_c"),
            "humidity": last.get("humidity"),
            "wind_speed_kmh": last.get("wind_speed_kmh"),
            "pressure_hpa": last.get("pressure_hpa"),
            "hourly": rows,
            "data_quality": {
                "available": bool(rows),
                "source": "open-meteo-era5-land",
                "dataset": "ERA5-Land reanalysis",
                "selected_date_observations": len(rows),
                "partial": len(rows) < 24,
            },
        }
        cache.set(cache_key, result, timeout=60 * 60 * 24 * 30)
        return result

    @staticmethod
    def _number(values, index=None):
        if index is None:
            value = values
        elif index >= len(values):
            return None
        else:
            value = values[index]
        return float(value) if value is not None else None
