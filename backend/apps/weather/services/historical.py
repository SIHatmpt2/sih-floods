from __future__ import annotations

import json
from datetime import date, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.cache import cache


HISTORICAL_FORECAST_API = "https://historical-forecast-api.open-meteo.com/v1/forecast"
ARCHIVE_API = "https://archive-api.open-meteo.com/v1/archive"
HISTORICAL_FORECAST_START_YEAR = 2024
HISTORICAL_REQUEST_TIMEOUT_SECONDS = 12


class HistoricalWeatherError(RuntimeError):
    """Raised when historical weather cannot be reconstructed."""


class HistoricalWeatherService:
    """Fetch historical hourly weather for a requested date.

    The Historical Forecast API is preferred for recent dates from 2024 onward.
    Older dates use the ERA5 archive directly because it provides gap-free
    historical coverage back to 1940. If the Historical Forecast API is slow
    or unavailable, ERA5 is used as a fallback so a valid date does not stall
    the analysis indefinitely.
    """

    @staticmethod
    def analysis_window(analysis_date: date) -> tuple[date, date]:
        return analysis_date - timedelta(days=6), analysis_date

    def for_date(self, latitude: float, longitude: float, analysis_date: date) -> dict:
        cache_key = (
            f"floodintel:historical-weather:{float(latitude):.4f}:"
            f"{float(longitude):.4f}:{analysis_date.isoformat()}"
        )
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        start_date, end_date = self.analysis_window(analysis_date)
        common = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "hourly": (
                "temperature_2m,relative_humidity_2m,precipitation,rain,"
                "wind_speed_10m,pressure_msl"
            ),
            "timezone": "Asia/Kolkata",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm",
        }

        if analysis_date.year >= HISTORICAL_FORECAST_START_YEAR:
            try:
                payload = self._request(HISTORICAL_FORECAST_API, common)
                result = self._build_result(
                    payload,
                    analysis_date,
                    source="open-meteo-historical-forecast",
                    dataset="Open-Meteo Historical Forecast",
                )
            except (
                HTTPError,
                URLError,
                TimeoutError,
                OSError,
                ValueError,
                HistoricalWeatherError,
            ):
                result = self._from_era5(common, analysis_date)
        else:
            result = self._from_era5(common, analysis_date)

        cache.set(cache_key, result, timeout=60 * 60 * 24 * 30)
        return result

    def _from_era5(self, common: dict, analysis_date: date) -> dict:
        params = {**common, "models": "era5"}
        try:
            payload = self._request(ARCHIVE_API, params)
            return self._build_result(
                payload,
                analysis_date,
                source="open-meteo-era5",
                dataset="ERA5 reanalysis",
            )
        except (
            HTTPError,
            URLError,
            TimeoutError,
            OSError,
            ValueError,
            HistoricalWeatherError,
        ) as exc:
            raise HistoricalWeatherError(
                f"Historical weather API failed for {analysis_date.isoformat()}: {exc}"
            ) from exc

    def _build_result(
        self,
        payload: dict,
        analysis_date: date,
        *,
        source: str,
        dataset: str,
    ) -> dict:
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

        if not rows:
            raise HistoricalWeatherError(
                f"No hourly observations were returned for {analysis_date.isoformat()}."
            )

        all_rain = [self._number(value) for value in precipitation if value is not None]
        selected_rain = [
            row["precipitation"] for row in rows if row["precipitation"] is not None
        ]
        recent_rain = all_rain[-72:] if all_rain else []
        last = rows[-1]
        return {
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
                "available": True,
                "source": source,
                "dataset": dataset,
                "selected_date_observations": len(rows),
                "partial": len(rows) < 24,
            },
        }

    @staticmethod
    def _request(endpoint: str, params: dict) -> dict:
        query = urlencode(params)
        request = Request(
            f"{endpoint}?{query}",
            headers={"User-Agent": "FloodIntel/1.0"},
        )
        with urlopen(request, timeout=HISTORICAL_REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if payload.get("error"):
            raise ValueError(payload.get("reason", "Unknown Open-Meteo error"))
        return payload

    @staticmethod
    def _number(values, index=None):
        if index is None:
            value = values
        elif index >= len(values):
            return None
        else:
            value = values[index]
        return float(value) if value is not None else None
